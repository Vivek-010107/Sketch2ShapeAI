"""Adapter for a GPU-hosted sketch-to-reference worker.

The public web app never needs GPU libraries.  It sends a sketch to this
adapter, which calls a separately hosted worker (for example the Colab/Kaggle
worker when a GPU is available).  Keeping this boundary explicit means the
quality gate and user interface remain usable if the inference worker is moved
to another machine.
"""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass

import httpx


class ReferenceWorkerUnavailable(RuntimeError):
    """Raised when no configured GPU candidate-generation worker is reachable."""


@dataclass(frozen=True)
class ReferenceWorker:
    endpoint: str

    @classmethod
    def from_environment(cls) -> "ReferenceWorker":
        endpoint = os.getenv("REFERENCE_GENERATOR_URL", "").strip().rstrip("/")
        if not endpoint:
            raise ReferenceWorkerUnavailable(
                "REFERENCE_GENERATOR_URL is not configured. Start a GPU reference worker first."
            )
        return cls(endpoint)

    async def generate(self, sketch: bytes, filename: str, prompt: str, count: int = 4) -> list[bytes]:
        """Call the worker contract and return raw candidate image bytes.

        Contract:
          POST {REFERENCE_GENERATOR_URL}/v1/reference-candidates
          multipart: sketch=<image>, prompt=<optional string>, count=<1..8>
          response: {"candidates": ["<base64-encoded PNG/JPEG>", ...]}
        """
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(
                    f"{self.endpoint}/v1/reference-candidates",
                    files={"sketch": (filename or "sketch.png", sketch, "application/octet-stream")},
                    data={"prompt": prompt, "count": str(count)},
                )
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError as exc:
            raise ReferenceWorkerUnavailable(f"GPU reference worker is unavailable: {exc}") from exc

        encoded = payload.get("candidates")
        if not isinstance(encoded, list) or not encoded:
            raise ReferenceWorkerUnavailable("GPU reference worker returned no candidate images.")
        if len(encoded) > 8:
            raise ReferenceWorkerUnavailable("GPU reference worker returned too many candidates.")

        try:
            return [base64.b64decode(item, validate=True) for item in encoded]
        except (TypeError, ValueError) as exc:
            raise ReferenceWorkerUnavailable("GPU reference worker returned invalid image encoding.") from exc
