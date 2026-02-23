from flask import Flask
from dataclasses import astuple, asdict
from collections import deque
import os
import jobs
import json

app = Flask(__name__)

def check_ffmpeg_log(job_id: str, passes: int, n=10):
    step, _, dur, filename = astuple(jobs.get_job(job_id))
    log_file = None
    match passes:
        case 1:
            log_file = open(f"./tmp/{job_id}/p{passes}.log")
        case 2:
            log_file = open(f"./tmp/{job_id}/p{passes}.log")
            pass
        case _:
            return

    out_prefix: str = "out_time_us="
    prog_prefix: str = "progress="

    ret = list(deque(log_file, maxlen=n))
    out_time_us = next((line for line in ret if line.startswith(out_prefix)), None)
    progress = next((line for line in ret if line.startswith(prog_prefix)), None)

    if not out_time_us or not progress:
        return 0

    out_val_str = out_time_us[len(out_prefix):]
    out_val = 0
    print(f"out_val_str: {out_val_str}")

    try:
        out_val = int(out_val_str)
        print("====================")
        print(f"out val: {out_val}")
        print("====================")
    except ValueError:
        pass

    if progress[len(prog_prefix):] == "end":
        out_val = 100

    new_pct = (out_val / dur * 100)

    print(f"{out_val}")
    jobs.update_job(job_id, jobs.JobInfo(step, new_pct, dur, filename))

    log_file.close()
    return out_val


def report_progress(job_id: str, step: str):
    # print(json.dumps(jobs = [asdict(job) for job in jobs.jobs], indent=4))
    if job_id not in jobs.jobs.keys():
        return "<div id=\"report\">uh oh</div>", 200

    step, pct, dur, filename = astuple(jobs.get_job(job_id))
    text = ""
    match step:
        case "dl":
            text = "Downloading..."
        case "p1":
            out = check_ffmpeg_log(job_id, 1, 12)
            pct = (out / dur * 100)
            text = f"Transcoding (Pass 1)..."
        case "p2":
            out = check_ffmpeg_log(job_id, 2, 12)
            pct = (out / dur * 100)
            text = "Transcoding (Pass 2)..."
        case "done":
            text = "Done."
        case "error":
            text = "Encountered error!"

    pct_text = f"{pct:.0f}% / 100%"
    print("====================")
    print(f"{pct}, {pct_text}")
    print("====================")
    html = None
    if step != "done":
        html = f"""
        <div id="report" hx-get=/report/{job_id} hx-trigger="every 1s" hx-swap="outerHTML">
            <p>{text} ({pct_text})</p>
            <progress id="progress" value="{pct}" max="100"></progress>
        </div>
        """
    else:
        if filename:
            print(filename)
        prefix = "./processed/"
        name, _ = filename[len(prefix):].rsplit(".", 1)
        html = f"""
        <div id="report">
            <p>{name}</p>
            <a href="{filename}">download file</a>
        </div>
        """
    # <div hx-get="/report/{id}?step={step}" hx-trigger="every 1s"></div>

    return html, 200
