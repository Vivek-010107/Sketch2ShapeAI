# Sketch2Shape AI

This repository starts the product as an honest, quality-gated sketch-to-3D workflow rather than claiming universal direct sketch reconstruction.

## Current milestone

`dist/` is a private, static product prototype: it accepts an image in the browser and explains the staged pipeline. It does not yet upload images or perform inference.

## Next implementation milestone (Colab GPU backend)

1. Build a persistent FastAPI worker in the tested Python 3.11 environment.
2. Receive a single sketch, normalize it, and run the known-class classifier plus open-vocabulary fallback.
3. Produce several sketch-conditioned reference candidates.
4. Score candidates for silhouette similarity, object identity, clean background, and view consistency.
5. Send only a passing candidate to the patched TripoSR worker; return OBJ/GLB plus the quality report.

The existing notebook remains the experimental record. Before production work, extract its reproducible environment setup and the two verified TripoSR source patches into versioned scripts.
