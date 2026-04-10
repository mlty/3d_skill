import json
import os
import requests
import base64
import time
import zipfile
from pathlib import Path
 
def encode_image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return encoded

def main():
    # 返回的.zip中包含了
    # model.glb for 3Dz资产
    # model.stl for 打印
    # model.png for 预览图
    # model.gif for 360度旋转预览图
    
    image_path = r"xxx.png"

    url = os.environ.get("IMAGE_2_3D_URL", "http://localhost:8000/v3/generation3d")

    image_base64 = encode_image_to_base64(image_path)

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
        "slat_sampling_steps": 12
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, data=json.dumps(payload), headers=headers)

    print("Status code:", response.status_code)
    print("Returned content size:", len(response.content))

    end_time = time.time()
    if response.status_code == 200:
        output_zip = Path("output/model_bundle.zip")
        extract_dir = Path("output/model_bundle")
        output_zip.parent.mkdir(parents=True, exist_ok=True)
        extract_dir.mkdir(parents=True, exist_ok=True)

        print(f"Time taken: {end_time - start_time} seconds")
        with open(output_zip, "wb") as f:
            f.write(response.content)

        print(f"✅ ZIP saved as: {output_zip}")

        try:
            with zipfile.ZipFile(output_zip, "r") as zf:
                zf.extractall(extract_dir)
                print(f"✅ Extracted to: {extract_dir}")
        except zipfile.BadZipFile:
            print("⚠️ Response is not a ZIP package; check API response format.")
            return

        expected = ["model.glb", "model.stl", "model.png", "model.gif"]
        for name in expected:
            p = extract_dir / name
            print(f"- {name}: {'found' if p.exists() else 'missing'}")

    else:
        print(f"err")
    
if __name__ == "__main__":
    main()