# Replit Agent Task Spec

## Instructions for Replit Agent
You are building/improving this project. Read this file carefully before touching any code.
Commit all changes with prefix "replit: " and push to main when done.

## Stack Rules (non-negotiable)
- Static → Cloudflare Pages (never Vercel)
- DB → Supabase self-hosted Docker (never cloud Supabase)
- Auth → NextAuth.js (free, not Auth0/Clerk)
- AI → Claude Sonnet 4.6 via Anthropic API (model: claude-sonnet-4-6)
- Payments (adult) → CCBill or Segpay only

## Improvements To Make
1. **Audit current state** — Read all pipeline scripts (free_pipeline.py, children_pipeline.py, image_generator.py, video_generator.py, web_image_generator.py) and requirements.txt. Document which APIs are currently used, what works, and what is broken/incomplete. Add a `AUDIT.md` file with findings.

2. **Add Open-Generative-AI integration** — Integrate https://github.com/Anil-matcha/Open-Generative-AI which provides 200+ image/video/lip-sync models via Muapi.ai API (NOT Open-Higgsfield-AI — that repo is dead). Create `muapi_generator.py` using `requests` to call Muapi.ai endpoints. Default image model: `flux-schnell`. Default video model: `wan-i2v` (image-to-video). Env var: `MUAPI_API_KEY` (user supplies from muapi.ai). If key not set, fall back to free providers (Pollinations.ai → Craiyon → HuggingFace SDXL). Add `muapi` as a provider option in the unified CLI.

3. **Add batch processing queue** — Create `batch_processor.py` with a simple file-based queue system. Queue format: JSON files in `queue/pending/`. Processor reads each job, runs the appropriate generator, moves completed jobs to `queue/done/` with output paths. Add a `run_batch.py` CLI: `python run_batch.py --jobs queue/pending/`.

4. **Improve output quality** — After each generated image/video, use Claude Vision (claude-sonnet-4-6) to score quality (1-10). If score < 6, automatically retry with adjusted parameters. Save scores to `outputs/quality_log.json`.

5. **Add unified CLI** — `main.py` as single entry point: `python main.py --type image --prompt "..." --provider muapi` or `--provider free`. Support: `--type image|video`, `--prompt TEXT`, `--provider free|muapi|web`, `--output-dir PATH`, `--batch FILE`.

6. **Update requirements.txt** — Add `anthropic` for quality scoring. Pin all versions. Add `setup.sh`.

7. **Add output organization** — `outputs/images/YYYY-MM-DD/`, `outputs/videos/YYYY-MM-DD/`. Timestamp + prompt slug filenames. `outputs/index.json` manifest.

## Do Not Touch
- outputs/ directory contents (existing generated files)
- __pycache__/ (auto-generated)

## Definition of Done
- [ ] AUDIT.md written
- [ ] Muapi.ai / Open-Generative-AI integrated with free fallback
- [ ] Batch processing queue works end-to-end
- [ ] Unified CLI (`python main.py --help`) works
- [ ] No Python import errors on startup
- [ ] Pushed to main with "replit: " prefix
