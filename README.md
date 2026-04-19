# Infinite Video Pipeline

End-to-end AI pipeline: **story prompt → illustrated video with narration**.
**No local GPU. No paid API keys required.**

```
"A bunny who discovers a magical garden"
        ↓  Claude (optional) or built-in template engine
        ↓  Pollinations.ai / Craiyon / HuggingFace SDXL (free image gen)
        ↓  edge-tts / gTTS (free narration audio)
        ↓  FFmpeg (image + audio → MP4 per scene → final video)
        ↓
  A_Bunny_Magical_Adventure.mp4  ✅
```

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
brew install ffmpeg   # macOS
```

### 2. (Optional) Set API key for richer stories

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

Without this key the pipeline uses a built-in story template — still fully functional.

### 3. Run

```bash
cd ~/infinite-video-pipeline

# Custom story prompt
python free_pipeline.py "A little elephant who learns to paint"

# Default random prompt
python free_pipeline.py
```

---

## Free AI Services Used

| Service | Purpose | Rate Limit | Auth Required |
|---------|---------|-----------|---------------|
| **Pollinations.ai** | Image generation (primary) | ~5 req/min | None |
| **Craiyon** | Image generation (secondary) | ~2 req/min | None |
| **HuggingFace SDXL** | Image generation (tertiary) | ~10 req/hr anonymous | None |
| **Playground AI** | Image generation (browser fallback) | 500 img/day free tier | Free account |
| **Microsoft edge-tts** | Narration TTS (primary) | Unlimited | None |
| **Google gTTS** | Narration TTS (fallback) | Unlimited | None |
| **Anthropic Claude** | Story script (optional) | Per your plan | `ANTHROPIC_API_KEY` |
| **FFmpeg** | Video assembly | Local — no limit | None |

### Strategy waterfall for image generation

```
Pollinations.ai  →  Craiyon  →  HuggingFace SDXL  →  Crawl4AI/Playground AI
(no auth, fast)     (no auth)    (no auth, slower)      (free account needed)
```

`web_image_generator.py` tries each strategy in order and stops at the first success.

---

## Output

| Path | Contents |
|------|----------|
| `~/infinite-video-pipeline/<Story_Title>.mp4` | Final video (ready to share) |
| `outputs/<timestamp>/story.json` | Full story script with scene details |
| `outputs/<timestamp>/images/` | Scene illustrations (.png) |
| `outputs/<timestamp>/audio/` | Narration clips (.mp3) |
| `outputs/<timestamp>/clips/` | Per-scene video segments (.mp4) |

---

## Infinite Image Loop

The standalone `web_image_generator.py` can run as an infinite image generation loop
(mirrors the original `image_generator.py` interface):

```bash
python web_image_generator.py
```

Images are saved to `outputs/` as `image_00000.png`, `image_00001.png`, …

---

## Crawl4AI / Playground AI Fallback

To enable the browser-automation fallback (Playground AI free tier — 500 img/day):

```bash
export PLAYGROUND_EMAIL=your@email.com
export PLAYGROUND_PASSWORD=yourpassword
```

This uses Crawl4AI v0.8.6 to log in and submit prompts via headless browser.
Only invoked if all three REST API strategies fail.

---

## Files

| File | Purpose |
|------|---------|
| `free_pipeline.py` | **Main pipeline** — story → images → TTS → video (all free) |
| `web_image_generator.py` | Multi-strategy free image generator |
| `children_pipeline.py` | Legacy pipeline (requires OPENAI + ElevenLabs API keys) |
| `image_generator.py` | Legacy Stable Diffusion stub |
| `video_generator.py` | Legacy FFmpeg batch converter |

---

## Troubleshooting

**`ffprobe` not found** — install FFmpeg: `brew install ffmpeg`

**All image strategies fail** — check internet connectivity; Pollinations.ai is the
most reliable. HuggingFace 503s are normal (model cold-start); it retries automatically.

**No audio in video** — install TTS: `pip install edge-tts gtts`

**Playground AI fallback not triggering** — set `PLAYGROUND_EMAIL` / `PLAYGROUND_PASSWORD`
