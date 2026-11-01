"""Create the clay-guide image used before SF3D reconstruction.

This script runs in Colab's base Python environment, separately from SF3D's
Python 3.10 environment, so their dependencies and GPU memory do not overlap.
"""

from __future__ import annotations

import argparse
import gc
from pathlib import Path

import torch
from diffusers import ControlNetModel, StableDiffusionControlNetPipeline
from PIL import Image, ImageOps


def scribble(image: Image.Image) -> Image.Image:
    image = ImageOps.contain(ImageOps.grayscale(image), (512, 512))
    canvas = Image.new("L", (512, 512), 255)
    canvas.paste(image, ((512 - image.width) // 2, (512 - image.height) // 2))
    # Black line art on white is the expected scribble condition.
    return canvas.point(lambda value: 0 if value < 220 else 255).convert("RGB")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--prompt", default="")
    args = parser.parse_args()

    controlnet = ControlNetModel.from_pretrained(
        "lllyasviel/sd-controlnet-scribble", torch_dtype=torch.float16
    )
    pipe = StableDiffusionControlNetPipeline.from_pretrained(
        "stable-diffusion-v1-5/stable-diffusion-v1-5",
        controlnet=controlnet,
        torch_dtype=torch.float16,
        safety_checker=None,
    ).to("cuda")

    source = Image.open(args.input).convert("RGB")
    condition = scribble(source)
    detail = args.prompt.strip() or "the object in the drawing"
    prompt = (
        f"{detail}, single centered object, clean matte gray clay 3D model, "
        "studio product photograph, neutral background, complete shape, high detail"
    )
    negative = "text, watermark, frame, collage, multiple objects, cropped, blurry, line drawing"
    result = pipe(
        prompt=prompt,
        negative_prompt=negative,
        image=condition,
        num_inference_steps=30,
        guidance_scale=7.5,
        controlnet_conditioning_scale=1.3,
        generator=torch.Generator(device="cuda").manual_seed(2026),
    ).images[0]
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    result.save(args.output)
    del pipe, controlnet
    gc.collect()
    torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
