# Replit Agent Task: infinite-video-pipeline

## Goal
Extend the existing free-tier video pipeline (story → images → narration → MP4) by integrating Open-Higgsfield-AI's library of 200+ video generation models, adding an interactive model selector, and building a batch queue system so multiple video jobs can run concurrently.

## Tasks
1. **Audit existing code**: read free_pipeline.py, children_pipeline.py, video_generator.py, image_generator.py, web_image_generator.py — understand the current architecture, what APIs are called, and how FFmpeg is used; document findings in a comment block at the top of the new main entry point
2. **Open-Higgsfield-AI integration**: create `higgsfield_client.py` that wraps the Higgsfield AI API (https://higgsfield.ai/api — use `HIGGSFIELD_API_KEY` from env); implement:
   - `list_models()` → returns list of {model_id, name, category, description, supported_inputs}
   - `generate_video(model_id, prompt, image_path=None, duration=5, aspect_ratio="16:9")` → returns job_id
   - `get_job_status(job_id)` → returns {status, progress, output_url}
   - `download_result(job_id, output_path)` → downloads finished video
3. **Model selector UI** (`model_selector.py`): a terminal UI (use `rich` library — already in requirements or add it) that displays available Higgsfield models in a paginated table grouped by category (Text-to-Video, Image-to-Video, Style Transfer, etc.); user selects a model with arrow keys or number input; selected model persists to `.selected_model` config file
4. **Batch queue system** (`batch_queue.py`):
   - `BatchQueue` class using Python `threading.ThreadPoolExecutor` (max 3 workers)
   - `add_job(prompt, model_id, output_name)` → adds to queue, returns job_id
   - `run_all()` → processes queue concurrently, shows rich progress bar per job
   - `get_results()` → returns list of {job_id, status, output_path, error}
   - Jobs that fail (API error, timeout) are retried once, then marked FAILED
5. **Unified CLI** (`main.py`): replace the current multi-script approach with a single CLI:
   ```
   python main.py --prompt "A dog running through NYC" --model higgsfield --model-id wan-t2v-1.3b --output out.mp4
   python main.py --batch jobs.csv --workers 3
   python main.py --select-model   # launches model selector TUI
   python main.py --free --prompt "..."  # falls back to original free pipeline
   ```
6. **Batch CSV format**: document and support `jobs.csv` with columns: prompt, model_id, output_name, duration, aspect_ratio; include a `jobs_example.csv` in the repo
7. **Progress reporting**: for batch jobs, render a rich `Live` display with a table showing: Job ID, Model, Status (queued/running/done/failed), Progress %, Output File; update every 2 seconds via polling
8. **Free pipeline preservation**: the existing free pipeline (Pollinations.ai + edge-tts + FFmpeg) must remain fully functional as a fallback when no `HIGGSFIELD_API_KEY` is set; import and call it from `main.py --free`
9. **Update requirements.txt**: add `rich`, `higgsfield` (or `requests` if no official SDK), `python-dotenv`; pin versions
10. **Update README**: document all CLI commands, env vars (`HIGGSFIELD_API_KEY`, `ANTHROPIC_API_KEY`), batch CSV format, and how to run the model selector

## Tech Stack
- Python 3.10+ (existing)
- Open-Higgsfield-AI API (HIGGSFIELD_API_KEY)
- rich library for TUI and progress bars
- threading.ThreadPoolExecutor for batch queue
- FFmpeg (existing dependency)
- python-dotenv for env var loading
- Existing free stack: Pollinations.ai, edge-tts, gTTS

## Deploy Target
Coolify (backend Python service, runs as a long-lived process or on-demand via CLI). Never Vercel.

## Done When
- [ ] `higgsfield_client.py` connects to Higgsfield API and list_models() returns model list
- [ ] `model_selector.py` renders a rich TUI with paginated model table and selection
- [ ] `batch_queue.py` processes at least 3 concurrent jobs with rich progress display
- [ ] `main.py` CLI supports `--prompt`, `--model`, `--batch`, `--select-model`, `--free` flags
- [ ] `jobs_example.csv` documents the batch input format
- [ ] Free pipeline still works with `--free` flag (no API key required)
- [ ] `requirements.txt` updated with all new dependencies
- [ ] README documents all env vars and CLI usage
