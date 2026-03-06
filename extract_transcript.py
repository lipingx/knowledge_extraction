#!/usr/bin/env python3
"""
Extract full transcript from a YouTube video.

Usage:
    python extract_transcript.py <youtube_url> [--start START] [--end END] [--output FILE]

Examples:
    python extract_transcript.py "https://youtu.be/4jONudu6yGU"
    python extract_transcript.py "https://youtu.be/4jONudu6yGU?t=625" --end 900
    python extract_transcript.py "https://youtu.be/4jONudu6yGU" --start 10:25 --end 15:28 --output transcript.txt
"""

import argparse
import sys
import os
from datetime import datetime
from youtube_extractor import YouTubeExtractor


def main():
    parser = argparse.ArgumentParser(description="Extract transcript from a YouTube video")
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument("--start", help="Start time (e.g. 0, 1:29, 1:24:07)")
    parser.add_argument("--end", help="End time (e.g. 300, 5:00, 1:30:00)")
    parser.add_argument("--duration", type=int, help="Duration in seconds from start")
    parser.add_argument("--output", "-o", help="Output file path (default: print to stdout)")
    parser.add_argument("--timestamps", "-t", action="store_true", help="Include timestamps for each line")
    args = parser.parse_args()

    extractor = YouTubeExtractor()

    try:
        segment = extractor.extract_segment(
            url=args.url,
            start_time=args.start or "0" if args.start is not None else None,
            end_time=args.end,
            duration=args.duration,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Format output
    if args.timestamps:
        text = extractor.format_segment_with_timestamps(segment)
    else:
        text = segment.transcript

    # Output
    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Saved to {args.output} ({len(text)} chars)", file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()
