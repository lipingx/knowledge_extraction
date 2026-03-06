#!/usr/bin/env python3
"""
YouTube to WeChat Article Pipeline

Given a YouTube URL:
1. Extract full transcript
2. Translate to Chinese (if not already Chinese)
3. Save Chinese transcript
4. Generate WeChat public account article with attractive title and opening

Usage:
    python youtube_to_wechat.py <youtube_url>
    python youtube_to_wechat.py <youtube_url> --start 10:25 --end 15:28
    python youtube_to_wechat.py <youtube_url> --output-dir my_articles
"""

import argparse
import os
import sys
import json
from datetime import datetime
from openai import OpenAI
from youtube_extractor import YouTubeExtractor


def get_openai_client():
    """Initialize OpenAI client, checking .env file and environment."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # Search for .env in current dir and up to 3 parent dirs
        search_dir = os.path.abspath(".")
        for _ in range(4):
            env_path = os.path.join(search_dir, ".env")
            if os.path.exists(env_path):
                with open(env_path) as f:
                    for line in f:
                        if line.startswith("OPENAI_API_KEY="):
                            api_key = line.split("=", 1)[1].strip().strip("\"'")
                            break
                if api_key:
                    break
            search_dir = os.path.dirname(search_dir)
    if not api_key:
        print("Error: OPENAI_API_KEY not set. Export it or add to .env file.", file=sys.stderr)
        sys.exit(1)
    return OpenAI(api_key=api_key)


def extract_transcript(url, start_time=None, end_time=None, duration=None):
    """Extract transcript from YouTube video."""
    extractor = YouTubeExtractor()
    segment = extractor.extract_segment(
        url=url,
        start_time=start_time,
        end_time=end_time,
        duration=duration,
    )
    return segment


def translate_to_chinese(client, text, model="gpt-4o-mini"):
    """Translate text to Chinese if it's not already Chinese. Returns (chinese_text, was_translated)."""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "你是一个专业翻译。判断以下文本是否为中文。"
                    "如果已经是中文，直接原样返回。"
                    "如果不是中文，翻译成流畅自然的中文。"
                    "注意：只输出翻译结果，不要加任何说明或前缀。"
                    "保持原文的段落结构和语气。专业术语保留英文并在括号中注明。"
                ),
            },
            {"role": "user", "content": text},
        ],
        temperature=0.3,
    )
    chinese_text = response.choices[0].message.content.strip()
    # Simple heuristic: if more than 30% of original chars are CJK, it was already Chinese
    cjk_count = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
    was_translated = cjk_count / max(len(text), 1) < 0.3
    return chinese_text, was_translated


def generate_wechat_article(client, chinese_transcript, video_url, model="gpt-4o-mini"):
    """Generate a WeChat public account article from the Chinese transcript."""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "你是一位资深的微信公众号内容创作者。"
                    "根据提供的视频文字稿，创作一篇高质量的微信公众号文章。\n\n"
                    "要求：\n"
                    "1. 根据内容自动判断最合适的文章风格（科普分享、专业深度、故事叙述等）\n"
                    "2. 创作一个吸引人的标题（15字以内，可以用数字、疑问句、或引发好奇心的方式）\n"
                    "3. 开头要有吸引力，让读者想继续往下读（可以用痛点切入、故事开头、或反常识观点）\n"
                    "4. 正文分段清晰，每段不要太长，适合手机阅读\n"
                    "5. 适当使用小标题（用 ## ）来组织内容\n"
                    "6. 结尾要有总结或行动建议\n"
                    "7. 文末加上一段引导互动的话（如：你有什么经验？欢迎留言分享）\n\n"
                    "输出格式为 Markdown。第一行是标题（用 # ）。"
                    "不要编造文字稿中没有的信息。"
                ),
            },
            {
                "role": "user",
                "content": f"视频链接：{video_url}\n\n以下是视频文字稿：\n\n{chinese_transcript}",
            },
        ],
        temperature=0.7,
        max_tokens=4000,
    )
    return response.choices[0].message.content.strip()


def main():
    parser = argparse.ArgumentParser(description="YouTube video to WeChat article pipeline")
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument("--start", help="Start time (e.g. 0, 1:29, 1:24:07)")
    parser.add_argument("--end", help="End time (e.g. 300, 5:00, 1:30:00)")
    parser.add_argument("--duration", type=int, help="Duration in seconds from start")
    parser.add_argument("--output-dir", "-o", default="output", help="Output directory (default: output)")
    parser.add_argument("--model", default="gpt-4o-mini", help="OpenAI model (default: gpt-4o-mini)")
    args = parser.parse_args()

    client = get_openai_client()

    # Step 1: Extract transcript
    print("Step 1/4: Extracting transcript...")
    try:
        segment = extract_transcript(args.url, args.start, args.end, args.duration)
    except Exception as e:
        print(f"Error extracting transcript: {e}", file=sys.stderr)
        sys.exit(1)

    video_id = segment.video_id
    transcript = segment.transcript
    print(f"  Video ID: {video_id}")
    print(f"  Time range: {segment.start_time}s - {segment.end_time}s")
    print(f"  Transcript: {len(transcript)} chars")

    # Save original transcript
    os.makedirs(args.output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    original_file = os.path.join(args.output_dir, f"{video_id}_{timestamp}_transcript_original.txt")
    with open(original_file, "w", encoding="utf-8") as f:
        f.write(f"Video: {args.url}\n")
        f.write(f"Time: {segment.start_time}s - {segment.end_time}s\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 60 + "\n\n")
        f.write(transcript)
    print(f"  Saved original: {original_file}")

    # Step 2: Translate to Chinese
    print("Step 2/4: Translating to Chinese...")
    chinese_text, was_translated = translate_to_chinese(client, transcript, model=args.model)
    if was_translated:
        print("  Translated to Chinese.")
    else:
        print("  Already in Chinese, no translation needed.")

    # Save Chinese transcript
    transcript_file = os.path.join(args.output_dir, f"{video_id}_{timestamp}_transcript_cn.txt")
    with open(transcript_file, "w", encoding="utf-8") as f:
        f.write(f"Video: {args.url}\n")
        f.write(f"Time: {segment.start_time}s - {segment.end_time}s\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 60 + "\n\n")
        f.write(chinese_text)
    print(f"  Saved: {transcript_file}")

    # Step 3: Generate WeChat article
    print("Step 3/4: Generating WeChat article...")
    article = generate_wechat_article(client, chinese_text, args.url, model=args.model)

    article_file = os.path.join(args.output_dir, f"{video_id}_{timestamp}_wechat_article.md")
    with open(article_file, "w", encoding="utf-8") as f:
        f.write(article)
        f.write(f"\n\n---\n*Source: {args.url}*\n")
    print(f"  Saved: {article_file}")

    print(f"\nDone! Files in {args.output_dir}/")
    print(f"  Original transcript: {original_file}")
    print(f"  Chinese transcript:  {transcript_file}")
    print(f"  WeChat article:      {article_file}")


if __name__ == "__main__":
    main()
