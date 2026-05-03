# Replit Agent Task Spec

## Instructions for Replit Agent
You are building/improving this project. Read this file carefully before touching any code.
Commit all changes with prefix "replit: " and push to main when done.

## Stack Rules (non-negotiable)
- Static → Cloudflare Pages (never Vercel)
- DB → Supabase self-hosted Docker (never cloud Supabase)
- Auth → NextAuth.js (free, not Auth0/Clerk)
- AI → Claude Sonnet 4.6 via Anthropic API (model: claude-sonnet-4-6)
- Payments (adult) → CCBill/Segpay only

## Project Overview
Automated AI video and image generation pipeline producing infinite content streams. Core scripts exist — needs integration, batch processing, and quality improvements.

## Current State
Files present: free_pipeline.py, children_pipeline.py, image_generator.py, video_generator.py, web_image_generator.py, requirements.txt, outputs/

## Tasks

### 1. Add Open-Higgsfield-AI integration
- Install higgsfield package (pip)
- Create higgsfield_generator.py with a generate_video(prompt, model="cosmos-1.0") function
- Wire it into video_generator.py as a provider option alongside existing ones
- Expose 5 top Higgsfield models as selectable options

### 2. Batch processing queue
- Create batch_queue.py — accepts a list of prompts from a JSON file (batch_input.json)
- Processes them sequentially, saves outputs to outputs/batch_{timestamp}/
- Logs progress to batch_log.txt
- CLI: python batch_queue.py --input batch_input.json --pipeline free|children

### 3. Quality control layer
- Create quality_check.py — takes an output image/video path, runs basic checks:
  - Image: resolution >= 512x512, file size > 10KB
  - Video: duration > 1s, has valid codec
- Returns pass/fail + reason
- Integrate into both pipelines: auto-retry once on fail

### 4. Unified CLI entrypoint
- Create main.py if not present
- Commands: generate, batch, check
- Example: python main.py generate --prompt "sunset over NYC" --type video --pipeline free

### 5. Update requirements.txt
- Add any new dependencies from tasks above
- Pin versions

### 6. Add README.md
- Document setup, env vars needed, and example commands for each pipeline
