"""
free_pipeline.py — Children's Story Video Pipeline (100% Free Services)
========================================================================
Replaces children_pipeline.py's paid services with free alternatives:

  Story generation : Anthropic Claude (optional, uses ANTHROPIC_API_KEY if set)
                     Falls back to a built-in story template engine — no key needed.
  Image generation : web_image_generator.py (Pollinations → Craiyon → HuggingFace)
  Text-to-speech   : edge-tts (Microsoft Edge TTS, free, no key)
                     Falls back to gtts (Google TTS, free, no key)
  Video assembly   : FFmpeg (local, free)

Usage
-----
    # Optional: set ANTHROPIC_API_KEY for richer stories
    python free_pipeline.py "A bunny who finds a magic garden"
    python free_pipeline.py                          # uses a random default prompt

Output
------
    ~/infinite-video-pipeline/<Story_Title>.mp4
    outputs/<timestamp>/story.json
    outputs/<timestamp>/images/
    outputs/<timestamp>/audio/
    outputs/<timestamp>/clips/
"""

import asyncio
import json
import os
import random
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from web_image_generator import generate_image

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE_DIR   = Path.home() / "infinite-video-pipeline"
VIDEO_W    = 1024
VIDEO_H    = 576
SCENE_DUR  = 6        # seconds each scene is shown in the final video
FRAMERATE  = 24

DEFAULT_PROMPTS = [
    "A bunny who discovers a magical garden",
    "A little elephant who learns to paint",
    "A baby dragon afraid of fire who finds courage",
    "A small robot who wants to make friends",
    "A sleepy bear who dreams of flying",
]

# ---------------------------------------------------------------------------
# Story generation (Claude if key present, else template engine)
# ---------------------------------------------------------------------------

STORY_TEMPLATE = {
    "title": "{subject} — A Magical Adventure",
    "scenes": [
        {
            "scene_number": 1,
            "narration": "Once upon a time, {subject_lower} set off on a grand adventure.",
            "image_prompt": "{subject_lower}, storybook illustration, magical setting, warm colors",
        },
        {
            "scene_number": 2,
            "narration": "Along the way, they discovered something truly wonderful.",
            "image_prompt": "magical discovery, glowing light, wonder, children's book art style",
        },
        {
            "scene_number": 3,
            "narration": "It was scary at first, but {subject_lower} was very brave.",
            "image_prompt": "{subject_lower}, brave expression, facing challenge, soft watercolor art",
        },
        {
            "scene_number": 4,
            "narration": "With a little help from a new friend, everything became possible.",
            "image_prompt": "two friendly characters helping each other, cheerful, children's book",
        },
        {
            "scene_number": 5,
            "narration": "And so, {subject_lower} returned home, full of joy and new memories.",
            "image_prompt": "{subject_lower}, happy ending, cozy home, golden sunset, storybook",
        },
    ],
}


def _template_story(user_prompt: str) -> dict:
    subject = user_prompt.strip().capitalize()
    subject_lower = user_prompt.strip().lower()
    story = json.loads(json.dumps(STORY_TEMPLATE))  # deep copy
    story["title"] = story["title"].format(subject=subject)
    for scene in story["scenes"]:
        scene["narration"] = scene["narration"].format(
            subject_lower=subject_lower
        )
        scene["image_prompt"] = scene["image_prompt"].format(
            subject_lower=subject_lower
        )
    return story


def _claude_story(user_prompt: str) -> dict | None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        system = (
            "You are a children's storybook author. "
            "Return ONLY valid JSON matching this schema — no prose before or after:\n"
            '{"title": "string", "scenes": ['
            '{"scene_number": int, "narration": "string (1-2 sentences)", '
            '"image_prompt": "string (Stable Diffusion style, child-friendly)"}'
            "]}. "
            "Create exactly 5 scenes. Keep narration simple and joyful (ages 3-8)."
        )
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = msg.content[0].text.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)
    except Exception as exc:
        print(f"[Story] Claude error: {exc}. Using template fallback.")
        return None


def generate_story(user_prompt: str) -> dict:
    print(f"[Story] Generating story for: '{user_prompt}'")
    story = _claude_story(user_prompt)
    if not story:
        story = _template_story(user_prompt)
        print("[Story] Using built-in template engine (no ANTHROPIC_API_KEY).")
    print(f"[Story] Title: {story['title']} ({len(story['scenes'])} scenes)")
    return story


# ---------------------------------------------------------------------------
# TTS: edge-tts → gtts fallback
# ---------------------------------------------------------------------------

async def _edge_tts(text: str, output_path: Path) -> bool:
    """Microsoft Edge TTS — free, high quality, no key required."""
    try:
        import edge_tts

        voice = "en-US-JennyNeural"  # warm, child-friendly
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(output_path))
        return True
    except ImportError:
        print("[TTS] edge-tts not installed. Run: pip install edge-tts")
    except Exception as exc:
        print(f"[TTS] edge-tts error: {exc}")
    return False


