"""Temporary GPU API for the Sketch2Shape browser prototype.

Run this file in the Colab runtime that contains the official
/content/stable-fast-3d repository, /content/controlnet_guide.py, and the
/content/sf3d-env environment. It intentionally has no database or
authentication: it is for a short-lived demo tunnel only.
"""

from __future__ import annotations

import asyncio
import shutil
import subprocess
import uuid
from pathlib import Path

import trimesh
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

ROOT = Path("/content")
PYTHON = ROOT / "sf3d-env" / "bin" / "python"
REPOSITORY = ROOT / "stable-fast-3d"
GUIDE_PYTHON = Path("/usr/bin/python3")
GUIDE_RUNNER = ROOT / "controlnet_guide.py"
WORK = ROOT / "sketch2shape_api"
INPUTS = WORK / "inputs"
OUTPUTS = WORK / "outputs"

for directory in (INPUTS, OUTPUTS):
    directory.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Sketch2Shape SF3D demo API", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Short-lived tunnel used only for the prototype.
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/outputs", StaticFiles(directory=OUTPUTS), name="outputs")
generation_lock = asyncio.Lock()


@app.get("/health")
def health() -> dict[str, str]:
    if not PYTHON.is_file() or not (REPOSITORY / "run.py").is_file() or not GUIDE_RUNNER.is_file():
        raise HTTPException(500, "A required model runner is missing.")
    return {"status": "ready"}


@app.post("/v1/generate")
async def generate(
    image: UploadFile = File(...),
    prompt: str = Form(""),
) -> dict[str, int | str]:
    if not (image.content_type or "").startswith("image/"):
        raise HTTPException(415, "Upload a PNG, JPG, or WEBP sketch image.")

    raw = await image.read()
    if not raw or len(raw) > 12 * 1024 * 1024:
        raise HTTPException(413, "Image must be between 1 byte and 12 MB.")

    job_id = uuid.uuid4().hex
    suffix = Path(image.filename or "sketch.png").suffix.lower() or ".png"
    if suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
        suffix = ".png"
    source = INPUTS / f"{job_id}{suffix}"
    output_dir = OUTPUTS / job_id
    output_dir.mkdir()
    source.write_bytes(raw)
    output = output_dir / "model.glb"
    guide = output_dir / "clay_guide.png"

    guide_command = [
        str(GUIDE_PYTHON), str(GUIDE_RUNNER), "--input", str(source),
        "--output", str(guide), "--prompt", prompt[:180],
    ]

    sf3d_output = output_dir / "sf3d"
    command = [
        str(PYTHON), str(REPOSITORY / "run.py"), str(guide),
        "--output-dir", str(sf3d_output), "--texture-resolution", "512",
        "--remesh_option", "none",
    ]

    async with generation_lock:  # A T4 handles one SF3D request safely.
        try:
            guide_result = await asyncio.to_thread(
                subprocess.run, guide_command, text=True, capture_output=True,
                timeout=360, check=False,
            )
            if guide_result.returncode != 0 or not guide.is_file():
                raise HTTPException(500, "Guide-image generation failed. Check the Colab log.")
            result = await asyncio.to_thread(
                subprocess.run, command, cwd=str(REPOSITORY),
                text=True, capture_output=True, timeout=600, check=False,
            )
        except subprocess.TimeoutExpired as error:
            raise HTTPException(504, "SF3D generation timed out.") from error

    generated = sf3d_output / "0" / "mesh.glb"
    if result.returncode != 0 or not generated.is_file():
        shutil.rmtree(output_dir, ignore_errors=True)
        raise HTTPException(500, "SF3D generation failed. Check the Colab log.")

    shutil.copy2(generated, output)

    mesh = trimesh.load(output, force="mesh")
    return {
        "glb_url": f"/outputs/{job_id}/model.glb",
        "vertices": int(len(mesh.vertices)),
        "faces": int(len(mesh.faces)),
        "prompt_received": prompt[:180],
    }
