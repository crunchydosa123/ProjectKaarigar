#!/usr/bin/env python3
"""
nl_video_edit_with_gemini_and_stickers.py

Extended pipeline:
 - supports "sticker" edits (emoji or image overlays)
 - for emoji content, searches local sticker directories for a matching PNG (by codepoint or name);
   if not found it downloads the Twemoji PNG for the emoji codepoint and uses that.
 - overlays stickers as PNG images using ffmpeg overlay + enable='between(t,START,END)'.

Added features:
 - supports "music" edits: find music by local file, direct URL, or Jamendo search (if JAMENDO_CLIENT_ID set)
 - mixes background music into final video (loop/trim/volume)
 - sticker name lookup searches the created `./stickers` directory

Requirements:
 - ffmpeg and ffprobe on PATH
 - google-generativeai (optional) if you want Gemini integration: pip install google-generativeai
 - JAMENDO_CLIENT_ID (optional) if you want Jamendo search/download support

Important licensing note:
 - This script only downloads Jamendo tracks (which expose license info) or uses local files or user-supplied URLs.
 - Do NOT use this script to fetch copyrighted commercial music unless you have a license.
"""
import os
import sys
import json
import shlex
import tempfile
import subprocess
import re
import unicodedata
import urllib.request
import urllib.parse
from typing import List, Dict, Any, Optional

# Gemini / genai import
try:
    import google.generativeai as genai
except Exception:
    genai = None

# ----------------------------
# Utilities: ffprobe / ffmpeg helpers
# ----------------------------
def run_cmd(cmd: List[str], check: bool = True):
    print("RUN:", " ".join(shlex.quote(x) for x in cmd))
    subprocess.run(cmd, check=check)


def get_duration(path: str) -> float:
    """Return media duration in seconds using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        path
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(res.stdout.strip())


def secs(t: str) -> float:
    """Allow hh:mm:ss or seconds input; return seconds as float."""
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


# ----------------------------
# Gemini integration (updated to allow music edits)
# ----------------------------
def extract_json_from_text(text: str) -> str:
    array_match = re.search(r"\[.*\]", text, flags=re.DOTALL)
    if array_match:
        return array_match.group(0)
    obj_match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if obj_match:
        return obj_match.group(0)
    return text


def call_gemini_raw(prompt: str, api_key: str, model_name: str = "gemini-2.0-flash",
                    max_output_tokens: int = 1024, temperature: float = 0.0) -> str:
    if genai is None:
        raise RuntimeError("google.generativeai package not installed. pip install google-generativeai")
    genai.configure(api_key=api_key)
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        if hasattr(response, "text") and response.text:
            return response.text
        if hasattr(response, "candidates") and response.candidates:
            c0 = response.candidates[0]
            if hasattr(c0, "content") and c0.content:
                return c0.content
            return str(c0)
        return str(response)
    except Exception:
        try:
            res = genai.generate(model=model_name, prompt=prompt, max_output_tokens=max_output_tokens, temperature=temperature)
            if isinstance(res, str):
                return res
            if hasattr(res, "candidates") and res.candidates:
                cand = res.candidates[0]
                if hasattr(cand, "content"):
                    return cand.content
                return str(cand)
            if isinstance(res, dict):
                if "candidates" in res and len(res["candidates"]) > 0:
                    c0 = res["candidates"][0]
                    if isinstance(c0, dict) and "content" in c0:
                        return c0["content"]
                    return json.dumps(c0)
                if "output" in res:
                    return res["output"]
            return str(res)
        except Exception as exc:
            raise RuntimeError(f"Failed to call Gemini: {exc}") from exc


def call_gemini_json(user_instruction: str, api_key: str, model_name: str = "gemini-2.0-flash") -> str:
    prompt = f"""
You are a machine assistant that MUST respond with MACHINE-READABLE JSON ONLY (no commentary, no markdown).
Given a user's natural-language video editing instruction, output a JSON array of edits. Each edit is an object with:
 - action: one of "cut", "speed", "sticker", "music"
 - For "cut": include start and end as seconds (float).
 - For "speed": include start, end (seconds), and rate (float).
 - For "sticker": include start and end (seconds) OR start and duration, and a content object:
      either {{ "emoji": "🔥" }}  (the actual emoji character) or {{ "image": "/full/path/to/sticker.png" }} (a local path).
   Optional sticker fields: position (one of top-left, top-right, bottom-left, bottom-right, center),
                        x (px), y (px), fontsize (int).
 - For "music": include start and end (seconds) OR start and duration, and one of:
      {{ "query": "upbeat pop instrumental" }}  (search local music or Jamendo if enabled),
      {{ "file": "./music/track.mp3" }} (local path),
      {{ "url": "https://..." }} (direct URL).
   Optional music fields: volume (0.0-1.0, default 0.4), loop (bool, default true), source (jamendo|local|url)

Rules:
 - Do not include overlapping cut/speed edits. Sticker edits overlay and may overlap. Music edits may overlap timeline but are applied after timeline changes.
 - Use seconds as floats (e.g. 12.5).
 - If the user provides times like "00:01:20", convert them to seconds in the JSON.
 - If you cannot parse any valid edits, return an empty JSON array: [].
 - Output JSON only and nothing else.

Examples:
User instruction: "Add upbeat pop track throughout"
Output:
[{{"action":"music","start":0.0,"end":120.0,"query":"upbeat pop instrumental","volume":0.35,"loop":true}}]

User instruction: "Add instrumental beat with no lyrics from 0:10 to 0:50"
Output:
[{{"action":"music","start":10.0,"end":50.0,"query":"instrumental beat no vocals","volume":0.4,"loop":false}}]

User instruction: "Add fire emoji at 0:20 for 2 seconds"
Output:
[{{"action":"sticker","start":{secs('0:20'):.1f},"end":{secs('0:20')+2.0:.1f},"content":{{"emoji":"🔥"}},"position":"bottom-right","fontsize":72}}]

