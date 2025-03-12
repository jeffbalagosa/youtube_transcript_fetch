from youtube_transcript_api import YouTubeTranscriptApi
import sys
import re


def get_video_id(url):
    """Extract video ID from YouTube URL"""
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


def print_transcript(youtube_url):
    try:
        # Get video ID from URL
        video_id = get_video_id(youtube_url)

        # Get transcript
        transcript = YouTubeTranscriptApi.get_transcript(video_id)

        # Build full transcript string without line breaks
        full_transcript = ""
        for entry in transcript:
            time = entry["start"]
            minutes = int(time // 60)
            seconds = int(time % 60)
            text = entry["text"].replace(
                "\n", " "
            )  # Replace any existing newlines with spaces
            full_transcript += f"[{minutes:02d}:{seconds:02d}] {text} "

        # Print as a single line, removing trailing space
        print(full_transcript.strip())

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
    print_transcript(youtube_url)


if __name__ == "__main__":
    main()
