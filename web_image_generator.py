"""
web_image_generator.py — Free Web-Based AI Image Generator
===========================================================
Replaces the Stable Diffusion subprocess approach with three
free, no-GPU, no-paid-API strategies tried in order:

  1. Pollinations.ai  — free REST API, no auth, ~5 req/min guideline
  2. Craiyon          — free public API, no auth, ~2 req/min guideline
  3. HuggingFace      — free anonymous inference (SDXL), ~10 req/hr
  4. Crawl4AI         — browser-automation fallback for Playground AI

Rate-limit targets are conservative estimates; none require an account.
"""

import os
import random
import time
import urllib.parse
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

OUTPUT_DIR = Path.home() / "infinite-video-pipeline" / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_WIDTH = 1024
DEFAULT_HEIGHT = 576

POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}"
CRAIYON_URL = "https://api.craiyon.com/v3"
HF_SDXL_URL = (
    "https://api-inference.huggingface.co/models/"
    "stabilityai/stable-diffusion-xl-base-1.0"
)
PLAYGROUND_URL = "https://playground.com/create"  # Crawl4AI fallback

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# ---------------------------------------------------------------------------
# Strategy 1: Pollinations.ai
# ---------------------------------------------------------------------------

def _pollinations(prompt: str, output_path: Path, width: int, height: int) -> bool:
    """
    Pollinations.ai — completely free, no auth required.
    Endpoint: https://image.pollinations.ai/prompt/{encoded_prompt}
    Rate limit: ~5 requests/min (unofficial guideline).
    """
    encoded = urllib.parse.quote(prompt)
    seed = random.randint(1, 99_999)
    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width={width}&height={height}&nologo=true&seed={seed}"
    )
    try:
        resp = requests.get(url, headers=HEADERS, timeout=90)
        ct = resp.headers.get("content-type", "")
        if resp.status_code == 200 and ct.startswith("image/"):
            output_path.write_bytes(resp.content)
            return True
        print(f"[Pollinations] HTTP {resp.status_code}")
    except Exception as exc:
        print(f"[Pollinations] Error: {exc}")
    return False


# ---------------------------------------------------------------------------
# Strategy 2: Craiyon
# ---------------------------------------------------------------------------

def _craiyon(prompt: str, output_path: Path) -> bool:
    """
    Craiyon (formerly DALL-E mini) — free public REST API, no auth.
    Returns 9 base64-encoded images; we save the first one.
    Rate limit: ~2 requests/min (unofficial guideline).
    """
    import base64

    payload = {
        "prompt": prompt,
        "negative_prompt": "",
        "model": "art",          # "art", "drawing", "photo", "none"
    }
    try:
        resp = requests.post(
            CRAIYON_URL,
            json=payload,
            headers={**HEADERS, "Content-Type": "application/json"},
            timeout=120,
        )
        if resp.status_code == 200:
            images = resp.json().get("images", [])
            if images:
                output_path.write_bytes(base64.b64decode(images[0]))
                return True
        print(f"[Craiyon] HTTP {resp.status_code}: {resp.text[:200]}")
    except Exception as exc:
        print(f"[Craiyon] Error: {exc}")
    return False


# ---------------------------------------------------------------------------
# Strategy 3: HuggingFace anonymous inference
# ---------------------------------------------------------------------------

def _huggingface(prompt: str, output_path: Path, retries: int = 2) -> bool:
    """
    HuggingFace Inference API (anonymous) — free, rate-limited.
    Model: stabilityai/stable-diffusion-xl-base-1.0
    Rate limit: ~10 requests/hr anonymous (unofficial guideline).
    Returns 503 with estimated_time when model is loading.
    """
    for attempt in range(retries + 1):
        try:
            resp = requests.post(
                HF_SDXL_URL,
                json={"inputs": prompt},
                headers={"Content-Type": "application/json"},
                timeout=120,
            )
            if resp.status_code == 200:
                output_path.write_bytes(resp.content)
                return True
            if resp.status_code == 503:
                wait = resp.json().get("estimated_time", 20)
                wait = min(float(wait), 60)
                print(f"[HuggingFace] Model loading, waiting {wait:.0f}s…")
                time.sleep(wait)
                continue
            print(f"[HuggingFace] HTTP {resp.status_code}: {resp.text[:200]}")
        except Exception as exc:
            print(f"[HuggingFace] Error: {exc}")
        if attempt < retries:
            time.sleep(5)
    return False


# ---------------------------------------------------------------------------
# Strategy 4: Crawl4AI browser automation (Playground AI)
# ---------------------------------------------------------------------------

