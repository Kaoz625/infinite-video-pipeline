> **REPLIT AGENT — START BUILDING IMMEDIATELY**
> Read this entire file, then start on Task 1 right now. Do not ask questions. Do not wait for input. Build everything in the task list, commit each completed task with prefix `replit: `, and push to main. When all tasks are done, run the project and verify it works.


# Infinite Video Pipeline — Replit Agent Build Spec

## Instructions for Replit Agent
You are building/improving this project. Read this file carefully before touching any code.
Commit all changes with prefix "replit: " and push to main when done.

## Stack Rules (non-negotiable)
- Static → Cloudflare Pages (never Vercel)
- DB → Supabase self-hosted Docker (never cloud Supabase)
- Auth → NextAuth.js (free, not Auth0/Clerk)
- AI → Claude Sonnet 4.6 via Anthropic API (model: claude-sonnet-4-6)
- Payments (adult) → CCBill/Segpay only

## Ethics Rules (REQUIRED — do not skip)
- CSAM absolute ban: add `safety_check(prompt)` that raises ValueError on any minor-related content
- Synthetic watermark: embed `{"synthetic": true, "generator": "infinite-video-pipeline"}` in output metadata
- NY AI Transparency Act (effective June 9, 2026): outputs used in ads need "AI-generated" disclosure
- Adult content requires explicit `--adult` flag — default is safe mode

## Project Overview
Automated AI video and image generation pipeline producing infinite content streams. Core scripts exist — needs multi-provider uncensored model support, batch processing, and quality improvements.

## Current State
Files present: free_pipeline.py, children_pipeline.py, image_generator.py, video_generator.py, web_image_generator.py, requirements.txt, outputs/

## Tasks

### 1. safety_check.py (build this FIRST)
```python
BLOCKED_TERMS = ["child", "minor", "underage", "teen", "kid", "young girl", "young boy", "loli", "shota", "preteen"]

def safety_check(prompt: str) -> None:
    lower = prompt.lower()
    for term in BLOCKED_TERMS:
        if term in lower:
            raise ValueError(f"Blocked: prohibited term '{term}'")
```
Call `safety_check(prompt)` at the top of every generation function.

### 2. Multi-provider video generation
Update `video_generator.py` with `--provider` flag:

**fal.ai** (`FAL_KEY` env var):
- `fal-ai/kling-video/v1.6/standard/text-to-video`
- `fal-ai/wan-t2v` (best free option)
- `fal-ai/minimax-video/video-01`

**Replicate** (`REPLICATE_API_TOKEN`):
- `anotherjesse/zeroscope-v2-xl`
- `lucataco/animate-diff`

**RunPod** (`RUNPOD_API_KEY` + `RUNPOD_ENDPOINT_ID`):
- Submit job → poll → download output

Adult flag: `--adult` disables provider-side safety filters where supported.

### 3. Multi-provider image generation
Update `image_generator.py` with same provider routing:

**fal.ai**: `flux-dev`, `flux-pro`, `flux-schnell` (fastest/free), `fast-sdxl`
**Replicate**: `realistic-vision-v5`, `dreamshaper-xl-turbo`, `juggernaut-xl-v9`
**Local A1111** (`LOCAL_SD_URL` env var, default `http://localhost:7860`): POST to `/sdapi/v1/txt2img`

Adult flag: pass `safety_tolerance="5"` to fal, `negative_prompt=""` to local SD.

### 4. Prompt enhancement via Claude
Create `prompt_enhancer.py`:
- Calls claude-sonnet-4-6 to expand short prompts into rich generation prompts
- System: "You are a professional AI director. Expand into a detailed visual prompt with lighting, style, composition, mood. Never include content involving minors."
- Cache results to `prompt_cache.json`
- `enhance(short_prompt, style="cinematic|photorealistic|anime", adult=False) -> str`

### 5. Batch processing queue
Create `batch_queue.py`:
- Input: `batch_input.json` — `[{"prompt":"...", "type":"video|image", "provider":"fal", "adult":false}]`
- Output: `outputs/batch_{timestamp}/`
- Log: `batch_log.txt`
- CLI: `python batch_queue.py --input batch_input.json`

### 6. Quality control
Create `quality_check.py`:
- Image: resolution >= 512×512, file size > 10KB
- Video: duration > 1s, valid codec (use `ffprobe`)
- Returns `(pass: bool, reason: str)`
- Auto-retry once on fail in all pipelines

### 7. Unified CLI
Update or create `main.py`:
```
python main.py generate --prompt "sunset NYC" --type video --provider fal
python main.py generate --prompt "portrait" --type image --provider replicate --adult
python main.py batch --input batch_input.json
python main.py infinite --type image --provider fal --delay 5
python main.py enhance --prompt "city at night"
```

### 8. Update requirements.txt
```
anthropic>=0.39.0
fal-client>=0.5.0
replicate>=0.25.0
Pillow>=10.4.0
requests>=2.31.0
python-dotenv>=1.0.0
tqdm>=4.66.0
```

### 9. .env.example
```
ANTHROPIC_API_KEY=
FAL_KEY=
REPLICATE_API_TOKEN=
RUNPOD_API_KEY=
RUNPOD_ENDPOINT_ID=
LOCAL_SD_URL=http://localhost:7860
```

### 10. Update README.md
Document all providers, flags, adult mode usage, ethics rules, and example commands.

## Environment Variables (add as Replit Secrets)
- `ANTHROPIC_API_KEY` — prompt enhancement
- `FAL_KEY` — primary provider (free tier at fal.ai)
- `REPLICATE_API_TOKEN` — alternative provider
- `RUNPOD_API_KEY` + `RUNPOD_ENDPOINT_ID` — custom models