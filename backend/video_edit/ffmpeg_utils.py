
import shlex
import subprocess
from typing import List


def run_cmd(cmd: List[str], check: bool = True):
    print("RUN:", " ".join(shlex.quote(x) for x in cmd))
    subprocess.run(cmd, check=check)


def get_duration(path: str) -> float:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        path
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(res.stdout.strip())


def secs(t: str) -> float:
    if isinstance(t, (int, float)):
        return float(t)
    if ":" in t:
        parts = [float(p) for p in t.split(":")]
        parts = list(reversed(parts))
        s = 0.0
        mul = 1.0
        for p in parts:
            s += p * mul
            mul *= 60.0
        return s
    return float(t)