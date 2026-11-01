# Sketch2Shape AI — Final Project Overview

## One-line summary

Sketch2Shape AI turns a single object sketch into an interactive, downloadable
3D model by first creating a coherent clay-style object guide and then
reconstructing a GLB mesh from that guide.

## What the final product looks like

The final product is a dark, browser-based creative workspace rather than a
technical notebook interface.

```text
┌────────────────────────────────────────────────────────────────────┐
│ Sketch2Shape                                      Live mode          │
├───────────────────────┬────────────────────────────────────────────┤
│                       │  Your creation                Keep / GLB    │
│  Give your idea       │                                            │
│  some depth.          │         Rotatable 3D GLB viewer             │
│                       │                                            │
│  [ Upload | Draw ]    │  Drag to rotate · Scroll to zoom            │
│                       │                                            │
│  Object note          ├────────────────────────────────────────────┤
│  [______________]     │  Sketch → Shape → Explore → Keep            │
│                       │  vertices · faces · generation time         │
│  [ Shape my idea ]    │                                            │
└───────────────────────┴────────────────────────────────────────────┘
```

The left side is deliberately simple: upload a sketch, draw one, optionally
add a short object note, and press **Shape my idea**. The right side is the
main result: a real GLB in a 3D viewer. Users can rotate, zoom, reset the
camera, open full screen, compare the original sketch, and download the mesh.

## What the user does

1. Uploads a PNG/JPG/WEBP sketch or draws directly on the canvas.
2. Optionally adds a short note such as “ceramic teapot with a curved spout.”
3. Connects live mode when a GPU worker is available.
4. Selects **Shape my idea**.
5. Explores the returned 3D model and downloads the GLB.

## What the system does

```text
User sketch
    ↓
Website sends image to GPU API
    ↓
ControlNet Scribble
    Creates a complete gray clay guide from sparse line art
    ↓
Stable Fast 3D (official SF3D)
    Infers geometry, texture, material, and UVs
    ↓
FastAPI returns GLB URL + mesh metadata
    ↓
Website loads the GLB in the interactive viewer
```

### Why the clay guide is important

SF3D is an image-to-3D model. Feeding it raw black-and-white line art directly
often produces thin, incomplete, or poorly textured geometry. ControlNet is
used as a bridge: it keeps the sketch's identity while adding the visual cues
that SF3D needs to form a plausible volumetric object.

## Core components

| Component | Role |
|---|---|
| `dist/index.html` | Product interface and input flow |
| `dist/app.js` | Upload, drawing, API call, viewer controls, metrics |
| `dist/styles.css` | Final dark visual design and responsive layout |
| `backend/controlnet_guide.py` | Produces the clay guide from the sketch |
| `backend/sf3d_api.py` | Runs the two-stage GPU workflow and serves results |
| Official SF3D | Produces the GLB mesh |
| `<model-viewer>` | Shows the returned GLB in the browser |

## What is demonstrated

- Sketch upload and in-browser drawing
- Conditional image generation from line art
- Image-to-3D conversion
- A rotatable browser 3D asset
- GLB export/download
- Model metadata: vertex count, face count, and elapsed generation time
- A real GPU inference API rather than only a mocked interface

## Current limitations

- The system sees one view, so hidden/back-side geometry is inferred rather
  than known.
- Geometry is plausible rather than guaranteed physically accurate.
- Some outputs may not be watertight, so they should not automatically be
  claimed as 3D-print-ready.
- Colab and Cloudflare quick tunnels are temporary; a persistent GPU host is
  required for unattended long-term access.
- The project intentionally avoids claiming that every drawing category will
  receive equally high-quality geometry.

## Why this is a strong prototype

The project does not stop at a classifier, a text description, or a 2D image.
It connects hand-drawn interaction, sketch conditioning, generative guidance,
mesh reconstruction, and a downloadable 3D asset in one user-facing workflow.
It also states the single-view limitation openly, which makes the technical
claim credible.

## Suggested presentation script

> “Sketch2Shape AI lets a user begin with a rough object sketch. We transform
> that sketch into a clay-style guide using ControlNet, then feed that guide to
> Stable Fast 3D. The output is a rotatable GLB that the user can inspect and
> download. We use the guide stage because direct line-art-to-3D loses volume;
> the guide gives the 3D model the surface information it needs.”

## What to show judges

1. The clean browser interface.
2. An uploaded sketch or a live canvas drawing.
3. The resulting clay guide image, if available.
4. The rotatable GLB from front, side, and oblique angles.
5. The mesh details and GLB download.
6. The repository documentation and two-stage architecture diagram.
