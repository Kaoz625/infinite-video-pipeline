# infinite-video-pipeline — Replit Import Notes

## What This Is
End-to-end free AI video pipeline: story prompt → illustrated video with narration.
No local GPU. No paid API keys required (Claude optional for richer stories).

## Stack
- Story: Claude Haiku (optional) or built-in template engine
- Images: Pollinations.ai → Craiyon → HuggingFace SDXL (free, auto-fallback)
- TTS: edge-tts (Microsoft) → gTTS (Google) fallback
- Video: FFmpeg (local)

## Current State (2026-05-02)
- crawl4ai: 0.8.6 (already at latest — no update needed)
- requirements.txt: up to date
- Open-Higgsfield-AI integration: **REPLACED** — use Open-Generative-AI instead (see below)

## Improvements Roadmap

### Task 1 — Integrate Open-Generative-AI as primary image/video source (HIGH PRIORITY)
Repo: https://github.com/Anil-matcha/Open-Generative-AI
What it is: Unified interface for 200+ AI image/video/lip-sync models via Muapi.ai API.
Covers: Image Studio, Video Studio, Lip Sync Studio, Cinema Studio.

Integration steps for Replit agent:
1. Add `muapi` as an HTTP client target — use `requests` to hit Muapi.ai endpoints
2. Add `MUAPI_API_KEY` to `.env` (user supplies their own key from muapi.ai)
3. In `free_pipeline.py`, add a `MuapiImageSource` class:
   - POST to `https://api.muapi.ai/v1/images/generate` with model + prompt
   - Use model `flux-schnell` as default (fast, high quality)
   - Fall back to existing Pollinations.ai → Craiyon chain if MUAPI_API_KEY not set
4. Add a `MuapiVideoSource` class for video frames:
   - POST to `https://api.muapi.ai/v1/videos/generate`
   - Use model `wan-i2v` (image-to-video) to animate generated frames
5. Update README with: "Set MUAPI_API_KEY for 200+ model access via muapi.ai"

- [ ] Replace Open-Higgsfield (404) with fal.ai free tier as secondary fallback
  - fal.ai/models/fal-ai/flux/schnell — free, fast FLUX image generation
  - pip install fal-client; env var: FAL_KEY
- [ ] Add Seedance 2.0 multishot workflow (storyboard → scene-by-scene video)
  - Reference: github.com/sarpstar/seedance2.0-rehber
- [ ] Add Replicate free tier (SDXL-turbo) as image fallback
- [ ] Add subtitle/caption overlay using FFmpeg drawtext filter
- [ ] Add background music via freesound.org API (free with key)

## Quick Start
```bash
pip install -r requirements.txt
python free_pipeline.py "A robot who learns to paint"
```
