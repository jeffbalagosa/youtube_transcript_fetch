#!/usr/bin/env python3
"""
Hybrid YouTube transcript fetcher
• Step 1: timedtext scrape (manual subs)
• Step 2: yt-dlp (auto or manual subs)
• Step 3: youtube-transcript-api fallback
Outputs one line: [MM:SS] text …
"""

import argparse
import logging
import warnings
import re
import sys
import json
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict

# Summarization prompt (must match spec exactly)
SUMMARIZE_PROMPT = (
    "Act as an expert summarizer. Analyze the provided transcript and extract the most important key takeaways, "
    "focusing on main ideas, insights, and actionable points. Present them as a concise bullet list.\n\n"
    "Example Output:\n"
    "- Key takeaway 1\n"
    "- Key takeaway 2\n"
    "- Key takeaway 3\n\n"
    "Input:"
)

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


# ---------- yt-dlp helpers ---------------------------------------------- #
class YtDlpLogger:
    """Adapter that honors verbosity preference while preserving errors."""

    def __init__(self, verbose: bool):
        self.verbose = verbose
        self._logger = logging.getLogger("yt_dlp")

    def debug(self, msg):
        if self.verbose:
            self._logger.debug(msg)

    def info(self, msg):
        if self.verbose:
            self._logger.info(msg)

    def warning(self, msg):
        if self.verbose:
            self._logger.warning(msg)

    def error(self, msg):
        self._logger.error(msg)

    def critical(self, msg):
        self._logger.critical(msg)

    def exception(self, msg):
        self._logger.exception(msg)


def yt_dlp_options(verbose: bool) -> Dict:
    """Return common yt-dlp options tailored to verbosity preference."""
    return {
        "skip_download": True,
        "ignore_no_formats_error": True,
        "quiet": not verbose,
        "no_warnings": not verbose,
        "logger": YtDlpLogger(verbose),
    }


# ---------- metadata ----------------------------------------------------- #
def get_meta_and_info(
    url: str,
    verbose: bool = False,
) -> tuple[Dict[str, str], Dict]:
    """
    Return ({"title": str, "channel": str}, info_dict).
    Falls back to empty strings on failure but preserves info dict for reuse.
    """
    try:
        opts = yt_dlp_options(verbose)
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
        title = info.get("title") or ""
        # Prefer 'channel' when available; fall back to 'uploader'
        channel = (info.get("channel") or info.get("uploader") or "")
        return {"title": title, "channel": channel}, info
    except Exception:
        return {"title": "", "channel": ""}, {}


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
def dlp_captions(
    url: str,
    lang: str = "en",
    info: Dict = None,
    verbose: bool = False,
) -> List[Dict]:
    if info is None:
        opts = yt_dlp_options(verbose)
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
                "start": (int(n.attrib["t"]) / 1000)
                if "t" in n.attrib
                else n.attrib["start"],
                "text": (n.text or "").replace("\n", " "),
            }
            for n in root.findall(".//text")
        ]


# ---------- 3. youtube-transcript-api ----------------------------------- #
def api_captions(
    video_id: str, langs=("en", "en-US", "en-GB")
) -> List[Dict]:
    for lang in langs:
        try:
            return YouTubeTranscriptApi.get_transcript(
                video_id, languages=[lang]
            )
        except (NoTranscriptFound, TranscriptsDisabled):
            continue
    return YouTubeTranscriptApi.get_transcript(video_id)  # let it throw


# ---------- arg parsing -------------------------------------------------- #
def parse_args(argv: List[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Fetch YouTube transcripts with multiple fallbacks."
    )
    parser.add_argument(
        "url",
        help=(
            "YouTube video URL to fetch transcripts from."
        ),
    )
    parser.add_argument(
        "--json",
        dest="json",
        action="store_true",
        help="Emit transcript as JSON.",
    )
    parser.add_argument(
        "--verbose",
        dest="verbose",
        action="store_true",
        help=(
            "Show warnings emitted by the tool and dependencies."
        ),
    )
    parser.add_argument(
        "--summarize",
        dest="summarize",
        action="store_true",
        help=("Prepend a fixed summarization prompt to stdout before the transcript."),
    )
    return parser.parse_args(argv)


# ---------- runtime config ---------------------------------------------- #
def configure_runtime(verbose: bool) -> None:
    """
    Tune warnings and logging output depending on verbosity preference.
    """
    warnings.simplefilter("default" if verbose else "ignore")
    log_level = logging.WARNING if verbose else logging.ERROR
    logging.basicConfig(level=log_level, force=True)
    for name in ("yt_dlp", "youtube_transcript_api"):
        logging.getLogger(name).setLevel(log_level)


# ---------- main --------------------------------------------------------- #
def main():
    args = parse_args()
    url = args.url
    want_json = args.json
    verbose = args.verbose
    summarize = getattr(args, "summarize", False)

    configure_runtime(verbose)

    # Fetch metadata up front (best effort; won't crash the run if it fails)
    meta, info = get_meta_and_info(url, verbose=verbose)

    vid_id = vid(url)
    for step in (
        lambda: scrape_manual(vid_id),
        lambda: dlp_captions(url, info=info, verbose=verbose),
        lambda: api_captions(vid_id),
    ):
        try:
            lines = step()
            transcript = pretty(lines)
            if want_json:
                if summarize:
                    # Prompt must be printed on stdout separately (not embedded in JSON)
                    print(SUMMARIZE_PROMPT)
                    print()
                print(json.dumps(
                    {
                        "title": meta["title"],
                        "channel": meta["channel"],
                        "transcript": transcript
                    },
                    ensure_ascii=False
                ))
            else:
                # Human-friendly default that still pipes fine
                if summarize:
                    # Prompt must precede plain-text transcript and be followed by a blank line
                    print(SUMMARIZE_PROMPT)
                    print()
                if meta["title"] or meta["channel"]:
                    # Print on separate lines so first token remains text
                    # when piping
                    if meta["title"]:
                        print(f"Title: {meta['title']}")
                    if meta["channel"]:
                        print(f"Channel: {meta['channel']}")
                print(transcript)
            return
        except Exception:
            continue
    sys.exit("❌  Couldn't fetch captions from any source.")


if __name__ == "__main__":
    main()