User instruction: "Add cat sticker at 1:20 for 2 seconds"
Output:
[{{"action":"sticker","start":{secs('1:20'):.1f},"end":{secs('1:20')+2.0:.1f},"content":{{"image": "./stickers/cat.png"}},"position":"bottom-right","fontsize":72}}]

Now convert this user instruction to JSON and return JSON only (no extra text, no explanation).

User instruction:
\"\"\"{user_instruction}\"\"\""""
    raw = call_gemini_raw(prompt, api_key=api_key, model_name=model_name)
    json_text = extract_json_from_text(raw)
    try:
        parsed = json.loads(json_text)
        if not isinstance(parsed, list):
            raise ValueError("Gemini did not return a JSON array.")
        return json_text
    except Exception as ex:
        raise RuntimeError(f"Unable to parse Gemini output as JSON. Raw output:\n{raw}\n\nExtracted part:\n{json_text}\nError: {ex}") from ex


# ----------------------------
# Editing pipeline helpers
# ----------------------------
def normalize_and_validate_edits(edits: List[Dict[str, Any]], duration: float) -> List[Dict[str, Any]]:
    norm: List[Dict[str, Any]] = []
    for e in edits:
        a = e.get("action")
        if a not in ("cut", "speed", "sticker", "music"):
            continue
        if a == "sticker" or a == "music":
            s = float(e.get("start", 0.0))
            if "end" in e:
                t = float(e.get("end"))
            elif "duration" in e:
                t = s + float(e.get("duration", 2.0))
            else:
                t = s + 2.0
            s = max(0.0, min(s, duration))
            t = max(0.0, min(t, duration))
            if t - s < 0.05:
                continue
            newe = {"action": a, "start": s, "end": t}
            if "content" in e:
                newe["content"] = e["content"]
            if "position" in e:
                newe["position"] = e["position"]
            if "x" in e:
                newe["x"] = e["x"]
            if "y" in e:
                newe["y"] = e["y"]
            if "fontsize" in e:
                newe["fontsize"] = int(e["fontsize"])
            if a == "music":
                newe["query"] = e.get("query")
                newe["url"] = e.get("url")
                newe["file"] = e.get("file")
                newe["volume"] = float(e.get("volume", 0.4))
                newe["loop"] = bool(e.get("loop", True))
                newe["source"] = e.get("source")
            norm.append(newe)
        else:
            s = float(e.get("start", 0.0))
            t = float(e.get("end", s))
            if t <= s:
                continue
            s = max(0.0, min(s, duration))
            t = max(0.0, min(t, duration))
            if t - s < 0.05:
                continue
            newe = {"action": a, "start": s, "end": t}
            if a == "speed":
                newe["rate"] = float(e.get("rate", 1.0))
            norm.append(newe)
    non_sticker = [x for x in norm if x["action"] in ("cut", "speed")]
    non_sticker.sort(key=lambda z: z["start"])
    for i in range(len(non_sticker)-1):
        if non_sticker[i]["end"] > non_sticker[i+1]["start"] - 1e-6:
            raise ValueError(f"Overlapping edits detected: {non_sticker[i]} and {non_sticker[i+1]}. Please have model output non-overlapping edits.")
    stickers = [x for x in norm if x["action"] == "sticker"]
    musics = [x for x in norm if x["action"] == "music"]
    final = non_sticker + stickers + musics
    final.sort(key=lambda z: z["start"])
    return final


def build_segments_to_keep(edits: List[Dict[str, Any]], duration: float) -> List[Dict[str, Any]]:
    segments = []
    cur = 0.0
    timeline_edits = [e for e in edits if e["action"] in ("cut", "speed")]
    timeline_edits.sort(key=lambda x: x["start"])
    for e in timeline_edits:
        if cur < e["start"]:
            segments.append({"start": cur, "end": e["start"], "action": "keep"})
        if e["action"] == "cut":
            cur = e["end"]
        elif e["action"] == "speed":
            segments.append({"start": e["start"], "end": e["end"], "action": "speed", "rate": e["rate"]})
            cur = e["end"]
    if cur < duration:
        segments.append({"start": cur, "end": duration, "action": "keep"})
    segments = [s for s in segments if s["end"] - s["start"] > 0.04]
    return segments


def atempo_filter_chain(rate: float) -> str:
    if rate <= 0:
        raise ValueError("rate must be > 0")
    parts = []
    remaining = rate
    if remaining >= 2.0:
        while remaining > 2.0001:
            parts.append("atempo=2.0")
            remaining /= 2.0
            if remaining < 2.0:
                break
    parts.append(f"atempo={remaining:.6f}")
    return ",".join(parts)


def create_segment(input_path: str, seg: Dict[str, Any], out_path: str):
    s = seg["start"]
    e = seg["end"]
    duration = e - s
    if seg["action"] == "keep":
        cmd = [
            "ffmpeg", "-y",
            "-ss", f"{s:.3f}",
            "-t", f"{duration:.3f}",
            "-i", input_path,
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-c:a", "aac", "-b:a", "128k",
            out_path
        ]
        run_cmd(cmd)
    elif seg["action"] == "speed":
        rate = float(seg.get("rate", 1.0))
        if rate <= 0:
            raise ValueError("Invalid rate")
        atempo_chain = atempo_filter_chain(rate)
        filter_complex = f"[0:v]setpts=PTS/{rate}[v];[0:a]{atempo_chain}[a]"
        cmd = [
            "ffmpeg", "-y",
            "-ss", f"{s:.3f}",
            "-t", f"{duration:.3f}",
            "-i", input_path,
            "-filter_complex", filter_complex,
            "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-c:a", "aac", "-b:a", "128k",
            out_path
        ]
        run_cmd(cmd)
    else:
        raise ValueError("Unknown segment action")


def concat_segments(segment_files: List[str], final_out: str):
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as f:
        list_path = f.name
        for p in segment_files:
            f.write(f"file '{os.path.abspath(p)}'\n")
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", list_path,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-c:a", "aac", "-b:a", "128k",
        final_out
    ]
    try:
        run_cmd(cmd)
    finally:
        try:
            os.remove(list_path)
        except Exception:
            pass


