# infinite-video-pipeline — Project Overview
**Owner:** Kaoz625 | **Stack:** Python, AI image/video generation APIs | **Status:** Basic pipeline scripts exist — needs Open-Higgsfield-AI integration, batch processing, and quality improvements

## What This Is
An automated AI video and image generation pipeline for creating infinite content streams. Uses multiple AI generation services to produce images and videos programmatically, with separate pipelines for free-tier and children-safe content generation.

## Current State
Core pipeline scripts exist: free_pipeline.py, children_pipeline.py, image_generator.py, video_generator.py, web_image_generator.py. Has requirements.txt and outputs directory. Missing: Open-Higgsfield-AI integration (200+ video models), batch processing queue, quality control layer.

## Tech Stack
- Python 3.10+
- Multiple AI generation APIs (see requirements.txt)
- File-based output pipeline
- Modular generator architecture
