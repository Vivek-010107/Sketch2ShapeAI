# Sketch2Shape AI

**A sketch-to-3D object studio for turning simple line drawings into interactive,
rotatable 3D assets.**

Sketch2Shape AI helps a user move from an early idea to a three-dimensional
object. They can upload a drawing or sketch directly on the canvas, add a short
description, and explore the resulting object in the browser.

```text
Sketch → ControlNet Scribble guide → Stable Fast 3D → GLB → interactive viewer
```

## What the prototype does

- Upload a PNG, JPG, WEBP, or AVIF sketch
- Draw directly in the browser
- Add a short optional object note
- Rotate, zoom, reset, full-screen, compare, and download a GLB asset
- Explore bundled real 3D studies without requiring a GPU
- Generate a new asset through Live mode when a GPU worker is connected

## Explore it without setup

The site includes genuine SF3D outputs produced from the project pipeline:

- **Revolver study** — 9,267 vertices / 13,928 faces
- **Cup study** — 17,451 vertices / 30,600 faces
- **Raw-sketch study** — 13,926 vertices / 22,512 faces

Use the **Explore finished studies** cards at the bottom of the page to load a
model. Each is rotatable, inspectable, and downloadable directly in the static
website.

To preview locally, serve `dist/` through HTTP:

```powershell
cd "C:\ML Hackathon\sketch2shape-ai\dist"
py -m http.server 4173
```

Open <http://127.0.0.1:4173>. GitHub Pages provides the same static experience.

## How it works

Raw hand-drawn line art is difficult for a single-image 3D model to interpret.
Instead of sending it directly to 3D reconstruction, Sketch2Shape uses a
two-stage generation path:

1. **ControlNet Scribble** preserves the important lines and silhouette while
   creating a neutral clay-style object guide.
2. **Stable Fast 3D (SF3D)** reconstructs that guide into a textured,
   UV-unwrapped GLB mesh.
3. **model-viewer** presents the resulting GLB in a browser with familiar 3D
   controls.

This guide stage gives substantially better inputs to SF3D than raw sketches
alone.

## Live mode

The static website is usable without a GPU, but **Shape my idea** creates a
new 3D asset and therefore needs a running GPU worker. The complete reproducible
Google Colab workflow is included in:

[Sketch2Shape_SF3D_Demo.ipynb](notebooks/Sketch2Shape_SF3D_Demo.ipynb)

For the exact Colab, Hugging Face access-token, API, and temporary live-link
steps, see [Live Mode Setup](docs/LIVE_MODE_SETUP.md).

## Project layout

```text
dist/                 Static browser experience and bundled GLB examples
backend/              ControlNet guide runner and FastAPI GPU endpoint
notebooks/            Reproducible SF3D notebook and earlier classifier work
docs/                 Architecture, project overview, and live-mode setup
```

## Technical stack

- Browser UI: HTML, CSS, JavaScript, `<model-viewer>`
- Sketch conditioning: ControlNet Scribble
- Reconstruction: Stability AI Stable Fast 3D (SF3D)
- Asset format: GLB / OBJ
- Optional runtime endpoint: FastAPI + Cloudflare quick tunnel
- GPU demonstration runtime: Google Colab Tesla T4

## Known limitations

Sketches provide only a single view, so hidden/rear geometry is inferred rather
than observed. Output quality varies with the clarity, silhouette, and object
complexity of the input. Generated GLBs are interactive demonstration assets;
they are not guaranteed watertight or ready for 3D printing.

## Further reading

- [Final Project Overview](docs/FINAL_PROJECT_OVERVIEW.md)
- [Project Documentation](docs/PROJECT_DOCUMENTATION.md)
- [Live Mode Setup](docs/LIVE_MODE_SETUP.md)

## License and model access

SF3D weights are gated by Stability AI. A user running Live mode must accept
the official [Stable Fast 3D terms](https://huggingface.co/stabilityai/stable-fast-3d)
and use a Hugging Face read token. Tokens and model weights are intentionally
not included in this repository.