# ----------------------------
# Emoji / sticker lookup & Twemoji download
# ----------------------------
DEFAULT_STICKER_DIRS = [
    "./stickers",
    "./emoji",
    "./emojis",
    "./twemoji",
    "/usr/share/emoji",
    "/usr/share/icons/emoji"
]

# ensure stickers dir exists (user requested specifically to use the created stickers directory)
ensure_dirs = True
for dd in DEFAULT_STICKER_DIRS:
    try:
        os.makedirs(dd, exist_ok=True)
    except Exception:
        pass


def ensure_dirs_exist(dirs: List[str]):
    for d in dirs:
        try:
            os.makedirs(d, exist_ok=True)
        except Exception:
            pass


def emoji_to_codepoints(emoji: str) -> str:
    """Return concatenated lowercase hex codepoints for the emoji (e.g. '1f525')."""
    return "".join(f"{ord(ch):x}" for ch in emoji)


def safe_unicodedata_name(ch: str) -> Optional[str]:
    try:
        return unicodedata.name(ch)
    except Exception:
        return None


def find_local_sticker_for_emoji(emoji: str, search_dirs: Optional[List[str]] = None) -> Optional[str]:
    """
    Search local directories for a PNG matching the emoji:
      - codepoint.png (e.g. 1f525.png)
      - any filename that contains the codepoint or the unicode name (lowercased)
      - direct emoji character in filename (rare)
    Returns full path or None.
    """
    if search_dirs is None:
        search_dirs = DEFAULT_STICKER_DIRS
    code = emoji_to_codepoints(emoji)  # e.g. 1f525
    name = safe_unicodedata_name(emoji) or ""
    name_lower = name.lower().replace(" ", "_")
    ensure_dirs_exist(search_dirs)
    for d in search_dirs:
        if not os.path.isdir(d):
            continue
        for fname in os.listdir(d):
            lf = fname.lower()
            full = os.path.join(d, fname)
            if not os.path.isfile(full):
                continue
            if lf.endswith(".png") or lf.endswith(".webp") or lf.endswith(".jpg") or lf.endswith(".jpeg"):
                base = lf.rsplit(".", 1)[0]
                # exact codepoint
                if base == code:
                    return full
                # contains codepoint
                if code in base:
                    return full
                # contains name or parts of name
                if name_lower and name_lower in base:
                    return full
                # contains emoji short textual names like 'fire' (try small heuristic)
                if name_lower:
                    parts = name_lower.split("_")
                    for p in parts:
                        if p and p in base:
                            return full
                # filename contains the emoji character itself
                if emoji in fname:
                    return full
    return None


def find_local_sticker_by_name(name: str, search_dirs: Optional[List[str]] = None) -> Optional[str]:
    """
    Search local sticker dirs for a file whose filename matches the provided name.
    Matching strategy:
     - normalize name -> lowercase tokens (split on non-alnum)
     - filename base matches if it contains all tokens (order-insensitive)
     - also matches if the base contains the joined name (e.g. mochicats)
    Returns full path or None.
    """
    if not name:
        return None
    if search_dirs is None:
        search_dirs = DEFAULT_STICKER_DIRS
    ensure_dirs_exist(search_dirs)
    # normalize tokens
    tokens = re.findall(r"[a-z0-9]+", name.lower())
    if not tokens:
        return None
    joined = "".join(tokens)
    for d in search_dirs:
        if not os.path.isdir(d):
            continue
        for fname in os.listdir(d):
            full = os.path.join(d, fname)
            if not os.path.isfile(full):
                continue
            lf = fname.lower()
            if not (lf.endswith(".png") or lf.endswith(".webp") or lf.endswith(".jpg") or lf.endswith(".jpeg")):
                continue
            base = lf.rsplit(".", 1)[0]
            # if all tokens present in base
            if all(token in base for token in tokens):
                return full
            # if joined name appears
            if joined and joined in base:
                return full
            # also try replacing hyphens/underscores in base and compare
            compact = re.sub(r"[^a-z0-9]", "", base)
            if joined and joined in compact:
                return full
    return None

def download_url_to_temp(url: str) -> Optional[str]:
    """Download a URL to a temp file and return the path, or None on failure."""
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return None
        ext = os.path.splitext(parsed.path)[1] or ".png"
        fd, tmp = tempfile.mkstemp(suffix=ext)
        os.close(fd)
        print(f"Downloading sticker from {url} -> {tmp}")
        urllib.request.urlretrieve(url, tmp)
        if os.path.getsize(tmp) > 0:
            return tmp
        else:
            os.remove(tmp)
            return None
    except Exception as e:
        print("download_url_to_temp failed:", e)
        return None


def download_twemoji_png_for_emoji(emoji: str, size: int = 72, out_dir: Optional[str] = None) -> Optional[str]:
    """
    Download Twemoji PNG for the emoji to out_dir (or temp dir). Returns path or None.
    size: pick from 72, 144, 512 available from Twemoji repo (72 smallest).
    """
    if out_dir is None:
        out_dir = os.path.join(tempfile.gettempdir(), "twemoji_cache")
    os.makedirs(out_dir, exist_ok=True)
    code = emoji_to_codepoints(emoji)
    # Twemoji asset path: assets/<size>x<size>/<code>.png (repo raw)
    url = f"https://github.com/twitter/twemoji/raw/master/assets/{size}x{size}/{code}.png"
    print(url)
    out_path = os.path.join(out_dir, f"{code}.png")
    # if already exists, return
    if os.path.isfile(out_path):
        return out_path
    try:
        print(f"Downloading Twemoji for emoji {emoji} -> {out_path}")
        urllib.request.urlretrieve(url, out_path)
        if os.path.getsize(out_path) > 0:
            return out_path
        return None
    except Exception as e:
        print("Failed to download Twemoji:", e)
        try:
            if os.path.isfile(out_path):
                os.remove(out_path)
        except Exception:
            pass
        return None


