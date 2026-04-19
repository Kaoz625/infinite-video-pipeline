#!/usr/bin/env python3
"""
Children's Video Pipeline - End-to-End AI Story & Video Generator

Flow: story prompt → LLM story/scenes → DALL-E 3 images → ElevenLabs TTS → FFmpeg MP4

Usage:
    python children_pipeline.py "A bunny who discovers a magical garden"
    python children_pipeline.py   # uses default prompt
"""

import os
import json
import sys
import subprocess
import datetime
import requests
import anthropic
import openai
from pathlib import Path

# ─── Config ───────────────────────────────────────────────────────────────────
PIPELINE_DIR = Path.home() / "infinite-video-pipeline"
OUTPUT_DIR = PIPELINE_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "")
ANTHROPIC_CLIENT = anthropic.Anthropic()
OPENAI_CLIENT = openai.OpenAI()

VIDEO_WIDTH = 1792
VIDEO_HEIGHT = 1024  # 16:9-ish widescreen

STORY_SYSTEM_PROMPT = """You are a children's book author. Create a short, engaging story for ages 3-8.
Return ONLY valid JSON — no markdown, no code fences — with this exact structure:
{
  "title": "Story Title",
  "scenes": [
    {
      "scene_number": 1,
      "narration": "1-3 simple sentences read aloud for this scene.",
      "image_prompt": "Detailed Pixar/Disney-style illustration prompt: bright colors, friendly characters, no scary elements, child-friendly"
    }
  ]
}
Create exactly 5 scenes. Keep narration warm, simple, and age-appropriate."""


# ─── Step 1: Story Generation ─────────────────────────────────────────────────
def generate_story(prompt: str) -> dict:
    print(f"\n📖  Generating story for: '{prompt}'")
    message = ANTHROPIC_CLIENT.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        system=STORY_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Write a children's story about: {prompt}"}],
    )
    text = message.content[0].text.strip()
    # Strip markdown code fences if model wraps in them
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0].strip()
    story = json.loads(text)
    print(f"    ✅ '{story['title']}' — {len(story['scenes'])} scenes")
    return story


# ─── Step 2: AI Image Generation (DALL-E 3) ───────────────────────────────────
def generate_image(image_prompt: str, output_path: Path) -> Path:
    print(f"    🎨  {output_path.name}")
    response = OPENAI_CLIENT.images.generate(
        model="dall-e-3",
        prompt=image_prompt,
        size="1792x1024",
        quality="standard",
        n=1,
    )
    image_url = response.data[0].url
    img_data = requests.get(image_url, timeout=60).content
    output_path.write_bytes(img_data)
    return output_path


def generate_all_images(story: dict, run_dir: Path) -> list:
    print(f"\n🎨  Generating {len(story['scenes'])} scene images...")
    images_dir = run_dir / "images"
    images_dir.mkdir(exist_ok=True)
    image_paths = []
    for scene in story["scenes"]:
        img_path = images_dir / f"scene_{scene['scene_number']:02d}.png"
        generate_image(scene["image_prompt"], img_path)
        image_paths.append(img_path)
    return image_paths


# ─── Step 3: Text-to-Speech Narration (ElevenLabs) ────────────────────────────
def generate_tts(text: str, output_path: Path) -> Path:
    print(f"    🎙️   {output_path.name}")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "model_id": "eleven_turbo_v2_5",
        "voice_settings": {"stability": 0.65, "similarity_boost": 0.75},
    }
    resp = requests.post(url, json=payload, headers=headers, timeout=60)
    resp.raise_for_status()
    output_path.write_bytes(resp.content)
    return output_path


def generate_all_narration(story: dict, run_dir: Path) -> list:
    print(f"\n🎙️   Generating narration for {len(story['scenes'])} scenes...")
    audio_dir = run_dir / "audio"
    audio_dir.mkdir(exist_ok=True)
    audio_paths = []
    for scene in story["scenes"]:
        audio_path = audio_dir / f"scene_{scene['scene_number']:02d}.mp3"
        generate_tts(scene["narration"], audio_path)
        audio_paths.append(audio_path)
    return audio_paths


# ─── Step 4: Video Assembly (FFmpeg) ──────────────────────────────────────────
def get_audio_duration(audio_path: Path) -> float:
    """Return audio duration in seconds using ffprobe."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio_path),
        ],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())


def create_scene_clip(image_path: Path, audio_path: Path, clip_path: Path) -> Path:
    """Combine one image + one audio segment into a short video clip."""
    duration = get_audio_duration(audio_path) + 0.5  # 0.5s tail padding
    vf = (
        f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,"
        f"pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=black"
    )
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(image_path),
        "-i", str(audio_path),
        "-c:v", "libx264", "-tune", "stillimage",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-t", str(duration),
        "-vf", vf,
        str(clip_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return clip_path


def concat_clips(clip_paths: list, output_path: Path) -> Path:
    """Concatenate all scene clips into the final video."""
    concat_file = output_path.parent / "concat_list.txt"
    concat_file.write_text("\n".join(f"file '{p}'" for p in clip_paths))
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy",
        str(output_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    concat_file.unlink()
    return output_path


def assemble_video(story: dict, image_paths: list, audio_paths: list, run_dir: Path) -> Path:
    print(f"\n🎬  Assembling {len(image_paths)} scene clips...")
    clips_dir = run_dir / "clips"
    clips_dir.mkdir(exist_ok=True)
    clip_paths = []
    for i, (img, audio) in enumerate(zip(image_paths, audio_paths), start=1):
        clip_path = clips_dir / f"clip_{i:02d}.mp4"
        print(f"    🎞️   Scene {i}: image + audio → {clip_path.name}")
        create_scene_clip(img, audio, clip_path)
        clip_paths.append(clip_path)

    safe_title = (
        "".join(c if c.isalnum() or c in " _-" else "" for c in story["title"])
        .strip()
        .replace(" ", "_")
    )
    final_path = PIPELINE_DIR / f"{safe_title}.mp4"
    print(f"    📼  Concatenating → {final_path.name}")
    concat_clips(clip_paths, final_path)
    return final_path


# ─── Main Orchestrator ────────────────────────────────────────────────────────
def run_pipeline(story_prompt: str) -> Path:
    """
    Full end-to-end pipeline:
      story prompt → story JSON → DALL-E 3 images → ElevenLabs TTS → FFmpeg MP4
    """
    run_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = OUTPUT_DIR / run_id
    run_dir.mkdir(parents=True)

    # 1. Story
    story = generate_story(story_prompt)

    # 2. Images
    image_paths = generate_all_images(story, run_dir)

    # 3. Narration
    audio_paths = generate_all_narration(story, run_dir)

    # 4. Video
    final_video = assemble_video(story, image_paths, audio_paths, run_dir)

    # Save metadata
    (run_dir / "story.json").write_text(json.dumps(story, indent=2))

    print(f"\n✅  Pipeline complete!")
    print(f"    📹  Video : {final_video}")
    print(f"    📁  Assets: {run_dir}")
    return final_video


if __name__ == "__main__":
    prompt = (
        " ".join(sys.argv[1:])
        if len(sys.argv) > 1
        else "A curious bunny who discovers a magical garden"
    )
    run_pipeline(prompt)
