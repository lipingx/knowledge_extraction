# YouTube to WeChat

Convert a YouTube video transcript into:

- the original transcript
- a Chinese transcript
- a WeChat-friendly Markdown article

Important behavior:

- If the source transcript is already Chinese, the script keeps the Chinese body text unchanged.
- If the source transcript is not Chinese, it is translated to Chinese once.
- After Chinese text is available, the script does not rewrite the body text. It only adds a title, section headings, and paragraph spacing for WeChat.

## Requirements

- Python 3.10+
- Internet access for YouTube transcript fetching
- `OPENAI_API_KEY` for non-Chinese videos

## Setup

Recommended: use a virtual environment.

```bash
cd /Users/lipingxiong/Documents/app_dev/knowledge_extraction
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

Create a `.env` file in the project root:

```bash
cat > .env <<'EOF'
OPENAI_API_KEY=your_openai_api_key_here
EOF
```

You can also export the key in your shell instead of using `.env`:

```bash
export OPENAI_API_KEY=your_openai_api_key_here
```

## Run

Run the full video:

```bash
python3 youtube_to_wechat.py "https://www.youtube.com/watch?v=CE2_N7EBX7k"
```

Run a time range:

```bash
python3 youtube_to_wechat.py "https://www.youtube.com/watch?v=CE2_N7EBX7k" --start 10:25 --end 15:28
```

Run with a duration from the start time:

```bash
python3 youtube_to_wechat.py "https://www.youtube.com/watch?v=CE2_N7EBX7k" --start 10:25 --duration 300
```

Choose a custom output directory:

```bash
python3 youtube_to_wechat.py "https://www.youtube.com/watch?v=CE2_N7EBX7k" --output-dir my_articles
```

Choose a different OpenAI model:

```bash
python3 youtube_to_wechat.py "https://www.youtube.com/watch?v=CE2_N7EBX7k" --model gpt-4o-mini
```

## Transcript Only

If you only want the transcript, without Chinese translation and without WeChat formatting, use:

```bash
python3 extract_transcript.py "https://www.youtube.com/watch?v=CE2_N7EBX7k"
```

Extract only a time range:

```bash
python3 extract_transcript.py "https://www.youtube.com/watch?v=CE2_N7EBX7k" --start 10:25 --end 15:28
```

Extract a time range and save it to a file:

```bash
python3 extract_transcript.py "https://www.youtube.com/watch?v=CE2_N7EBX7k" --start 10:25 --end 15:28 --output transcript.txt
```

Use timestamps:

```bash
python3 extract_transcript.py "https://www.youtube.com/watch?v=CE2_N7EBX7k" --start 10:25 --end 15:28 --timestamps
```

## Output

The script writes files into `output/` by default:

- `*_transcript_original.txt`
- `*_transcript_cn.txt`
- `*_wechat_article.md`

## Notes

- `youtube_to_wechat.py` fetches the transcript first.
- For non-Chinese videos, translation happens in step 2.
- The final WeChat Markdown keeps the Chinese body text intact and only changes formatting.
- `extract_transcript.py` prints the transcript to the terminal by default.
- `extract_transcript.py` only saves to disk when you pass `--output`.
- If you pass `--output transcript.txt`, the file is saved relative to your current directory unless you provide an absolute path.
- If `openai` is missing, install dependencies again:

```bash
python3 -m pip install -r requirements.txt
```