def find_or_fetch_sticker_image_for_emoji(emoji: str, sticker_dirs: Optional[List[str]] = None) -> Optional[str]:
    """
    Try local search, then Twemoji download fallback. Returns path or None.
    """
    path = find_local_sticker_for_emoji(emoji, sticker_dirs)
    if path:
        return path
    # fallback: download twemoji
    tw = download_twemoji_png_for_emoji(emoji, size=72)
    return tw


# ----------------------------
# Sticker overlay helpers (image-overlay-first strategy)
# ----------------------------
def escape_drawtext_text(t: str) -> str:
    t = t.replace("\\", "\\\\")
    t = t.replace("'", "\\'")
    return t


def build_drawtext_filter(emoji: str, start: float, end: float, position: str = "bottom-right",
                          x: Optional[int] = None, y: Optional[int] = None, fontsize: int = 72) -> str:
    fontfile = None  # we prefer PNG overlays for emoji; drawtext is fallback
    txt = escape_drawtext_text(emoji)
    if x is not None and y is not None:
        x_expr = str(x)
        y_expr = str(y)
    else:
        if position == "top-left":
            x_expr = "10"
            y_expr = "10"
        elif position == "top-right":
            x_expr = "w-tw-10"
            y_expr = "10"
        elif position == "bottom-left":
            x_expr = "10"
            y_expr = "h-th-10"
        elif position == "center":
            x_expr = "(w-tw)/2"
            y_expr = "(h-th)/2"
        else:
            x_expr = "w-tw-10"
            y_expr = "h-th-10"
    enable_expr = f"between(t,{start:.3f},{end:.3f})"
    font_part = f"fontfile=/path/to/font.ttf:" if fontfile else ""
    filter_str = f"drawtext={font_part}text='{txt}':fontsize={fontsize}:x={x_expr}:y={y_expr}:enable='{enable_expr}':box=1:boxborderw=10:boxcolor=black@0.3"
    return filter_str


