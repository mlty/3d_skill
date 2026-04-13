"""Convert selected candidate image to 3D model via image_2_3d API."""
import json, requests, base64, time, zipfile, os
from pathlib import Path

image_path = Path('output/candidates/Gemini_3.png')
url = os.environ.get('IMAGE_2_3D_URL', 'http://xx.xxx.xx.155:8000/v3/generation3d')

with open(image_path, 'rb') as f:
    image_base64 = base64.b64encode(f.read()).decode('utf-8')

print(f'Sending {image_path} to {url} ...', flush=True)
start = time.time()

payload = {
    'image_base64': image_base64,
    'output_format': 'multi_formats',
    'seed': 0,
    'simplify': 0.95,
    'texture_size': 1024,
    'randomize_seed': True,
    'ss_guidance_strength': 7.5,
    'ss_sampling_steps': 12,
    'slat_guidance_strength': 3.0,
    'slat_sampling_steps': 12,
}

try:
    resp = requests.post(url, json=payload, timeout=600)
    elapsed = time.time() - start
    print(f'Status: {resp.status_code} | Time: {elapsed:.1f}s | Size: {len(resp.content)} bytes', flush=True)

    if resp.status_code == 200:
        out_zip = Path('output/model_bundle_print.zip')
        out_dir = Path('output/model_bundle_print')
        out_zip.parent.mkdir(parents=True, exist_ok=True)
        if out_dir.exists():
            import shutil
            shutil.rmtree(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        with open(out_zip, 'wb') as f:
            f.write(resp.content)
        with zipfile.ZipFile(out_zip, 'r') as zf:
            zf.extractall(out_dir)
        for name in ['model.glb', 'model.stl', 'model.png', 'model.gif', 'thumbnail.png']:
            p = out_dir / name
            if p.exists():
                print(f'  {name}: {p.stat().st_size/1024:.0f} KB', flush=True)
            else:
                print(f'  {name}: MISSING', flush=True)
        print('DONE', flush=True)
    else:
        print(f'Error: {resp.status_code}', flush=True)
        print(resp.text[:500], flush=True)
except Exception as e:
    print(f'FAILED: {e}', flush=True)
