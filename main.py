from datetime import datetime
from typing import Optional
from flask import Flask, render_template, request, send_from_directory
from process import *
from report import *
import threading

SIZE = "10m"

app = Flask(__name__)

VALID_EXTS = {"mp4", "mkv", "webm", "mov", "avi"}

# def valid_file(filename: str | None) -> tuple[bool, str]:
#     if not filename:
#         return (False, "")
#
#     ext = filename.rsplit(".", 1)[1].lower()
#     if "." in filename and ext in VALID_EXTS:
#         return (True, ext)
#
#     return (False, "")

def validate_form(form) -> Optional[tuple[str, int]]:
    try:
        size = int(form["size"])
    except ValueError:
        return "invalid size", 400
    except KeyError:
        return "no size given", 400

    try:
        suffix = form["suffix"]
    except KeyError:
        return "no size suffix given", 400

    try:
        passes = int(form["passes"])
    except ValueError:
        return "invalid passes format", 400
    except KeyError:
        return "no passes given", 400

    match passes:
        case 1 | 2:
            pass
        case _:
            return "invalid number of passes", 400

    return None

def handle_file(id: str):
    if "file" not in request.files:
        print("no file given")
        return "<p>no file given</p>", 400

    if (res := validate_form(request.form)) != None:
        return res

    size, suffix, passes = int(request.form["size"]), request.form["suffix"], int(request.form["passes"])

    file = request.files["file"]
    if not file or file.filename == "":
        print("empty file")
        return "empty file", 400

    name, ext = file.filename.rsplit(".", 1)
    print(f"{name} {ext}")
    if file and "." in file.filename and ext in VALID_EXTS:
        new_name = f"{name}-{datetime.now().strftime("%Y%m%d-%H-%M-%S")}"
        full_name = f"./uploads/{new_name}.{ext}"
        processed_name = f"./processed/{new_name}.mp4"
        file.save(full_name)
        print(f"uploaded {full_name}")
        print(f"in: {full_name}, out: {processed_name}")
        info = RequestInfo(size, suffix, passes, id)
        match passes:
            case 1:
                one_pass(full_name, processed_name, info)
            case 2:
                two_passes(full_name, processed_name, info)
            case _:
                assert False, "unreachable"

        print("processed!")
        return f"""
            <p>{new_name}</p>
            <a href="{processed_name}">download file</a>
        """, 200

    return "<p>something went wrong</p>", 400

def handle_url(id: str, form):
    print(f"{threading.current_thread()}")
    if (res := validate_form(form)) != None:
        return res

    size, suffix, passes = int(form["size"]), form["suffix"], int(form["passes"])

    url = None
    try:
        url = form["url"]
    except KeyError:
        return "no url given", 400

    if not url:
        return "empty url", 400

    info = RequestInfo(size, suffix, passes, id)

    return download(url, info)

@app.route("/")
def test():
    return render_template("index.html")

@app.route("/upload", methods=["GET"])
def upload_page():
    if not os.path.exists("./uploads/"):
        os.makedirs("./uploads/")
    if not os.path.exists("./processed/"):
        os.makedirs("./processed/")
    if not os.path.exists("./tmp/"):
        os.makedirs("./tmp/")

    return render_template("upload.html")

@app.route("/upload", methods=["POST"])
def try_recv_file():
    print(request.form)
    if "source_type" in request.form:
        full = f"{request.remote_addr}-{datetime.now().timestamp()}"
        id = "".join(str(part) for part in full.split("."))
        tmp_dir = f"./tmp/{id}/"
        print(tmp_dir)

        os.makedirs(tmp_dir)
        match request.form["source_type"]:
            case "url":
                print("url")
                jobs.update_job(id, ("dl", 0.0, 1))
                threading.Thread(target=handle_url, args=(id, request.form)).start()
                return f"""
                <div hx-get=/report/{id}?step=dl hx-trigger="every 1s"></div>
                """
            case "file":
                print("file")
                return handle_file(id)
            case _:
                return "invalid source type", 400
    else:
        return "<p>something went wrong</p>", 400

@app.route("/processed/<filename>", methods=["GET"])
def get_processed_video(filename):
    try:
        return send_from_directory("./processed/", path=filename, as_attachment=True)
    except:
        return "file not found", 404


if __name__ == "__main__":
    # full_name = "./uploads/upload-20260217-16-12-08.mkv"
    # processed_name = "./processed/upload-20260217-16-12-08.mkv"
    # full_name = "./uploads/20260217-17-03-50.mp4"
    # processed_name = "./processed/20260217-17-03-50.mp4"
    # full_name = "./Aoki Ryuusei SPT Layzner OP HD (Textless) [gJWpOqrMtjs].mkv"
    # full_name = "./testvideo.mp4"
    # processed_name = "./testthing.mp4"
    # two_passes(full_name, processed_name, "10mb")
    url = "https://www.youtube.com/watch?v=UOjrBYgRBxo"
    url = "https://www.youtube.com/watch?v=6rDLigCs0xI&pp=ygUKbGF5em5lciBvcA%3D%3D"
    url = "https://www.youtube.com/watch?v=AfmP53JtDVU&pp=0gcJCYcKAYcqIYzv"
    info = RequestInfo(10, "mb", 2, "")
    download(url, info)
# size_in_bytes(SIZE)
# two_passes("testvideo.mp4", "15m")

@app.route("/report/<job_id>", methods=["GET"])
def report(job_id):
    step = request.args.get("step", "dl")
    return report_progress(job_id, step)