def apply_stickers_to_video(input_video: str, stickers: List[Dict[str, Any]], out_video: str,
                            sticker_dirs: Optional[List[str]] = None):
    """
    Apply sticker overlays. This version resolves any provided image references by:
     - using them if they exist,
     - attempting to find matching sticker files in sticker_dirs if path missing,
     - downloading URLs if content.image is a http(s) URL,
     - falling back to drawtext if image cannot be resolved.
    """
    if not stickers:
        run_cmd(["ffmpeg", "-y", "-i", input_video, "-c", "copy", out_video])
        return

    if sticker_dirs is None:
        sticker_dirs = DEFAULT_STICKER_DIRS
    ensure_dirs_exist(sticker_dirs)
    try:
        os.makedirs(sticker_dirs[0], exist_ok=True)
    except Exception:
        pass

    # Resolve content.image references: try to map non-existent paths to local sticker files or download URLs
    resolved_image_stickers = []
    unresolved_drawtext_stickers = []

    # First: handle name-based stickers (content may contain 'name'/'label'/'text' as the sticker name)
    for s in stickers:
        content = s.get("content", {}) or {}
        if isinstance(content, dict) and "image" not in content and "emoji" not in content:
            # look for name/label/text keys
            candidate_name = None
            if "name" in content:
                candidate_name = content["name"]
            elif "label" in content:
                candidate_name = content["label"]
            elif "text" in content:
                candidate_name = content["text"]
            elif isinstance(content, str) and content.strip():
                candidate_name = content
            if candidate_name:
                found = find_local_sticker_by_name(str(candidate_name), search_dirs=sticker_dirs)
                if found:
                    s["content"] = {"image": found}
                else:
                    # keep s as drawtext fallback
                    pass

    # Next: emoji -> image flow unchanged (reuse your earlier logic)
    for s in stickers:
        content = s.get("content", {}) or {}
        if isinstance(content, dict) and "emoji" in content and "image" not in content:
            emoji_char = content["emoji"]
            img_path = find_or_fetch_sticker_image_for_emoji(emoji_char, sticker_dirs=sticker_dirs)
            if img_path:
                s["content"] = {"image": img_path}
            else:
                # keep for drawtext fallback
                pass

    # Now, go over stickers and decide which ones can be image overlays vs drawtext
    for s in stickers:
        content = s.get("content", {}) or {}
        if isinstance(content, dict) and "image" in content:
            img_ref = content["image"]
            resolved = resolve_image_path(img_ref, sticker_dirs=sticker_dirs)
            if resolved:
                # update to resolved absolute path
                s["content"]["image"] = resolved
                resolved_image_stickers.append(s)
            else:
                print(f"Warning: could not resolve image '{img_ref}' for sticker at {s.get('start')}s. Falling back to drawtext if possible.")
                unresolved_drawtext_stickers.append(s)
        else:
            # not an image sticker (text or emoji w/o image) -> drawtext
            unresolved_drawtext_stickers.append(s)

    # If no resolved images, fall back to drawtext-only pipeline
    if not resolved_image_stickers:
        vf_parts = []
        for s in unresolved_drawtext_stickers:
            content = s.get("content", {}) or {}
            text = ""
            if isinstance(content, dict):
                text = content.get("text") or content.get("emoji") or ""
            elif isinstance(content, str):
                text = content
            pos = s.get("position", "bottom-right")
            vf_parts.append(build_drawtext_filter(text, s["start"], s["end"], pos, s.get("x"), s.get("y"), s.get("fontsize", 72)))
        vf = ",".join(vf_parts) if vf_parts else None
        if vf:
            cmd = [
                "ffmpeg", "-y",
                "-i", input_video,
                "-vf", vf,
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                "-c:a", "aac", "-b:a", "128k",
                out_video
            ]
        else:
            cmd = ["ffmpeg", "-y", "-i", input_video, "-c", "copy", out_video]
        run_cmd(cmd)
        return

    # Build ffmpeg command with video + resolved image inputs
    cmd = ["ffmpeg", "-y", "-i", input_video]
    image_inputs = []
    for s in resolved_image_stickers:
        img = s["content"]["image"]
        cmd += ["-i", img]
        image_inputs.append((s, img))

    # Build filter_complex chaining overlays for only the resolved ones
    filter_parts = []
    last_label = "[0:v]"
    input_idx = 1
    for (s, img) in image_inputs:
        start = s["start"]
        end = s["end"]
        pos = s.get("position", "bottom-right")
        x = s.get("x")
        y = s.get("y")
        if x is not None and y is not None:
            x_expr = str(x); y_expr = str(y)
        else:
            if pos == "top-left":
                x_expr = "10"; y_expr = "10"
            elif pos == "top-right":
                x_expr = "main_w-overlay_w-10"; y_expr = "10"
            elif pos == "bottom-left":
                x_expr = "10"; y_expr = "main_h-overlay_h-10"
            elif pos == "center":
                x_expr = "(main_w-overlay_w)/2"; y_expr = "(main_h-overlay_h)/2"
            else:
                x_expr = "main_w-overlay_w-10"; y_expr = "main_h-overlay_h-10"
        enable_expr = f"between(t,{start:.3f},{end:.3f})"
        in_label = f"[{input_idx}:v]"
        out_label = f"[v{input_idx}]"
        filter_parts.append(f"{last_label}{in_label}overlay={x_expr}:{y_expr}:enable='{enable_expr}'{out_label}")
        last_label = out_label
        input_idx += 1

    # If there are any unresolved drawtext stickers, append them now using last_label
    if unresolved_drawtext_stickers:
        draw_parts = []
        for s in unresolved_drawtext_stickers:
            content = s.get("content", {}) or {}
            text = ""
            if isinstance(content, dict):
                text = content.get("text") or content.get("emoji") or ""
            elif isinstance(content, str):
                text = content
            pos = s.get("position", "bottom-right")
            fontsize = s.get("fontsize", 72)
            if s.get("x") is not None and s.get("y") is not None:
                x_expr = str(s.get("x")); y_expr = str(s.get("y"))
            else:
                if pos == "top-left":
                    x_expr = "10"; y_expr = "10"
                elif pos == "top-right":
                    x_expr = "w-tw-10"; y_expr = "10"
                elif pos == "bottom-left":
                    x_expr = "10"; y_expr = "h-th-10"
                elif pos == "center":
                    x_expr = "(w-tw)/2"; y_expr = "(h-th)/2"
                else:
                    x_expr = "w-tw-10"; y_expr = "h-th-10"
            enable_expr = f"between(t,{s['start']:.3f},{s['end']:.3f})"
            txt = escape_drawtext_text(text)
            draw_parts.append(f"drawtext=text='{txt}':fontsize={fontsize}:x={x_expr}:y={y_expr}:enable='{enable_expr}':box=1:boxborderw=10:boxcolor=black@0.3")
        draw_chain = ",".join(draw_parts)
        if filter_parts:
            filter_complex = ";".join(filter_parts) + ";" + f"{last_label}{draw_chain}[vout]"
        else:
            filter_complex = f"{last_label}{draw_chain}[vout]"
        final_label = "[vout]"
    else:
        filter_complex = ";".join(filter_parts) if filter_parts else ""
        final_label = last_label

    full_cmd = cmd + ["-filter_complex", filter_complex, "-map", final_label, "-map", "0:a?", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-c:a", "aac", "-b:a", "128k", out_video]
    run_cmd(full_cmd)

    # (Optional) If you want to clean downloaded twemoji images for privacy, remove files in downloaded_temp_images here.


def resolve_image_path(image_ref: str, sticker_dirs: Optional[List[str]] = None) -> Optional[str]:
    """
    Resolve an image reference to an actual local file path:
    - if image_ref exists as a file -> return abs path
    - else if image_ref looks like a URL -> download to temp and return path
    - else try to find a matching file in sticker_dirs by basename tokens
    - else return None
    """
    if not image_ref:
        return None

    # 1) If file exists as given (absolute or relative), use it
    if os.path.isfile(image_ref):
        return os.path.abspath(image_ref)

    # 2) If it's a URL, download it
    parsed = urllib.parse.urlparse(image_ref)
    if parsed.scheme in ("http", "https"):
        dl = download_url_to_temp(image_ref)
        if dl:
            return dl
        return None

    # 3) Try token-based search in sticker_dirs using basename (strip extension)
    basename = os.path.basename(image_ref)
    base_no_ext = os.path.splitext(basename)[0]
    # try direct name search first
    found = find_local_sticker_by_name(base_no_ext, search_dirs=sticker_dirs)
    if found:
        return found

    # 4) If the provided image_ref contains directory components, try to use the last two path components as tokens
    parts = re.findall(r"[a-z0-9]+", base_no_ext.lower())
    if parts:
        joined = "".join(parts)
        # fallback search through sticker dirs
        if sticker_dirs is None:
            sticker_dirs = DEFAULT_STICKER_DIRS
        ensure_dirs_exist(sticker_dirs)
        for d in sticker_dirs:
            if not os.path.isdir(d):
                continue
            for fname in os.listdir(d):
                lf = fname.lower()
                if not (lf.endswith(".png") or lf.endswith(".webp") or lf.endswith(".jpg") or lf.endswith(".jpeg")):
                    continue
                base = lf.rsplit(".", 1)[0]
                compact = re.sub(r"[^a-z0-9]", "", base)
                if joined in compact:
                    return os.path.join(d, fname)
    return None


# ----------------------------
# Music support (Jamendo + local + URL)
# ----------------------------
JAMENDO_CLIENT_ID = os.getenv("JAMENDO_CLIENT_ID", "f24ed52c")

def download_url_to_temp_audio(url: str) -> Optional[str]:
    """Download a URL (audio) to a temp file and return the path, or None on failure."""
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return None
        ext = os.path.splitext(parsed.path)[1] or ".mp3"
        fd, tmp = tempfile.mkstemp(suffix=ext)
        os.close(fd)
        print(f"Downloading audio from {url} -> {tmp}")
        urllib.request.urlretrieve(url, tmp)
        if os.path.getsize(tmp) > 0:
            return tmp
        else:
            os.remove(tmp)
            return None
    except Exception as e:
        print("download_url_to_temp_audio failed:", e)
        return None


def search_jamendo_track(query: str) -> Optional[Dict[str, Any]]:
    """
    Use Jamendo API to search tracks. Returns the track dict (first result) or None.
    Requires JAMENDO_CLIENT_ID env var set. Jamendo returns license info — respect it.
    """
    if not JAMENDO_CLIENT_ID:
        return None
    try:
        q = urllib.parse.quote(query)
        url = f"https://api.jamendo.com/v3.0/tracks/?client_id={JAMENDO_CLIENT_ID}&format=json&limit=6&include=licenses&audioformat=mp32&search={q}"
        print("Jamendo search URL:", url)
        res = urllib.request.urlopen(url, timeout=15)
        txt = res.read().decode("utf-8")
        data = json.loads(txt)
        if "results" in data and len(data["results"]) > 0:
            return data["results"][0]
    except Exception as e:
        print("Jamendo search failed:", e)
    return None


def fetch_jamendo_audio(track_info: Dict[str, Any], out_dir: Optional[str] = None) -> Optional[str]:
    """
    Download the Jamendo track audio to out_dir and return path. track_info should contain 'audio' or 'files'.
    """
    if not track_info:
        return None
    try:
        audio_url = None
        if "audio" in track_info and track_info["audio"]:
            audio_url = track_info["audio"]
        else:
            for v in track_info.values():
                if isinstance(v, str) and v.startswith("http"):
                    audio_url = v
                    break
        if not audio_url:
            print("No audio URL in Jamendo result")
            return None
        if out_dir is None:
            out_dir = os.path.join(tempfile.gettempdir(), "jamendo_cache")
        os.makedirs(out_dir, exist_ok=True)
        track_id = track_info.get("id") or ""
        name = re.sub(r"[^a-z0-9]+", "_", track_info.get("name", "track").lower())[:40]
        ext = os.path.splitext(urllib.parse.urlparse(audio_url).path)[1] or ".mp3"
        out_path = os.path.join(out_dir, f"{track_id}_{name}{ext}")
        if os.path.isfile(out_path) and os.path.getsize(out_path) > 1000:
            return out_path
        print(f"Downloading Jamendo audio {audio_url} -> {out_path}")
        urllib.request.urlretrieve(audio_url, out_path)
        if os.path.isfile(out_path) and os.path.getsize(out_path) > 1000:
            return out_path
    except Exception as e:
        print("fetch_jamendo_audio failed:", e)
    return None


DEFAULT_MUSIC_DIRS = ["./music", "./tracks", "./audio"]
for md in DEFAULT_MUSIC_DIRS:
    try:
        os.makedirs(md, exist_ok=True)
    except Exception:
        pass


def find_local_music_by_query(query: str, search_dirs: Optional[List[str]] = None) -> Optional[str]:
    """
    Search local music directories for a file matching the query tokens.
    """
    if search_dirs is None:
        search_dirs = DEFAULT_MUSIC_DIRS
    ensure_dirs_exist(search_dirs)
    tokens = re.findall(r"[a-z0-9]+", (query or "").lower())
    if not tokens:
        return None
    joined = "".join(tokens)
    for d in search_dirs:
        if not os.path.isdir(d):
            continue
        for fname in os.listdir(d):
            full = os.path.join(d, fname)
            if not os.path.isfile(full):
                continue
            lf = fname.lower()
            if not lf.endswith((".mp3", ".m4a", ".wav", ".aac", ".ogg")):
                continue
            base = lf.rsplit(".", 1)[0]
            if all(token in base for token in tokens):
                return full
            compact = re.sub(r"[^a-z0-9]", "", base)
            if joined and joined in compact:
                return full
    return None


def search_and_fetch_music(edit: Dict[str, Any]) -> Optional[str]:
    """
    Given a music edit dict (with keys query/url/file), return a local audio filepath (downloaded or existing).
    Uses Jamendo if JAMENDO_CLIENT_ID is set and 'query' provided. Accepts direct URLs.
    """
    # 1) user provided local file path
    if edit.get("file"):
        if os.path.isfile(edit["file"]):
            return os.path.abspath(edit["file"])
    # 2) user provided a URL
    if edit.get("url"):
        maybe = download_url_to_temp_audio(edit["url"])
        if maybe:
            return maybe
    # 3) search local music dir
    if edit.get("query"):
        q = edit["query"]
        local = find_local_music_by_query(q)
        if local:
            return local
        # 4) try Jamendo (if enabled)
        if JAMENDO_CLIENT_ID:
            jm_info = search_jamendo_track(q)
            if jm_info:
                jm = fetch_jamendo_audio(jm_info)
                if jm:
                    return jm
    return None


# ----------------------------
# Background music mixing helpers
# ----------------------------
def has_audio(path: str) -> bool:
    cmd = ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "default=noprint_wrappers=1:nokey=1", path]
    res = subprocess.run(cmd, capture_output=True, text=True)
    return bool(res.stdout.strip())


