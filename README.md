# YouTube Transcript Downloader

This Python script extracts transcripts from YouTube videos and prints them to the console as a single line with timestamps. It's useful for quickly getting video transcripts without saving to files.

## Features
- Extracts transcripts from YouTube videos using the video URL
- Outputs timestamps in `[MM:SS]` format followed by the transcript text
- Removes line breaks, presenting all text in a single continuous line
- Supports piping output to clipboard

## Prerequisites
- Python 3.x
- youtube_transcript_api library
- (Optional) xclip for clipboard support on Linux

## Installation

1. **Install Python dependencies**:
   ```bash
   pip install youtube_transcript_api
   ```

2. **Install xclip (Linux only, for clipboard support)**:
   - On Ubuntu/Debian:
     ```bash
     sudo apt-get install xclip
     ```
   - On Fedora:
     ```bash
     sudo dnf install xclip
     ```
   - On Arch:
     ```bash
     sudo pacman -S xclip
     ```

## Usage

Run the script from the command line with a YouTube URL as an argument:

```bash
python3 main.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

### Output Example
```
[00:00] First line of transcript [00:03] Second line of transcript [00:07] Third line of transcript
```

### Piping to Clipboard
- **Linux (with xclip)**:
  ```bash
  python3 main.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" | xclip -selection clipboard
  ```
- **macOS**:
  ```bash
  python3 main.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" | pbcopy
  ```
- **Windows (PowerShell)**:
  ```bash
  python3 main.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" | clip
  ```

After running with clipboard piping, paste the transcript using Ctrl+V (or Cmd+V on macOS).

## Notes
- Not all YouTube videos have transcripts available
- Requires an internet connection
- May encounter rate limits with excessive use
- Supports various YouTube URL formats (watch?v=, youtu.be/, embed/)

## Troubleshooting
- If you get an error about the video ID, check that the URL is valid
- If no transcript is available, you'll see an error message from the API
- Ensure all dependencies are installed correctly

## License
This script is provided as-is for personal use. See the [youtube_transcript_api documentation](https://pypi.org/project/youtube-transcript-api/) for its licensing terms.
