# Live Mode Setup

This guide is only needed when testing **Shape my idea** with a new sketch.
The bundled 3D studies in the static website do not require this setup.

## 1. Prepare the Colab runtime

1. Open `notebooks/Sketch2Shape_SF3D_Demo.ipynb` in
   [Google Colab](https://colab.research.google.com/).
2. Select **Runtime → Change runtime type → T4 GPU**.
3. Run the notebook cells in order. The first run downloads CUDA, model
   dependencies, ControlNet, and SF3D, so it can take several minutes.

## 2. Get SF3D model access

SF3D weights are gated and are not committed to this repository.

1. Sign in or create a free [Hugging Face account](https://huggingface.co/join).
2. Open [Stable Fast 3D](https://huggingface.co/stabilityai/stable-fast-3d).
3. Select **Agree and access repository**.
4. Create a **Read** token from
   [Hugging Face access tokens](https://huggingface.co/settings/tokens).
5. Paste the `hf_...` token only into the notebook's hidden token prompt.

Never commit a token, use it in a public URL, or include it in a screenshot.

## 3. Start the GPU API

After the notebook setup succeeds, upload these two files from the repository
to the Colab `/content` folder:

```text
backend/controlnet_guide.py
backend/sf3d_api.py
```

```python
from google.colab import files
from pathlib import Path

uploaded = files.upload()
for filename, data in uploaded.items():
    Path('/content', filename).write_bytes(data)

assert Path('/content/controlnet_guide.py').is_file()
assert Path('/content/sf3d_api.py').is_file()
print('Backend scripts uploaded.')
```

Install the API dependencies and start the server:

```python
import sys, subprocess, time, requests

subprocess.run([
    sys.executable, '-m', 'pip', 'install', '-q',
    'fastapi', 'uvicorn[standard]', 'python-multipart', 'trimesh'
], check=True)

api_process = subprocess.Popen([
    sys.executable, '-m', 'uvicorn', 'sf3d_api:app',
    '--host', '0.0.0.0', '--port', '8000'
], cwd='/content')

for _ in range(30):
    try:
        response = requests.get('http://127.0.0.1:8000/health', timeout=2)
        if response.ok:
            print('SF3D API:', response.json())
            break
    except requests.RequestException:
        time.sleep(1)
else:
    raise RuntimeError('API did not become ready. Check the Colab logs.')
```

Expected response:

```text
SF3D API: {'status': 'ready'}
```

## 4. Create the temporary browser link

```python
import re, subprocess, time
from pathlib import Path

cloudflared = Path('/content/cloudflared')
if not cloudflared.exists():
    subprocess.run([
        'wget', '-q',
        'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64',
        '-O', str(cloudflared)
    ], check=True)
    cloudflared.chmod(0o755)

tunnel_process = subprocess.Popen(
    [str(cloudflared), 'tunnel', '--url', 'http://127.0.0.1:8000'],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
)

public_url = None
deadline = time.time() + 60
while time.time() < deadline:
    line = tunnel_process.stdout.readline()
    print(line, end='')
    match = re.search(r'https://[-a-z0-9]+\.trycloudflare\.com', line)
    if match:
        public_url = match.group(0)
        break

if not public_url:
    raise RuntimeError('Cloudflare tunnel URL was not created.')

print('PASTE THIS INTO LIVE MODE:', public_url)
print('Health check:', public_url + '/health')
```

## 5. Connect the website

1. Open the Sketch2Shape website.
2. Select **Live mode** in the header.
3. Paste the printed `https://...trycloudflare.com` URL into **Generation link**.
4. Upload/draw a clear, single-object sketch.
5. Click **Shape my idea**.

The Cloudflare quick-tunnel link expires when Colab disconnects. It is intended
for a live demo or video recording, not unattended long-term hosting.
