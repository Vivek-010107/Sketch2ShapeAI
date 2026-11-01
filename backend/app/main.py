"""FastAPI service for automatic candidate selection.

POST /v1/quality/select receives the uploaded sketch and candidate reference
images.  It returns exactly one selected candidate or a retry decision; the UI
never asks the end user to choose a generated image.
"""

from __future__ import annotations

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .scoring import select_best
from .reference_worker import ReferenceWorker, ReferenceWorkerUnavailable

app = FastAPI(title="Sketch2Shape Quality Gate", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "quality-gate"}


@app.post("/v1/quality/select")
async def choose_reference(
    sketch: UploadFile = File(...),
    candidates: list[UploadFile] = File(...),
) -> dict:
    if not sketch.content_type or not sketch.content_type.startswith("image/"):
        raise HTTPException(415, "Sketch must be an image file.")
    if not 1 <= len(candidates) <= 8:
        raise HTTPException(422, "Submit between 1 and 8 candidate images.")
    if any(not item.content_type or not item.content_type.startswith("image/") for item in candidates):
        raise HTTPException(415, "Every candidate must be an image file.")

    try:
        best, scores = select_best(await sketch.read(), [await item.read() for item in candidates])
    except Exception as exc:  # PIL/OpenCV reports invalid image payloads here.
        raise HTTPException(422, f"Unable to score image candidates: {exc}") from exc

    return {
        "decision": "accept" if best.accepted else "retry",
        "selected_candidate_index": best.index if best.accepted else None,
        "best_candidate": best.to_dict(),
        "candidates": [score.to_dict() for score in scores],
        "next_step": "send_selected_reference_to_3d" if best.accepted else "generate_new_candidates",
    }


@app.post("/v1/jobs/reference")
async def create_reference_job(
    sketch: UploadFile = File(...),
    prompt: str = Form(""),
    candidate_count: int = Form(4),
) -> dict:
    """Generate, score, and automatically select one reference candidate.

    A GPU worker is intentionally separate from this web-facing service. If no
    worker is configured, the caller receives an explicit 503 instead of a fake
    successful job.
    """
    if not sketch.content_type or not sketch.content_type.startswith("image/"):
        raise HTTPException(415, "Sketch must be an image file.")
    if not 1 <= candidate_count <= 8:
        raise HTTPException(422, "candidate_count must be between 1 and 8.")

    sketch_data = await sketch.read()
    try:
        worker = ReferenceWorker.from_environment()
        candidates = await worker.generate(sketch_data, sketch.filename or "sketch.png", prompt, candidate_count)
        best, scores = select_best(sketch_data, candidates)
    except ReferenceWorkerUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(422, f"Unable to process sketch: {exc}") from exc

    return {
        "decision": "accept" if best.accepted else "retry",
        "selected_candidate_index": best.index if best.accepted else None,
        "best_candidate": best.to_dict(),
        "candidates": [score.to_dict() for score in scores],
        "next_step": "send_selected_reference_to_3d" if best.accepted else "generate_new_candidates",
        "prompt_used": prompt,
    }