def prepare_music_for_duration(music_path: str, duration: float, volume: float = 0.4, loop: bool = True) -> Optional[str]:
    """
    Create a temporary audio file of exactly `duration` seconds by trimming/looping the source music
    and applying volume. Returns path to prepared audio file (audio-only).
    - Produces AAC/.m4a preferred; falls back to MP3/.mp3 (libmp3lame) if AAC fails.
    - Uses -vn to drop any attached cover art streams.
    - Ensures the file is audio-only and matches requested duration (using -t).
    """
    if not os.path.isfile(music_path):
        print("prepare_music_for_duration: music_path not found:", music_path)
        return None

    def _try_encode(out_path: str, codec_args: List[str]) -> bool:
        cmd = ["ffmpeg", "-y"]
        if loop:
            cmd += ["-stream_loop", "-1"]
        cmd += ["-vn", "-i", music_path, "-t", f"{duration:.3f}", "-af", f"volume={volume:.6f}"]
        cmd += codec_args + [out_path]
        try:
            run_cmd(cmd)
            # sanity check
            if os.path.isfile(out_path) and os.path.getsize(out_path) > 1000:
                return True
            return False
        except Exception as e:
            print("prepare_music_for_duration: encoding attempt failed:", e)
            try:
                if os.path.exists(out_path):
                    os.remove(out_path)
            except Exception:
                pass
            return False

    # Preferred: AAC in .m4a container
    fd, out_m4a = tempfile.mkstemp(suffix=".m4a")
    os.close(fd)
    if _try_encode(out_m4a, ["-c:a", "aac", "-b:a", "192k"]):
        return out_m4a

    # Fallback: MP3 in .mp3 using libmp3lame
    try:
        if os.path.exists(out_m4a):
            os.remove(out_m4a)
    except Exception:
        pass

    fd2, out_mp3 = tempfile.mkstemp(suffix=".mp3")
    os.close(fd2)
    if _try_encode(out_mp3, ["-c:a", "libmp3lame", "-b:a", "192k"]):
        return out_mp3

    # Both failed: cleanup
    for p in (out_m4a, out_mp3):
        try:
            if p and os.path.exists(p):
                os.remove(p)
        except Exception:
            pass
    return None