def _gtts(text: str, output_path: Path) -> bool:
    """Google TTS — free, no key required."""
    try:
        from gtts import gTTS

        tts = gTTS(text=text, lang="en", slow=False)
        tts.save(str(output_path))
        return True
    except ImportError:
        print("[TTS] gtts not installed. Run: pip install gtts")
    except Exception as exc:
        print(f"[TTS] gtts error: {exc}")
    return False


def generate_narration(text: str, output_path: Path) -> bool:
    """Try edge-tts then gtts; return True if audio was saved."""
    if asyncio.run(_edge_tts(text, output_path)):
        print(f"[TTS] ✓ edge-tts → {output_path.name}")
        return True
    if _gtts(text, output_path):
        print(f"[TTS] ✓ gtts → {output_path.name}")
        return True
    print(f"[TTS] ✗ No TTS available for scene. Proceeding without audio.")
    return False


# ---------------------------------------------------------------------------
# FFmpeg helpers
# ---------------------------------------------------------------------------

def _run(cmd: list[str], label: str) -> bool:
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as exc:
        print(f"[FFmpeg/{label}] Error: {exc.stderr.decode()[:300]}")
        return False


def image_to_clip(image_path: Path, audio_path: Path | None, clip_path: Path) -> bool:
    """Combine one image + optional audio into a video clip."""
    audio_exists = audio_path and audio_path.exists()

    # Build base clip (image looped for SCENE_DUR seconds)
    base_clip = clip_path.with_suffix(".silent.mp4")
    ok = _run(
        [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(image_path),
            "-t", str(SCENE_DUR),
            "-vf", f"scale={VIDEO_W}:{VIDEO_H}:force_original_aspect_ratio=decrease,"
                   f"pad={VIDEO_W}:{VIDEO_H}:(ow-iw)/2:(oh-ih)/2,setsar=1",
            "-c:v", "libx264", "-r", str(FRAMERATE), "-pix_fmt", "yuv420p",
            "-tune", "stillimage",
            str(base_clip),
        ],
        "image→clip",
    )
    if not ok:
        return False

    if audio_exists:
        ok = _run(
            [
                "ffmpeg", "-y",
                "-i", str(base_clip),
                "-i", str(audio_path),
                "-c:v", "copy", "-c:a", "aac",
                "-shortest",
                str(clip_path),
            ],
            "add-audio",
        )
        base_clip.unlink(missing_ok=True)
        return ok
    else:
        base_clip.rename(clip_path)
        return True


def concat_clips(clip_paths: list[Path], output_path: Path) -> bool:
    """Concatenate scene clips into the final video."""
    list_file = output_path.parent / "concat_list.txt"
    list_file.write_text(
        "\n".join(f"file '{p}'" for p in clip_paths)
    )
    ok = _run(
        [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(list_file),
            "-c", "copy",
            str(output_path),
        ],
        "concat",
    )
    list_file.unlink(missing_ok=True)
    return ok


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_pipeline(user_prompt: str) -> Path | None:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir   = BASE_DIR / "outputs" / ts
    img_dir   = run_dir / "images"
    audio_dir = run_dir / "audio"
    clips_dir = run_dir / "clips"
    for d in (img_dir, audio_dir, clips_dir):
        d.mkdir(parents=True, exist_ok=True)

    # 1. Story
    story = generate_story(user_prompt)
    (run_dir / "story.json").write_text(json.dumps(story, indent=2))

    clip_paths: list[Path] = []

    for scene in story["scenes"]:
        n = scene["scene_number"]
        print(f"\n--- Scene {n}/{len(story['scenes'])} ---")

        # 2. Image
        img_path = img_dir / f"scene_{n:02d}.png"
        result = generate_image(
            prompt=scene["image_prompt"],
            output_path=img_path,
            width=VIDEO_W,
            height=VIDEO_H,
        )
        if not result:
            print(f"[Pipeline] Scene {n}: image generation failed, skipping.")
            continue

        # 3. Narration
        audio_path = audio_dir / f"scene_{n:02d}.mp3"
        generate_narration(scene["narration"], audio_path)

        # 4. Scene clip
        clip_path = clips_dir / f"clip_{n:02d}.mp4"
        if not image_to_clip(img_path, audio_path if audio_path.exists() else None, clip_path):
            print(f"[Pipeline] Scene {n}: FFmpeg clip failed, skipping.")
            continue

        clip_paths.append(clip_path)
        print(f"[Pipeline] Scene {n} done ✓")

    if not clip_paths:
        print("[Pipeline] No clips produced — aborting.")
        return None

    # 5. Concatenate
    safe_title = "".join(c if c.isalnum() or c in " _-" else "" for c in story["title"])
    safe_title = safe_title.strip().replace(" ", "_")
    final_path = BASE_DIR / f"{safe_title}.mp4"

    print(f"\n[Pipeline] Assembling final video → {final_path.name}")
    if not concat_clips(clip_paths, final_path):
        return None

    print(f"\n[Pipeline] ✅ Complete: {final_path}")
    print(f"           Story JSON: {run_dir / 'story.json'}")
    return final_path


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    prompt = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else ""
    if not prompt:
        prompt = random.choice(DEFAULT_PROMPTS)
        print(f"[Pipeline] No prompt supplied — using: '{prompt}'")
    run_pipeline(prompt)
