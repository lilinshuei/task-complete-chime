# -*- coding: utf-8 -*-
"""
Task completion chime - a tiny, dependency-free Windows reminder.

Why this exists:
    A short system beep is easy to miss when you are working on something else.
    This script plays a clear 12-second chime when an agent finishes (or fails)
    a task, then gets out of the way.

Design:
    * Standard library only: wave + winsound. No pip install, no network.
    * Default sound is an original chime bundled in assets/chime.wav.
    * Use --audio to play your own local file. Non-WAV input is converted with
      ffmpeg when ffmpeg is on PATH.
    * One process plays; another process can stop it with --stop.
    * Nothing is uploaded, no registry changes, no files are deleted.

Usage:
    python chime.py
    python chime.py --audio "C:\\path\\to\\your.wav"
    python chime.py --seconds 8
    python chime.py --full
    python chime.py --stop
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_AUDIO = os.path.join(ROOT, "assets", "chime.wav")

STATE = os.path.join(os.environ.get("LOCALAPPDATA") or os.path.expanduser("~"),
                     "task-complete-chime")
LOG = os.path.join(STATE, "chime.log")
STOP = os.path.join(STATE, "STOP")


def log(message):
    line = "[%s] %s" % (time.strftime("%Y-%m-%d %H:%M:%S"), message)
    try:
        os.makedirs(STATE, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass
    try:
        print(line, flush=True)
    except OSError:
        pass


def wav_duration(path):
    with wave.open(path, "rb") as w:
        return w.getnframes() / float(w.getframerate())


def to_wav(src, seconds):
    """Return (wav_path, is_temp). WAV passes through; other formats use ffmpeg."""
    if src.lower().endswith(".wav"):
        return src, False
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("non-WAV audio needs ffmpeg on PATH; use a .wav file instead")
    tmp = os.path.join(tempfile.gettempdir(), "task-complete-chime.wav")
    cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", src]
    if seconds and seconds > 0:
        cmd += ["-t", str(seconds)]
    cmd += ["-ac", "1", "-ar", "22050", tmp]
    proc = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    if proc.returncode != 0 or not os.path.exists(tmp):
        raise RuntimeError("ffmpeg failed: " + (proc.stderr or "")[-300:])
    return tmp, True


def play(path, seconds):
    import winsound

    total = wav_duration(path)
    limit = total if seconds is None or seconds <= 0 else min(float(seconds), total)
    winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
    started = time.time()
    reason = "finished"
    try:
        while time.time() - started < limit:
            if os.path.exists(STOP):
                reason = "stop_flag"
                break
            time.sleep(0.1)
    except KeyboardInterrupt:
        reason = "interrupt"
    finally:
        winsound.PlaySound(None, winsound.SND_PURGE)
    return reason, time.time() - started


def main():
    parser = argparse.ArgumentParser(description="Play a short task-completion chime.")
    parser.add_argument("--audio", default=os.environ.get("CHIME_AUDIO") or DEFAULT_AUDIO,
                        help="local audio file (default: assets/chime.wav)")
    parser.add_argument("--seconds", type=int, default=12,
                        help="play at most N seconds (default 12; 0 = full track)")
    parser.add_argument("--full", action="store_true", help="play the full track")
    parser.add_argument("--stop", action="store_true", help="stop a running chime")
    args = parser.parse_args()

    os.makedirs(STATE, exist_ok=True)

    if args.stop:
        with open(STOP, "w", encoding="utf-8") as f:
            f.write(str(time.time()))
        print("STOP_OK")
        return 0

    if os.name != "nt":
        print("CHIME_FAIL only Windows is supported (winsound)")
        return 2

    try:
        if os.path.exists(STOP):
            os.remove(STOP)
    except OSError:
        pass

    src = args.audio
    if not os.path.exists(src):
        log("audio_missing %s" % src)
        print("CHIME_FAIL audio_missing")
        return 2

    seconds = 0 if args.full else args.seconds
    tmp = None
    try:
        wav, is_temp = to_wav(src, seconds)
        if is_temp:
            tmp = wav
        log("play_start src=%s seconds=%s" % (os.path.basename(src), seconds))
        reason, elapsed = play(wav, seconds)
        log("play_end reason=%s elapsed=%.1fs" % (reason, elapsed))
        print("CHIME_DONE reason=%s elapsed=%.1f" % (reason, elapsed))
        return 0
    except Exception as exc:
        log("CHIME_FAIL %s" % exc)
        print("CHIME_FAIL %s" % exc)
        return 3
    finally:
        if tmp:
            try:
                os.remove(tmp)
            except OSError:
                pass


if __name__ == "__main__":
    sys.exit(main())