def mix_background_music(input_video: str, music_source_path: str, out_video: str,
                         music_query: Optional[str] = None, music_duration: Optional[float] = None,
                         music_volume: float = 0.4, loop: bool = True,
                         # extra keyword args your callers might pass:
                         music_start: float = 0.0, music_end: Optional[float] = None,
                         reduce_original_volume: float = 1.0, music_loop: bool = True,
                         fade: float = 0.0):
    """
    Mix background music into `input_video` and write `out_video`.
    This version tries to avoid re-encoding the video by using -c:v copy
    (fast) because we only modify audio streams.

    Parameters:
      - input_video: path to intermediate (timeline+stickers) video
      - music_source_path: resolved local path or URL to the music file
      - out_video: target output path
      - music_start: place the beginning of the prepared music at this second in the video timeline
      - music_end: end time in video timeline for the music (if None -> video end)
      - music_volume: target music volume factor (0.0-1.0) used when preparing the music
      - reduce_original_volume: multiplier applied to the video's original audio (1.0 = unchanged)
      - music_loop: whether to loop the source audio if it's shorter than desired music segment
      - fade: placeholder (no-op) — if you want afade implemented say so
    """
    # 1) Get video duration
    try:
        vid_dur = get_duration(input_video)
    except Exception as e:
        raise RuntimeError(f"Unable to get duration of input video: {e}")

    # if music_end not specified, music plays until end of video
    if music_end is None:
        music_end = vid_dur

    # clamp
    music_start = max(0.0, min(music_start, vid_dur))
    music_end = max(0.0, min(music_end, vid_dur))
    if music_end <= music_start:
        raise ValueError("music_end must be greater than music_start after clamping to video duration")

    music_segment_duration = music_end - music_start
    if music_segment_duration <= 0:
        raise ValueError("music segment duration <= 0")

    # 2) resolve music_source_path (if URL, download)
    music_file = None
    parsed = urllib.parse.urlparse(music_source_path)
    if parsed.scheme in ("http", "https"):
        music_file = download_url_to_temp_audio(music_source_path)
        if not music_file:
            raise RuntimeError("Failed to download music from URL: " + music_source_path)
    else:
        if os.path.isfile(music_source_path):
            music_file = os.path.abspath(music_source_path)
        else:
            raise RuntimeError(f"Music file not found: {music_source_path}")

    # 3) prepare trimmed/looped/volume-adjusted music (audio-only)
    prepared = prepare_music_for_duration(music_file, duration=music_segment_duration, volume=music_volume, loop=music_loop)
    if not prepared:
        raise RuntimeError("Failed to prepare music file")

    # 4) build filter_complex: delay music by music_start (ms)
    adelay_ms = int(round(music_start * 1000.0))
    stereo_delay = f"{adelay_ms}|{adelay_ms}"  # for two channels

    video_has_audio = has_audio(input_video)

    if video_has_audio:
        # Reduce original audio level and mix with music.
        # Use amix duration=first so result follows the video's audio length (avoid 'longest')
        # Filter chain:
        #   [0:a]volume=reduce_original_volume[va];
        #   [1:a]adelay=... , apad [mv];
        #   [va][mv]amix=inputs=2:duration=first:dropout_transition=2[aout]
        filter_parts = []
        filter_parts.append(f"[0:a]volume={reduce_original_volume:.6f}[va]")

        if adelay_ms > 0:
            filter_parts.append(f"[1:a]adelay={stereo_delay},apad[mv]")
        else:
            filter_parts.append(f"[1:a]apad[mv]")

        filter_parts.append("[va][mv]amix=inputs=2:duration=first:dropout_transition=2[aout]")

        filter_complex = ";".join(filter_parts)

        # IMPORTANT: copy video stream to avoid heavy re-encode
        cmd = [
            "ffmpeg", "-y",
            "-i", input_video,
            "-i", prepared,
            "-filter_complex", filter_complex,
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",          # <-- fast: don't re-encode video
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            out_video
        ]
    else:
        # If input has no audio, just add the prepared music (delayed)
        if adelay_ms > 0:
            filter_complex = f"[1:a]adelay={stereo_delay},apad[aout]"
        else:
            filter_complex = f"[1:a]apad[aout]"

        cmd = [
            "ffmpeg", "-y",
            "-i", input_video,
            "-i", prepared,
            "-filter_complex", filter_complex,
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",          # copy video, only changing audio
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            out_video
        ]

    try:
        run_cmd(cmd)
    finally:
        # cleanup prepared file if a temp in tempdir
        try:
            if prepared and prepared.startswith(tempfile.gettempdir()):
                os.remove(prepared)
        except Exception:
            pass





