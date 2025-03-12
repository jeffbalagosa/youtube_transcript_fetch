# YouTube Transcript Downloader

This Python script extracts transcripts from YouTube videos and prints them to the console as a single line with timestamps. It's useful for quickly getting video transcripts without saving to files.

## Features
- Extracts transcripts from YouTube videos using the video URL
- Outputs timestamps in `[MM:SS]` format followed by the transcript text
- Removes line breaks, presenting all text in a single continuous line
- Supports piping output to clipboard

## Prerequisites
- Python 3.x
- (Optional) xclip for clipboard support on Linux

## Installation

1. **Clone the repository** (if applicable) or copy the files to your working directory:
   - `main.py`
   - `README.md`
   - `requirements.txt`
   - `.gitignore`

2. **Set up a virtual environment**:
   ```bash
   python3 -m venv .venv
   ```
   - On Linux/macOS: Activate it with:
     ```bash
     source .venv/bin/activate
     ```
   - On Windows: Activate it with:
     ```bash
     .venv\Scripts\activate
     ```

3. **Install dependencies from requirements.txt**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install xclip (Linux only, for clipboard support)**:
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

Run the script from the command line with a YouTube URL as an argument (ensure the virtual environment is activated):

```bash
python main.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

### Output Example
```
[00:00] First line of transcript [00:03] Second line of transcript [00:07] Third line of transcript
```

### Piping to Clipboard
- **Linux (with xclip)**:
  ```bash
  python main.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" | xclip -selection clipboard
  ```
- **macOS**:
  ```bash
  python main.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" | pbcopy
  ```
- **Windows (PowerShell)**:
  ```bash
  python main.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" | clip
  ```

After running with clipboard piping, paste the transcript using Ctrl+V (or Cmd+V on macOS).

## Notes
- Not all YouTube videos have transcripts available
- Requires an internet connection
- May encounter rate limits with excessive use
- Supports various YouTube URL formats (watch?v=, youtu.be/, embed/)
- The virtual environment keeps dependencies isolated from your system Python

## Troubleshooting
- If you get an error about the video ID, check that the URL is valid
- If no transcript is available, you'll see an error message from the API
- Ensure the virtual environment is activated and dependencies are installed (`pip list` to check)
- If dependencies fail to install, try updating pip: `pip install --upgrade pip`

## Deactivating the Virtual Environment
When you're done, deactivate the virtual environment:
```bash
deactivate
```

## License
This script is provided as-is for personal use. See the [youtube_transcript_api documentation](https://pypi.org/project/youtube-transcript-api/) for its licensing terms.
