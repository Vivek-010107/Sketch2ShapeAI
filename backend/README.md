# Quality-gate backend

This service automatically ranks generated reference images before 3D
reconstruction. It is deliberately independent of TripoSR or any external 3D
provider.

## Run locally

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Use `POST /v1/quality/select` with one `sketch` image and one or more
`candidates` image files. The response either contains one accepted candidate
index or returns `retry`; the user never selects a candidate.

## Full automatic reference step

`POST /v1/jobs/reference` takes only a `sketch`, optional `prompt`, and
`candidate_count`. It calls a separate GPU worker configured using
`REFERENCE_GENERATOR_URL`, then scores all returned candidates and selects one
without user input.

The GPU worker contract is deliberately small:

```text
POST /v1/reference-candidates
multipart fields: sketch, prompt, count
response: {"candidates": ["base64 PNG/JPEG", ...]}
```

If no worker is configured, `/v1/jobs/reference` returns HTTP 503. This is
intentional: the service never pretends that an image was generated.

The first scorer is deterministic and lightweight: foreground/silhouette
overlap, edge preservation, centering, and single-object isolation. A future
CLIP identity scorer can be added without changing the endpoint contract.

## SF3D browser demo

`sf3d_api.py` is the separate, short-lived API used by the web interface. It
must run in the prepared Google Colab SF3D environment, where
`/content/stable-fast-3d`, `/content/controlnet_guide.py`, and
`/content/sf3d-env` already exist. It first makes a clay guide with ControlNet,
then gives that guide to the official SF3D runner. It exposes:

```text
GET  /health
POST /v1/generate    multipart fields: image, prompt
```

The response contains a GLB URL plus mesh counts. The Colab runtime is exposed
only temporarily through a Cloudflare quick tunnel; GitHub Pages cannot run
SF3D or provide a GPU.
