"""Convert selected chibi image to 3D model via image_2_3d API."""
import json
import requests
import base64
import time
import zipfile
from pathlib import Path


def encode_image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def main():
    image_path = Path("output/chibi_candidates/candidate_1.png")
    if not image_path.exists():
        print(f"Error: {image_path} not found")
        return

    url = "http://57.152.82.155:8000/v3/generation3d"
    image_base64 = encode_image_to_base64(str(image_path))

    print(f"Sending {image_path} to 3D generation API...")
    start_time = time.time()

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

    headers = {"Content-Type": "application/json"}

    response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=600)

    elapsed = time.time() - start_time
    print(f"Status: {response.status_code} | Time: {elapsed:.1f}s | Size: {len(response.content)} bytes")

    if response.status_code == 200:
        output_zip = Path("output/model_bundle.zip")
        extract_dir = Path("output/model_bundle")
        output_zip.parent.mkdir(parents=True, exist_ok=True)
        extract_dir.mkdir(parents=True, exist_ok=True)

        with open(output_zip, "wb") as f:
            f.write(response.content)
        print(f"ZIP saved: {output_zip}")

        try:
            with zipfile.ZipFile(output_zip, "r") as zf:
                zf.extractall(extract_dir)
                print(f"Extracted to: {extract_dir}")
        except zipfile.BadZipFile:
            print("Error: Response is not a valid ZIP. Check API response.")
            return

        expected = ["model.glb", "model.stl", "model.png", "model.gif"]
        for name in expected:
            p = extract_dir / name
            status = f"{p.stat().st_size / 1024:.0f} KB" if p.exists() else "MISSING"
            print(f"  {name}: {status}")

        print("\nDone! Model bundle ready.")
    else:
        print(f"Error: API returned {response.status_code}")
        print(response.text[:500])


if __name__ == "__main__":
    main()
