# Sketch2Shape AI — Submission Documentation

## Problem

Hand-drawn sketches quickly express an object's visible silhouette but cannot
directly be inspected as 3D assets. This prototype explores a usable path from
one sketch to a rotatable GLB.

## Solution

The system uses two generative stages. ControlNet Scribble preserves line-art
structure while producing a coherent clay-style guide. SF3D then infers a mesh,
material, and GLB export from that guide. The website provides drawing/upload,
3D inspection, and download.

## Technology

| Layer | Technology |
|---|---|
| Interface | HTML, CSS, JavaScript, model-viewer |
| Guide generation | Stable Diffusion v1.5 + ControlNet Scribble |
| Reconstruction | Stability AI Stable Fast 3D |
| GPU endpoint | FastAPI + Uvicorn |
| Runtime | NVIDIA Tesla T4 / CUDA PyTorch |
| Output | GLB / glTF |

## Responsible claim

The output is a plausible 3D interpretation, not ground-truth reconstruction.
It should not be presented as universally accurate, watertight, or suitable for
manufacturing. It performs best on clean, central, single-object sketches.

## Deployment

The frontend can be hosted as static files. The GPU worker must be hosted
separately. Colab plus a Cloudflare quick tunnel is appropriate for a live demo
but temporary; persistent judging requires a GPU provider.
