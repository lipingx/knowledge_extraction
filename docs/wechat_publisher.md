# WeChat Official Account Publisher

This project now includes a standalone script for pushing a prepared article to a WeChat Official Account draft and publish flow:

`publish_to_wechat.py`

## What It Does

- Reads a local UTF-8 article file.
- Uses the first non-empty line as the article title.
- Converts the remaining text into simple WeChat-friendly HTML.
- Uploads a local cover image if you do not already have a `thumb_media_id`.
- Creates a draft article via the WeChat Official Account API.
- Optionally submits that draft for publishing.
- Optionally polls publish status.

## Important Constraints

- Your Official Account must have access to the relevant draft/freepublish APIs.
- The account AppID/AppSecret must be valid.
- WeChat may require IP allowlisting or other platform-side configuration.
- The script has not been live-tested in this repository because no WeChat credentials are checked into the project.

## Environment Variables

You can place these in `.env` or export them in your shell:

```bash
WECHAT_APP_ID=your_wechat_app_id
WECHAT_APP_SECRET=your_wechat_app_secret
WECHAT_AUTHOR=Your Author Name
WECHAT_CONTENT_SOURCE_URL=https://your-site.example.com/original-post
WECHAT_THUMB_MEDIA_ID=optional_existing_cover_media_id
```

## Basic Usage

### 1. Preview generated HTML only

```bash
python3 publish_to_wechat.py \
  content/molly-come-off-ppi-wechat-zh.txt \
  --thumb-media-id your_existing_media_id \
  --dry-run \
  --html-out content/molly-come-off-ppi-wechat-preview.html
```

### 2. Create a draft and stop there

```bash
python3 publish_to_wechat.py \
  content/molly-come-off-ppi-wechat-zh.txt \
  --author "Your Author Name" \
  --thumb-image content/cover.jpg \
  --draft-only
```

### 3. Create a draft and submit it for publishing

```bash
python3 publish_to_wechat.py \
  content/molly-come-off-ppi-wechat-zh.txt \
  --author "Your Author Name" \
  --thumb-image content/cover.jpg \
  --status-poll-seconds 60
```

### 4. Query an existing publish task

```bash
python3 publish_to_wechat.py --check-publish-id your_publish_id
```

## Notes About Article Formatting

- The script is optimized for the text files already produced in this repo.
- It upgrades lines like `一、...` into section headings.
- It preserves short emphasis lines as highlighted paragraphs.
- It keeps the generated HTML intentionally simple because WeChat strips or rewrites some styles.

## Recommended Workflow

1. Finalize the article text file in `content/`.
2. Prepare a cover image.
3. Run with `--dry-run` and inspect the generated HTML file.
4. Run with `--draft-only` first.
5. Confirm the draft looks right in WeChat.
6. Run without `--draft-only` when you are ready to publish.
