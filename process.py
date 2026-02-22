from datetime import datetime
from dataclasses import dataclass, astuple
import ffmpeg
import glob
import json
import math
import os
from flask import request
import yt_dlp
import jobs

format: str = "mp4"
upload_str = "./uploads/"

@dataclass
class RequestInfo:
    size: int
    suffix: str
    passes: int
    id: str 

def size_in_bytes(size: int, suffix: str) -> int:
    # num_part = ""
    # idx = 0
    # while size[idx].isnumeric() or size[idx] == ".":
    #     num_part += size[idx]
    #     idx += 1

    # suffix_part = size[idx:].lower()
    exp = 0
    suffix_name = ""
    match suffix:
        case "k" | "kb":
            exp = 1
            suffix_name = "kilobytes"
        case "m" | "mb": 
            exp = 2
            suffix_name = "megabytes"
        case _:
            pass

    print(f"target size: {size} {suffix_name}")

    final = math.ceil(float(size) * 1024 ** exp)
    print(f"or: {final:,} bytes")
    return final

def get_bitrate(duration: float, target_size: int, suffix: str) -> int:
    size_bits = size_in_bytes(target_size, suffix) * 8
    target_bitrate = size_bits / duration / 1000
    return int(target_bitrate)

def one_pass(in_path: str, out_path: str, info: RequestInfo):
    probe = ffmpeg.probe(in_path)
    # for stream in probe["streams"]:
    #     print("====================")
    #     print(stream["codec_type"].upper())
    #     print(json.dumps(stream, sort_keys=True, indent=4))
    #     print("====================")

    video_stream = next((stream for stream in probe["streams"] if stream["codec_type"] == "video"), None)
    audio_stream = next((stream for stream in probe["streams"] if stream["codec_type"] == "audio"), None)

    size, suffix, passes, id = astuple(info)

    if video_stream is not None:
        duration = float(video_stream['duration'])
        # print(duration)

        target_bitrate = get_bitrate(duration, size, suffix)
        if audio_stream is not None:
            target_bitrate -= 96
        target_bitrate *= .95

        (
            ffmpeg
            .input(in_path)
            .output(
                out_path,
                video_bitrate=f"{int(target_bitrate)}k", 
                audio_bitrate="96k",
                vcodec="libx264",
                acodec="aac"
            )
            .overwrite_output()
            .run()
        )

def two_passes(in_path: str, out_path: str, info: RequestInfo):
    probe = ffmpeg.probe(in_path)
    # for stream in probe["streams"]:
    #     # print(stream)
    #     print("====================")
    #     print(stream["codec_type"].upper())
    #     print(json.dumps(stream, sort_keys=True, indent=4))
    #     print("====================")
    print(json.dumps(probe["format"], sort_keys=True, indent=4))

    size, suffix, passes, id = astuple(info)

    target_size = size_in_bytes(size, suffix)

    video_stream = next((stream for stream in probe["streams"] if stream["codec_type"] == "video"), None)
    audio_stream = next((stream for stream in probe["streams"] if stream["codec_type"] == "audio"), None)
    if video_stream is not None:
        duration = float(probe["format"]["duration"])
        print("====================")
        print(f"duration: {duration}")
        print("====================")
        jobs.update_job(info.id, ("p1", 0.0, duration * 1e6))
        format_size = float(probe["format"]["size"])
        bitrate = format_size * 8 // duration
        print("====================")
        w = int(video_stream["width"])
        h = int(video_stream["height"])
        fps_str = video_stream["avg_frame_rate"].split("/")
        fps = int(fps_str[0]) / int(fps_str[1])
        assert len(fps_str) == 2
        print(f"bitrate: {bitrate}, as kbps: {bitrate / 1000}")
        print(f"br: {bitrate}, w: {w}, h: {h}, fps: {fps}")
        bpp = bitrate / (w * h * fps)
        print(f"current bpp: {bpp}")
        print("====================")

        target_bitrate = get_bitrate(duration, size, suffix)
        print(f"target: {target_bitrate}")
        if audio_stream is not None:
            target_bitrate -= 96
        target_bitrate *= .95
        print(f"target: {target_bitrate}")

        sink = "NUL" if os.name == "nt" else "/dev/null"

        # time = datetime.now().timestamp()

        common_args = {
            # "vf": "scale=1024:-2",
            "c:v": "libx264",
            "b:v": f"{int(target_bitrate)}k",
            "preset": "slow",
            "passlogfile": "ffmpeg2pass",
            # "progress": f"{time}.txt",
            # "progress": "pipe:",
            "nostats": None,
        }

        (
            ffmpeg
            .input(in_path)
            .output(
                sink,
                **{
                    **common_args,
                    "pass": 1,
                    "an": None,
                    "f": "mp4",
                    "progress": f"./tmp/{id}/p1.log",
                },
            )
            .overwrite_output()
            # .run_async(quiet=False, pipe_stdout=True, pipe_stderr=True)
            .run()
        )

        jobs.update_job(id, ("p2", 0.0, duration * 1e6))

        (
            ffmpeg
            .input(in_path)
            .output(
                out_path,
                **{
                    **common_args,
                    "pass": 2,
                    "c:a": "aac",
                    "b:a": "96k",
                    "progress": f"./tmp/{id}/p2.log",
                },
            )
            .overwrite_output()
            .run(quiet=False)
        )

        jobs.update_job(id, ("done", 100, 1))

    output_size = os.path.getsize(out_path)
    print(f"size was {output_size:,} bytes (target was {target_size:,})")
    assert output_size <= target_size, f"size was {output_size} ({output_size - target_size} bytes larger than {target_size})"

    print(f"{output_size / 1000 ** 2:.2f} MB, {output_size / 1024 ** 2:.2f} MiB")

    for f in glob.glob("ffmpeg2pass*"):
        os.remove(f)
    print("removed pass info files!")

def download(url: str, info: RequestInfo):
    def dl_progress_hook(d):
        match d["status"]:
            case "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
                downloaded = d.get("downloaded_bytes", 0)
                if total > 0:
                    percent = (downloaded / total) * 100
                    jobs.update_job(info.id, ("dl", percent, 1.0))
            case "finished":
                print("done!")

    opts = {
        "outtmpl": "%(title)s.%(ext)s",
        "merge_output_format": format,
        "no-mtime": True,
        "paths": {
            "home": upload_str
        },
        "progress_hooks": [dl_progress_hook],
        # "quiet": True,
    }

    with yt_dlp.YoutubeDL(opts) as dl:
        dl_info = dl.extract_info(url, download=True)
        filename = dl.prepare_filename(dl_info)
        print("====================")
        print(filename)
        print("====================")
        try:
            dl.download(url)
        except yt_dlp.DownloadError:
            return "bad url", 400

        name, ext = filename[len(upload_str):].rsplit(".", 1)
        print("====================")
        print(f"{name} {ext}")
        print("====================")
        output_file = f"./processed/{name}-{datetime.now().strftime("%Y%m%d-%H-%M-%S")}.mp4"

        # one_pass()
        two_passes(f"./uploads/{name}.{ext}", output_file, info)
        return f"""
            <p>{name}</p>
            <a href="{output_file}">download file</a>
        """, 200

