#!/usr/bin/env python3
"""
YouTube to WeChat Article Pipeline

Given a YouTube URL:
1. Extract full transcript
2. Translate to Chinese (if not already Chinese)
3. Save Chinese transcript
4. Format the Chinese transcript for WeChat without rewriting the body text

Usage:
    python youtube_to_wechat.py <youtube_url>
    python youtube_to_wechat.py <youtube_url> --start 10:25 --end 15:28
    python youtube_to_wechat.py <youtube_url> --output-dir my_articles
"""

import argparse
import os
import sys
import json
import re
from datetime import datetime
from youtube_extractor import YouTubeExtractor


def find_openai_api_key():
    """Look for an OpenAI API key in the environment or a nearby .env file."""
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
    return api_key


def try_get_openai_client():
    """Best-effort OpenAI client initialization for optional title generation."""
    try:
        from openai import OpenAI
    except ImportError:
        return None

    api_key = find_openai_api_key()
    if not api_key:
        return None

    return OpenAI(api_key=api_key)


def get_openai_client():
    """Initialize OpenAI client, checking .env file and environment."""
    client = try_get_openai_client()
    if client is not None:
        return client

    try:
        import openai  # noqa: F401
    except ImportError:
        print("Error: openai package not installed. Run `pip install openai`.", file=sys.stderr)
        sys.exit(1)

    api_key = find_openai_api_key()
    if not api_key:
        print("Error: OPENAI_API_KEY not set. Export it or add to .env file.", file=sys.stderr)
        sys.exit(1)

    # This branch is mostly defensive; try_get_openai_client already handles the normal path.
    from openai import OpenAI

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


def is_mostly_chinese(text, threshold=0.3):
    """Heuristic language check used to avoid sending Chinese originals through the LLM."""
    non_whitespace_chars = [char for char in text if not char.isspace()]
    if not non_whitespace_chars:
        return False

    cjk_count = sum(1 for char in non_whitespace_chars if "\u4e00" <= char <= "\u9fff")
    return cjk_count / len(non_whitespace_chars) >= threshold


def translate_to_chinese(client, text, model="gpt-4o-mini"):
    """Translate text to Chinese if it's not already Chinese. Returns (chinese_text, was_translated)."""
    if is_mostly_chinese(text):
        return text, False

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
    return chinese_text, True


def format_chinese_transcript_for_wechat(text):
    """Reformat Chinese text for WeChat without changing the original wording."""
    paragraphs = split_transcript_paragraphs(text)
    return "\n\n".join(paragraphs)


