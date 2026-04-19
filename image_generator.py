"""
Image Generator: Infinite Image Generation Workflow
- Uses Stable Diffusion to generate images incrementally.
- Can randomize prompts for variety in outputs.
"""

import random
import os
import subprocess

# Configuration
output_dir = os.path.expanduser('~/infinite-video-pipeline/outputs')
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

prompts = [
    "A beautiful serene landscape, ultra-realistic, 8k resolution",
    "A futuristic cityscape at night, vibrant neon colors",
    "A cyberpunk character artwork, intricate detail, concept art",
    "Pixar-style illustration of a friendly dog and his adventures",
    "Fantasy castle on a hill during sunset, vivid and breathtaking"
]

def generate_image(output_path, prompt):
    try:
        print(f"[Generator] Generating Image: {output_path}")
        # Replace this command with your specific Stable Diffusion or generation tool call
        generation_command = f"python run_diffusion.py --output '{output_path}' --prompt '{prompt}'"
        subprocess.run(generation_command, shell=True, check=True)
    except subprocess.CalledProcessError as error:
        print(f"[Generator Error] {str(error)}")

def main():
    counter = 0
    while True:  # Infinite Loop
        random_prompt = random.choice(prompts)
        output_file = os.path.join(output_dir, f"image_{counter:05}.png")
        generate_image(output_file, random_prompt)
        counter += 1

if __name__ == "__main__":
    print("[Pipeline] Starting Infinite Image Generation...")
    main()
