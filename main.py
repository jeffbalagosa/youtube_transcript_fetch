from youtube_transcript_api import YouTubeTranscriptApi
import sys
import re
from datetime import datetime


def get_video_id(url):
    """Extract video ID from YouTube URL"""
    # Regular expressions to match different YouTube URL formats
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"(?:embed\/)([0-9A-Za-z_-]{11})",
        r"(?:youtu.be\/)([0-9A-Za-z_-]{11})",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError("Could not extract video ID from URL")


def download_transcript(youtube_url):
    try:
        # Get video ID from URL
        video_id = get_video_id(youtube_url)

        # Get transcript
        transcript = YouTubeTranscriptApi.get_transcript(video_id)

        # Create filename with current timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"transcript_{video_id}_{timestamp}.txt"

        # Write transcript to file
        with open(filename, "w", encoding="utf-8") as file:
            for entry in transcript:
                # Format: [timestamp] text
                time = entry["start"]
                minutes = int(time // 60)
                seconds = int(time % 60)
                text = entry["text"]
                file.write(f"[{minutes:02d}:{seconds:02d}] {text}\n")

        print(f"Transcript successfully saved to {filename}")
        return True

    except Exception as e:
        print(f"Error: {str(e)}")
        return False


def main():
    # Check if URL is provided as command line argument
    if len(sys.argv) != 2:
        print("Usage: python script.py <youtube_url>")
        sys.exit(1)

    youtube_url = sys.argv[1]
    download_transcript(youtube_url)


if __name__ == "__main__":
    main()