def split_transcript_paragraphs(text):
    """Split transcript into WeChat-friendly paragraphs while preserving original text order."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return []

    blocks = [block.strip() for block in re.split(r"\n\s*\n", normalized) if block.strip()]
    if not blocks:
        return []

    sentence_endings = "。！？!?；;"
    closing_marks = "\"'”’」』）》】）)]}"
    paragraphs = []

    for block in blocks:
        current = []
        index = 0
        while index < len(block):
            char = block[index]
            current.append(char)
            index += 1

            if char == "\n":
                paragraph = "".join(current).strip()
                if paragraph:
                    paragraphs.append(paragraph)
                current = []
                continue

            if char not in sentence_endings:
                continue

            while index < len(block) and block[index] in closing_marks:
                current.append(block[index])
                index += 1

            paragraph = "".join(current).strip()
            if paragraph:
                paragraphs.append(paragraph)
            current = []

        paragraph = "".join(current).strip()
        if paragraph:
            paragraphs.append(paragraph)

    return paragraphs


def group_paragraphs(paragraphs, target_size=4, max_chars=700):
    """Group consecutive paragraphs into titled WeChat sections."""
    sections = []
    current_section = []
    current_chars = 0

    for paragraph in paragraphs:
        paragraph_len = len(paragraph)
        should_split = (
            current_section
            and (len(current_section) >= target_size or current_chars + paragraph_len > max_chars)
        )
        if should_split:
            sections.append(current_section)
            current_section = []
            current_chars = 0

        current_section.append(paragraph)
        current_chars += paragraph_len

    if current_section:
        sections.append(current_section)

    return sections


def build_fallback_title(paragraphs):
    """Create a deterministic title when heading generation is unavailable."""
    if not paragraphs:
        return "视频内容整理"

    first_paragraph = paragraphs[0].replace("\n", "").strip()
    first_paragraph = re.sub(r"[。！？!?；;].*$", "", first_paragraph)
    first_paragraph = first_paragraph[:18].strip()
    return first_paragraph or "视频内容整理"


def build_fallback_section_headings(section_count):
    return [f"第{i + 1}部分" for i in range(section_count)]


def generate_wechat_headings(client, chinese_transcript, sections, video_url, model="gpt-4o-mini"):
    """Generate only the title and section headings. The transcript body is assembled locally."""
    fallback = {
        "title": build_fallback_title(split_transcript_paragraphs(chinese_transcript)),
        "section_headings": build_fallback_section_headings(len(sections)),
    }

    if client is None or not sections:
        return fallback

    section_payload = [
        {
            "index": index + 1,
            "text": "\n".join(section),
        }
        for index, section in enumerate(sections)
    ]

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "你是一位微信公众号编辑，只负责生成标题和小节标题。"
                    "不要改写、润色、总结、删减、扩写正文，也不要返回正文。"
                    "根据给定的中文文字稿分段，输出一个 JSON 对象，格式为："
                    '{"title":"总标题","section_headings":["小节1","小节2"]}。'
                    "要求：总标题 18 字以内；每个小节标题 10 字以内；"
                    "section_headings 的数量必须与 sections 数量一致；"
                    "只输出合法 JSON，不要加 Markdown 代码块，不要加解释。"
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "video_url": video_url,
                        "sections": section_payload,
                    },
                    ensure_ascii=False,
                ),
            },
        ],
        temperature=0.2,
        max_tokens=600,
    )
    content = response.choices[0].message.content.strip()

    try:
        metadata = json.loads(content)
    except json.JSONDecodeError:
        return fallback

    title = str(metadata.get("title", "")).strip() or fallback["title"]
    section_headings = metadata.get("section_headings")
    if not isinstance(section_headings, list) or len(section_headings) != len(sections):
        return {"title": title, "section_headings": fallback["section_headings"]}

    cleaned_headings = []
    for index, heading in enumerate(section_headings):
        heading_text = str(heading).strip()
        cleaned_headings.append(heading_text or fallback["section_headings"][index])

    return {"title": title, "section_headings": cleaned_headings}


def build_wechat_article(chinese_transcript, title, section_headings):
    """Assemble the final Markdown article without changing the Chinese body text."""
    paragraphs = split_transcript_paragraphs(chinese_transcript)
    sections = group_paragraphs(paragraphs)
    lines = []

    if title:
        lines.append(f"# {title}")
        lines.append("")

    if not sections:
        return "\n".join(lines).strip()

    for index, section in enumerate(sections):
        heading = section_headings[index] if index < len(section_headings) else f"第{index + 1}部分"
        if heading:
            lines.append(f"## {heading}")
            lines.append("")

        for paragraph in section:
            lines.append(paragraph)
            lines.append("")

    return "\n".join(lines).rstrip()


def main():
    parser = argparse.ArgumentParser(description="YouTube video to WeChat article pipeline")
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument("--start", help="Start time (e.g. 0, 1:29, 1:24:07)")
    parser.add_argument("--end", help="End time (e.g. 300, 5:00, 1:30:00)")
    parser.add_argument("--duration", type=int, help="Duration in seconds from start")
    parser.add_argument("--output-dir", "-o", default="output", help="Output directory (default: output)")
    parser.add_argument("--model", default="gpt-4o-mini", help="OpenAI model (default: gpt-4o-mini)")
    args = parser.parse_args()

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
    client = None
    if is_mostly_chinese(transcript):
        chinese_text, was_translated = transcript, False
    else:
        client = get_openai_client()
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

    # Step 3: Assemble WeChat article without rewriting the Chinese body text
    print("Step 3/4: Building WeChat article layout...")
    if client is None:
        client = try_get_openai_client()
    paragraphs = split_transcript_paragraphs(chinese_text)
    sections = group_paragraphs(paragraphs)
    metadata = generate_wechat_headings(client, chinese_text, sections, args.url, model=args.model)
    article = build_wechat_article(
        chinese_text,
        metadata["title"],
        metadata["section_headings"],
    )

    article_file = os.path.join(args.output_dir, f"{video_id}_{timestamp}_wechat_article.md")
    with open(article_file, "w", encoding="utf-8") as f:
        f.write(article)
    print(f"  Saved: {article_file}")

    print(f"\nDone! Files in {args.output_dir}/")
    print(f"  Original transcript: {original_file}")
    print(f"  Chinese transcript:  {transcript_file}")
    print(f"  WeChat article:      {article_file}")


if __name__ == "__main__":
    main()
