"""Deterministic image-quality checks used before 3D reconstruction.

This module intentionally does not choose a 3D model.  Its only job is to
reject weak image candidates and select the candidate that best preserves the
uploaded sketch.  It therefore remains useful with any future reference-image
or image-to-3D provider.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from io import BytesIO
from typing import Iterable

import cv2
import numpy as np
from PIL import Image, ImageOps


CANVAS = 384


@dataclass(frozen=True)
class CandidateScore:
    index: int
    total: float
    silhouette: float
    edge_similarity: float
    centering: float
    isolation: float
    accepted: bool
    reason: str

    def to_dict(self) -> dict:
        return asdict(self)


def load_rgb(data: bytes) -> np.ndarray:
    """Load arbitrary user image data to a square RGB OpenCV array."""
    image = Image.open(BytesIO(data)).convert("RGB")
    image = ImageOps.contain(image, (CANVAS, CANVAS), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (CANVAS, CANVAS), "white")
    x = (CANVAS - image.width) // 2
    y = (CANVAS - image.height) // 2
    canvas.paste(image, (x, y))
    return cv2.cvtColor(np.array(canvas), cv2.COLOR_RGB2BGR)


def _foreground_mask(image: np.ndarray) -> np.ndarray:
    """Estimate a foreground mask for a centered, light-background image."""
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    border = np.concatenate((lab[:8], lab[-8:], lab[:, :8], lab[:, -8:]), axis=0)
    background = np.median(border.reshape(-1, 3), axis=0)
    distance = np.linalg.norm(lab.astype(np.float32) - background, axis=2)
    mask = (distance > 15).astype(np.uint8) * 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    return mask


def _edge_map(image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.Canny(gray, 50, 150)


def _iou(a: np.ndarray, b: np.ndarray) -> float:
    a, b = a > 0, b > 0
    union = np.logical_or(a, b).sum()
    return float(np.logical_and(a, b).sum() / union) if union else 0.0


def _centering(mask: np.ndarray) -> float:
    moments = cv2.moments(mask)
    if moments["m00"] == 0:
        return 0.0
    cx, cy = moments["m10"] / moments["m00"], moments["m01"] / moments["m00"]
    distance = np.hypot(cx - CANVAS / 2, cy - CANVAS / 2) / (CANVAS / 2)
    return float(max(0.0, 1.0 - distance))


def _isolation(mask: np.ndarray) -> float:
    count, _, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    if count <= 1:
        return 0.0
    areas = stats[1:, cv2.CC_STAT_AREA]
    largest = float(areas.max())
    total = float(areas.sum())
    if total == 0:
        return 0.0
    # A single dominant object is preferred. Tiny detached marks are tolerated.
    return float(largest / total)


def score_candidate(sketch: np.ndarray, candidate: np.ndarray, index: int) -> CandidateScore:
    sketch_mask = _foreground_mask(sketch)
    candidate_mask = _foreground_mask(candidate)
    silhouette = _iou(sketch_mask, candidate_mask)

    sketch_edges = _edge_map(sketch)
    candidate_edges = _edge_map(candidate)
    dilated = cv2.dilate(candidate_edges, np.ones((5, 5), np.uint8))
    edge_similarity = float((np.logical_and(sketch_edges > 0, dilated > 0).sum()) /
                            max(1, (sketch_edges > 0).sum()))

    centering = _centering(candidate_mask)
    isolation = _isolation(candidate_mask)
    total = 0.40 * silhouette + 0.30 * edge_similarity + 0.15 * centering + 0.15 * isolation
    accepted = total >= 0.52 and isolation >= 0.72

    if accepted:
        reason = "Candidate passed silhouette, isolation, and framing checks."
    elif isolation < 0.72:
        reason = "Rejected: multiple disconnected foreground regions detected."
    else:
        reason = "Rejected: candidate does not preserve enough of the sketch silhouette."

    return CandidateScore(index, round(total, 4), round(silhouette, 4), round(edge_similarity, 4),
                          round(centering, 4), round(isolation, 4), accepted, reason)


def select_best(sketch_data: bytes, candidates: Iterable[bytes]) -> tuple[CandidateScore, list[CandidateScore]]:
    sketch = load_rgb(sketch_data)
    scores = [score_candidate(sketch, load_rgb(data), index) for index, data in enumerate(candidates)]
    if not scores:
        raise ValueError("At least one candidate image is required.")
    best = max(scores, key=lambda result: result.total)
    return best, scores
