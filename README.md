# vidthing

A tool for downloading and compressing videos.

This is still a work in progress!

# Requirements

The following packages must be installed on your system to work:
- `ffmpeg`

I have `yt-dlp` installed separately, but that's probably not necessary.

Do something like this prior to running:
```console
git clone https://github.com/nbschon/vidthing
cd vidthing
python -m venv ./venv/
source ./venv/bin/activate
python -m pip install -r requirements.txt
```

# Usage

Run with a command that looks like the following:
```console
python -m flask --app main run
```
If you want to have the site be accessible to other devices on your local network,
append `--host 0.0.0.0` to the previous command. 

Connect to the site locally at `http://127.0.0.1:5000` in your browser, or the
host machine's IP at port 5000, depending on how you're running it.


| :warning: Warning |
|:------------------|
| This is definitely *not* suitable for running on a public network, so don't do that. |

# Rationale

I want to be able to send videos sometimes, but I don't always like linking to an external site, and when
I download the video, it can often times be too big to send directly. 

I'm also not always seated at a "real" computer with access to the command line, 
so downloading and compressing isn't very easy.

There are a few existing solutions, but they don't do quite what I want.

### cobalt.tools

Good for downloading videos on mobile! But sometimes videos are too large,
and as of me writing this (February 2026) YouTube is not supported.

### 8mb.video

Good for compressing videos to size! However, you need to have already downloaded
the video, which is another, rather cumbersome, step on mobile. Also, the upper size limit
(8 megabytes) is 20% smaller than what sites like Discord support without paying, so you are losing
~20% of quality.

### Handbrake

Very good, but very heavy, too. Many settings, and last time I checked, there isn't an option to 
target a specific file size. Does not run on mobile.

Basically, I wanted a method that would download / prepare a video I wanted to share without having
to think about twiddling options and have it all be in one place.
