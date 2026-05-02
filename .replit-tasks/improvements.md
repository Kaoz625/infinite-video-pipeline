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
2. **Add Open-Higgsfield-AI integration** — Clone and integrate https://github.com/Anil-matcha/Open-Higgsfield-AI which provides access to 200+ video generation models. Create a new module `higgsfield_generator.py` that wraps the Open-Higgsfield-AI client. Support at minimum: text-to-video, image-to-video, and video-to-video modes. Add `higgsfield` as a provider option alongside existing providers.
3. **Add batch processing queue** — Create `batch_processor.py` with a simple file-based queue system. Queue format: JSON files in `queue/pending/`. Processor reads each job, runs the appropriate generator, moves completed jobs to `queue/done/` with output paths. Add a `run_batch.py` CLI: `python run_batch.py --jobs queue/pending/` that processes all queued jobs and reports results.
4. **Improve output quality** — Add a quality control layer: after each generated image/video, use Claude Vision (claude-sonnet-4-6) to score the output quality (1-10) and describe any issues. If score < 6, automatically retry with adjusted parameters (higher steps, different seed). Save quality scores to `outputs/quality_log.json`.
5. **Add unified CLI** — Create `main.py` (if it doesn't exist or is incomplete) as the single entry point: `python main.py --type image --prompt "..." --provider higgsfield` or `--provider free`. Support: `--type image|video`, `--prompt TEXT`, `--provider free|higgsfield|web`, `--output-dir PATH`, `--batch FILE`.
6. **Update requirements.txt** — Add any new dependencies needed for Open-Higgsfield-AI integration. Pin all versions. Add a `setup.sh` script that does `pip install -r requirements.txt` and any additional setup steps.
7. **Add output organization** — Organize outputs/ directory: `outputs/images/YYYY-MM-DD/`, `outputs/videos/YYYY-MM-DD/`. Rename output files with timestamp + prompt slug (first 30 chars, sanitized). Add a simple `outputs/index.json` that lists all generated files with metadata.

## Do Not Touch
- outputs/ directory contents (existing generated files)
- __pycache__/ (auto-generated)

## Definition of Done
- [ ] AUDIT.md written with current state findings
- [ ] Open-Higgsfield-AI integrated and working
- [ ] Batch processing queue works end-to-end
- [ ] Unified CLI (`python main.py --help`) works
- [ ] No Python import errors on startup
- [ ] Pushed to main with "replit: " commit prefix
