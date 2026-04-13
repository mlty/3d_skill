"""One-shot: convert selected candidate image to 3D model (with retry)."""
import json, requests, base64, time, zipfile
from pathlib import Path

image_path = "output/candidates/Gemini_3.png"
url = "http://xx.xxx.xx.155:8000/v3/generation3d"

with open(image_path, "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode("utf-8")

payload = {
    "image_base64": image_base64,
    "output_format": "multi_formats",
    "seed": 0,
    "simplify": 0.95,
    "texture_size": 1024,
    "randomize_seed": True,
    "ss_guidance_strength": 7.5,
    "ss_sampling_steps": 12,
    "slat_guidance_strength": 3.0,
    "slat_sampling_steps": 12,
}

response = None
for attempt in range(1, 4):
    print(f"Attempt {attempt}/3: Sending to image_2_3d API...")
    start = time.time()
    try:
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=300)
        elapsed = time.time() - start
        print(f"Status: {response.status_code}, Size: {len(response.content)} bytes, Time: {elapsed:.1f}s")
        break
    except Exception as e:
        elapsed = time.time() - start
        print(f"Attempt {attempt} failed after {elapsed:.1f}s: {e}")
        if attempt < 3:
            print("Retrying in 5s...")
            time.sleep(5)

if response is None:
    print("All attempts failed.")
    exit(1)

if response.status_code == 200:
    output_zip = Path("output/model_bundle.zip")
    extract_dir = Path("output/model_bundle")
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    extract_dir.mkdir(parents=True, exist_ok=True)
    with open(output_zip, "wb") as f:
        f.write(response.content)
    with zipfile.ZipFile(output_zip, "r") as zf:
        zf.extractall(extract_dir)
    for name in ["model.glb", "model.stl", "model.png", "model.gif"]:
        p = extract_dir / name
        status = "found" if p.exists() else "missing"
        print(f"  {name}: {status}")
    print("Done!")
else:
    print(f"Error: {response.text[:500]}")