def _crawl4ai_playground(prompt: str, output_path: Path) -> bool:
    """
    Crawl4AI browser-automation fallback targeting Playground AI free tier.
    Playground AI allows ~500 free images/day without a paid plan.
    Requires a free account login; set env vars PLAYGROUND_EMAIL / PLAYGROUND_PASSWORD.
    Rate limit: ~500 images/day free tier.
    """
    email = os.environ.get("PLAYGROUND_EMAIL")
    password = os.environ.get("PLAYGROUND_PASSWORD")
    if not email or not password:
        print(
            "[Crawl4AI] Skipping Playground AI: "
            "set PLAYGROUND_EMAIL and PLAYGROUND_PASSWORD to enable."
        )
        return False

    try:
        import asyncio
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

        async def _run() -> bool:
            browser_cfg = BrowserConfig(headless=True, verbose=False)
            run_cfg = CrawlerRunConfig(wait_until="networkidle", page_timeout=60_000)
            async with AsyncWebCrawler(config=browser_cfg) as crawler:
                # Navigate and log in
                await crawler.arun(
                    url="https://playground.com/login",
                    config=run_cfg,
                )
                page = crawler.browser_context.pages[-1]
                await page.fill('input[name="email"]', email)
                await page.fill('input[name="password"]', password)
                await page.click('button[type="submit"]')
                await page.wait_for_load_state("networkidle")

                # Navigate to create page and submit prompt
                await page.goto(PLAYGROUND_URL, wait_until="networkidle")
                await page.fill('textarea[placeholder*="prompt" i]', prompt)
                await page.click('button:has-text("Generate")')

                # Wait for an image to appear (up to 60 s)
                locator = page.locator("img[src*='cdn']").first
                await locator.wait_for(timeout=60_000)
                src = await locator.get_attribute("src")

                if src:
                    img_resp = requests.get(src, timeout=30)
                    if img_resp.status_code == 200:
                        output_path.write_bytes(img_resp.content)
                        return True
            return False

        return asyncio.run(_run())
    except Exception as exc:
        print(f"[Crawl4AI] Error: {exc}")
        return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_image(
    prompt: str,
    output_path: str | Path | None = None,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    counter: int | None = None,
) -> Path | None:
    """
    Generate one image for *prompt* and save it to *output_path*.

    Tries strategies in order:
      Pollinations.ai → Craiyon → HuggingFace SDXL → Crawl4AI (Playground)

    Returns the output Path on success, None on total failure.
    """
    if output_path is None:
        idx = counter if counter is not None else int(time.time())
        output_path = OUTPUT_DIR / f"image_{idx:05d}.png"
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[Generator] Prompt: '{prompt[:60]}…'")

    strategies = [
        ("Pollinations.ai", lambda: _pollinations(prompt, output_path, width, height)),
        ("Craiyon",         lambda: _craiyon(prompt, output_path)),
        ("HuggingFace SDXL",lambda: _huggingface(prompt, output_path)),
        ("Crawl4AI/Playground", lambda: _crawl4ai_playground(prompt, output_path)),
    ]

    for name, fn in strategies:
        print(f"[Generator] Trying {name}…")
        if fn():
            size_kb = output_path.stat().st_size // 1024
            print(f"[Generator] ✓ {name} → {output_path.name} ({size_kb} KB)")
            return output_path
        time.sleep(2)  # brief pause before next strategy

    print(f"[Generator] ✗ All strategies failed for prompt: {prompt[:60]}")
    return None


# ---------------------------------------------------------------------------
# Infinite generation loop (mirrors original image_generator.py interface)
# ---------------------------------------------------------------------------

PROMPTS = [
    "A beautiful serene landscape, ultra-realistic, golden hour",
    "A futuristic cityscape at night, vibrant neon colors",
    "A cyberpunk character artwork, intricate detail, concept art",
    "Pixar-style illustration of a friendly dog on an adventure",
    "Fantasy castle on a hill during sunset, vivid and breathtaking",
    "Underwater coral reef teeming with colorful fish, 8k",
    "Ancient library filled with glowing magical books",
    "Astronaut floating above a pastel alien planet",
]


def main():
    print("[Pipeline] Starting infinite web-based image generation…")
    counter = 0
    while True:
        prompt = random.choice(PROMPTS)
        result = generate_image(prompt, counter=counter)
        if result:
            counter += 1
        # Polite delay between requests (~12 s keeps us under Pollinations guideline)
        time.sleep(12)


if __name__ == "__main__":
    main()
