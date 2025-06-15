# Hybrid YouTube Transcript Fetcher

A **resilient CLI tool** for downloading YouTube video transcripts, even after recent API and scraping restrictions. It:

1. **Scrapes manual captions** using YouTube's `timedtext` endpoint.
2. **Falls back to `yt-dlp`**, which extracts auto-generated captions.
3. **Falls back again** to `youtube-transcript-api` as a last resort.

Outputs a single line of transcript with `[MM:SS]` timestamps—ideal for summarization, pasting, or piping to other tools.

---

## Features

* ✅ No API keys or OAuth required
* ✅ Supports manual and auto-generated captions
* ✅ Works on most public YouTube videos
* ✅ Single-line timestamped output
* ✅ Cross-platform (Linux, macOS, Windows)

---

## Installation

Clone the repo and set up your environment:

```bash
git clone <your-repo-url>
cd youtube_transcript_fetch
python3 -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## Requirements

* Python 3.8+
* `yt-dlp`
* `youtube-transcript-api`
* `requests`

Included in `requirements.txt`:

```
requests>=2.32.0
yt-dlp>=2025.04.10
youtube-transcript-api>=1.0.0
```

---

## Usage

```bash
python main.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

**Example output:**

```
[00:00] We're no strangers to love [00:04] You know the rules and so do I ...
```

---

## Pipe to Clipboard

| OS      | Command example          |                          |
| ------- | ------------------------ | ------------------------ |
| Linux   | \`python main.py "<URL>" | xclip -sel clip\`        |
| macOS   | \`python main.py "<URL>" | pbcopy\`                 |
| Windows | \`python main.py "<URL>" | clip\` (PowerShell only) |

Paste with `Ctrl+V` or `Cmd+V`.

---

## How It Works

1. **Manual Subtitles (scrape):**
   Attempts to fetch captions from:
   `https://video.google.com/timedtext?lang=en&v=<video_id>`

2. **yt-dlp Captions (auto or manual):**
   Parses player JSON and retrieves direct caption download links.
   This works even when `timedtext` is blank.

3. **youtube-transcript-api Fallback:**
   Grabs available transcripts via YouTube’s public API.
   Works best for popular and indexed videos.

---

## Why yt-dlp?

YouTube began returning empty caption XML for many auto-generated tracks.
`yt-dlp` avoids this by pulling the **actual subtitle file URLs** directly from the video player’s metadata.

---

## Troubleshooting

### “no element found: line 1, column 0”

You’re hitting a known issue with `timedtext`. It’s returning an empty blob.
This means the video only has **auto-generated captions**, and you’re not the owner.

**Fix:** This script now falls back to `yt-dlp`, which usually succeeds.

---

### Still failing?

1. Confirm the video actually shows captions via the YouTube player.
2. The video might be region-blocked or age-restricted.
3. If yt-dlp fails, try passing cookies:

   ```
   yt-dlp --cookies-from-browser chrome <URL>
   ```

---

## Roadmap Ideas

* Batch processing of multiple URLs
* Option to output Markdown or plain text
* Language fallback customization
* Auto-copy or export to file

---

## License

MIT – Do whatever you want. No warranty, no guarantees.