# ----------------------------
# High-level process wrapper which uses Gemini
# ----------------------------
def process_with_gemini(input_path: str, user_prompt: str, output_path: str,
                        api_key: str, model_name: str = "gemini-2.0-flash"):
    print("Requesting edits from Gemini...")
    json_text = call_gemini_json(user_prompt, api_key=api_key, model_name=model_name)
    edits = json.loads(json_text)

    duration = get_duration(input_path)
    print(f"Input duration: {duration:.3f} seconds")

    edits = normalize_and_validate_edits(edits, duration)
    print("Parsed edits:", json.dumps(edits, indent=2))

    sticker_edits = [e for e in edits if e["action"] == "sticker"]
    music_edits = [e for e in edits if e["action"] == "music"]
    timeline_edits = [e for e in edits if e["action"] in ("cut", "speed")]

    segments = build_segments_to_keep(timeline_edits, duration)
    print("Planned segments:", json.dumps(segments, indent=2))

    temp_files: List[str] = []
    try:
        for i, seg in enumerate(segments):
            fd, tmp = tempfile.mkstemp(suffix=".mp4")
            os.close(fd)
            os.unlink(tmp)
            out_path_tmp = tmp
            create_segment(input_path, seg, out_path_tmp)
            temp_files.append(out_path_tmp)

        if not temp_files:
            raise RuntimeError("No output segments created (maybe the entire video was cut?).")

        intermediate = output_path + ".intermediate.mp4"
        concat_segments(temp_files, intermediate)
        print("Intermediate (timeline edits applied) written to", intermediate)

        after_stickers_path = intermediate
        if sticker_edits:
            print("Applying sticker overlays:", json.dumps(sticker_edits, indent=2))
            tmp_with_stickers = output_path + ".withstickers.mp4"
            apply_stickers_to_video(intermediate, sticker_edits, tmp_with_stickers)
            after_stickers_path = tmp_with_stickers
            try:
                os.remove(intermediate)
            except Exception:
                pass

        if music_edits:
            # Simplify: support the first music edit (can be extended to multiple)
            m = music_edits[0]
            print("Processing music edit:", json.dumps(m, indent=2))
            music_file = search_and_fetch_music(m)
            if not music_file:
                raise RuntimeError("Could not find or download music for query/url/file in edit: " + str(m))
            mix_background_music(after_stickers_path, music_file, output_path,
                                 music_start=m["start"], music_end=m["end"],
                                 music_volume=m.get("volume", 0.4), reduce_original_volume=1.0,
                                 music_loop=m.get("loop", True), fade=1.0)
            # cleanup intermediate sticker file
            if after_stickers_path != intermediate:
                try:
                    os.remove(after_stickers_path)
                except Exception:
                    pass
        else:
            os.replace(after_stickers_path, output_path)
            print("Output written to", output_path)
    finally:
        for p in temp_files:
            try:
                os.remove(p)
            except Exception:
                pass


# ----------------------------
# Manual pipeline: use when JSON is known (skips Gemini)
# ----------------------------
def process_with_manual_edits(input_path: str, edits_json_text: str, output_path: str):
    edits = json.loads(edits_json_text)
    duration = get_duration(input_path)
    edits = normalize_and_validate_edits(edits, duration)
    sticker_edits = [e for e in edits if e["action"] == "sticker"]
    music_edits = [e for e in edits if e["action"] == "music"]
    timeline_edits = [e for e in edits if e["action"] in ("cut", "speed")]
    segments = build_segments_to_keep(timeline_edits, duration)

    temp_files: List[str] = []
    try:
        for i, seg in enumerate(segments):
            fd, tmp = tempfile.mkstemp(suffix=".mp4")
            os.close(fd)
            os.unlink(tmp)
            create_segment(input_path, seg, tmp)
            temp_files.append(tmp)
        intermediate = output_path + ".intermediate.mp4"
        concat_segments(temp_files, intermediate)

        after_stickers_path = intermediate
        if sticker_edits:
            tmp_with_stickers = output_path + ".withstickers.mp4"
            apply_stickers_to_video(intermediate, sticker_edits, tmp_with_stickers)
            after_stickers_path = tmp_with_stickers
            try:
                os.remove(intermediate)
            except Exception:
                pass

        if music_edits:
            m = music_edits[0]
            music_file = search_and_fetch_music(m)
            if not music_file:
                raise RuntimeError("Could not find or download music for query/url/file in edit: " + str(m))
            mix_background_music(after_stickers_path, music_file, output_path,
                                 music_start=m["start"], music_end=m["end"],
                                 music_volume=m.get("volume", 0.4), reduce_original_volume=1.0,
                                 music_loop=m.get("loop", True), fade=1.0)
            if after_stickers_path != intermediate:
                try:
                    os.remove(after_stickers_path)
                except Exception:
                    pass
        else:
            os.replace(after_stickers_path, output_path)
        print("Output written to", output_path)
    finally:
        for p in temp_files:
            try:
                os.remove(p)
            except Exception:
                pass


# ----------------------------
# Hardcoded test calls (edit for your environment)
# ----------------------------
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyAVSGUozgbc7AQs4xEhP_-xaTGtN78HBFU")

def _test_gemini_run(user_prompt: str):
    input_path = "input.mp4"         # <- change to a real file
    output_path = "output_gemini_test.mp4"
    process_with_gemini(input_path, user_prompt, output_path, api_key=GOOGLE_API_KEY)

# Example tests:
# _test_gemini_run("Place mochi cats sticker at bottom left between 0:20 and 0:25")
_test_gemini_run("Add Lungi Dance bollywood song throughout")

def _test_manual_run():
    input_path = "input.mp4"
    output_path = "output_manual_test.mp4"
    edits = [
        {"action":"speed","start":10.0,"end":15.0,"rate":1.5},
        {"action":"sticker","start":20.0,"end":22.0,"content":{"emoji":"🔥"},"position":"bottom-right","fontsize":96}
    ]
    process_with_manual_edits(input_path, json.dumps(edits), output_path)

# Uncomment to use manual test
# _test_manual_run()

# End of file
