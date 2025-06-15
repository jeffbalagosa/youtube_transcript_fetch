#!/usr/bin/env python3
"""
Hybrid YouTube transcript fetcher
• Step 1: timedtext scrape (manual subs)
• Step 2: yt-dlp (auto or manual subs)
• Step 3: youtube-transcript-api fallback
Outputs one line: [MM:SS] text …
"""

import re, sys, requests, xml.etree.ElementTree as ET
from typing import List, Dict

# 3rd-party deps
from yt_dlp import YoutubeDL  # <-- new
from youtube_transcript_api import (  # unchanged
    YouTubeTranscriptApi,
    NoTranscriptFound,
    TranscriptsDisabled,
)


# ---------- helpers ------------------------------------------------------ #
def vid(url: str) -> str:
    patts = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11})(?:\?|&|/|$)",
        r"(?:youtu\.be\/)([0-9A-Za-z_-]{11})(?:\?|&|/|$)",
    ]
    for p in patts:
        if m := re.search(p, url):
            return m.group(1)
    raise ValueError("Cannot find YouTube video ID in URL.")


def pretty(lines: List[Dict]) -> str:
    segs = []
    for e in lines:
        m, s = divmod(int(float(e["start"])), 60)
        segs.append(f"[{m:02d}:{s:02d}] {e['text'].strip()}")
    return " ".join(segs)


# ---------- 1. timedtext scrape ----------------------------------------- #
def scrape_manual(video_id: str, lang="en") -> List[Dict]:
    url = f"https://video.google.com/timedtext?lang={lang}&v={video_id}"
    r = requests.get(url, timeout=10)
    if not r.ok or not r.text.strip():
        raise RuntimeError("No manual captions.")
    root = ET.fromstring(r.content)
    out = [
        {"start": n.attrib["start"], "text": (n.text or "").replace("\n", " ")}
        for n in root.findall("text")
    ]
    if not out:
        raise RuntimeError("Empty manual track.")
    return out


# ---------- 2. yt-dlp extractor ----------------------------------------- #
def dlp_captions(url: str, lang="en") -> List[Dict]:
    opts = {"skip_download": True, "quiet": True}
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    for src in ("subtitles", "automatic_captions"):
        tracks = info.get(src, {})
        if not tracks:
            continue
        # pick first matching track with a URL we can fetch (vtt or srv3)
        for code, lst in tracks.items():
            if not code.startswith(lang):
                continue
            for t in lst:
                if t["ext"] in {"vtt", "srv3", "srv1"}:
                    return _parse_caption_url(t["url"], t["ext"])
    raise RuntimeError("yt-dlp found no captions.")


def _parse_caption_url(url: str, ext: str) -> List[Dict]:
    txt = requests.get(url, timeout=10).text
    if ext == "vtt":  # very lax VTT → plain
        entries = []
        for block in txt.split("\n\n"):
            if "-->" not in block:
                continue
            timestr, *lines = block.strip().splitlines()
            h, m, s = map(float, re.sub("[^0-9:.]", "", timestr).split(":"))
            start = h * 3600 + m * 60 + s
            entries.append({"start": start, "text": " ".join(lines)})
        return entries
    else:  # srv1/3 = XML
        root = ET.fromstring(txt.encode())
        return [
            {
                "start": n.attrib["t"] / 1000 if "t" in n.attrib else n.attrib["start"],
                "text": (n.text or "").replace("\n", " "),
            }
            for n in root.findall(".//text")
        ]


# ---------- 3. youtube-transcript-api ----------------------------------- #
def api_captions(video_id: str, langs=("en", "en-US", "en-GB")) -> List[Dict]:
    for l in langs:
        try:
            return YouTubeTranscriptApi.get_transcript(video_id, languages=[l])
        except (NoTranscriptFound, TranscriptsDisabled):
            continue
    return YouTubeTranscriptApi.get_transcript(video_id)  # let it throw


# ---------- main --------------------------------------------------------- #
def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python main.py <YouTube URL>")
    url = sys.argv[1]
    vid_id = vid(url)
    for step in (
        lambda: scrape_manual(vid_id),
        lambda: dlp_captions(url),
        lambda: api_captions(vid_id),
    ):
        try:
            lines = step()
            print(pretty(lines))
            return
        except Exception:
            continue
    sys.exit("❌  Couldn’t fetch captions from any source.")


if __name__ == "__main__":
    main()
