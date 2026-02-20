from datetime import datetime
from flask import Flask, render_template, request, send_from_directory
from process import *

SIZE = "10m"

app = Flask(__name__)

VALID_EXTS = {"mp4", "mkv", "webm", "mov", "avi"}

def valid_file(filename: str | None) -> tuple[bool, str]:
    if not filename:
        return (False, "")

    ext = filename.rsplit(".", 1)[1].lower()
    if "." in filename and ext in VALID_EXTS:
        return (True, ext)

    return (False, "")

def handle_file():
    if "file" not in request.files:
        print("no file given")
        return "<p>no file given</p>", 400

    size = None
    try:
        size_str = request.form["size"]
        size = int(size_str)
    except ValueError:
        return "invalid size", 400
    except KeyError:
        return "no size given", 400

    suffix = None
    try:
        suffix = request.form["suffix"]
    except KeyError:
        return "no size suffix given", 400

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
        two_passes(full_name, processed_name, size, suffix)
        print("processed!")
        return f"""
            <p>{new_name}</p>
            <a href="{processed_name}">download file</a>
        """, 200

        print("invalid file extension.")
        return "<p>invalid file extension</p>", 400
    return "<p>something went wrong</p>", 400

def handle_url():
    size = None
    try:
        size_str = request.form["size"]
        size = int(size_str)
    except ValueError:
        return "invalid size", 400
    except KeyError:
        return "no size given", 400

    suffix = None
    try:
        suffix = request.form["suffix"]
    except KeyError:
        return "no size suffix given", 400

    url = None
    try:
        url = request.form["url"]
    except KeyError:
        return "no url given", 400

    if not url:
        return "empty url", 400

    return download(url, size, suffix)

@app.route("/")
def test():
    return render_template("index.html")

@app.route("/upload", methods=["GET"])
def upload_page():
    return render_template("upload.html")

@app.route("/upload", methods=["POST"])
def try_recv_file():
    print(request.form)
    if "source_type" in request.form:
        match request.form["source_type"]:
            case "url":
                return handle_url()
            case "file":
                return handle_file()
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
    download(url)
# size_in_bytes(SIZE)
# two_passes("testvideo.mp4", "15m")

