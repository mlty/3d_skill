"""Convert image to 3D model via image_2_3d API."""

import json
import requests
import base64
import time

def encode_image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return encoded

def main():

    # Load an image
    # image_path = Image.open(file_path)
    image_path = r"XXX"

    url = "http://57.152.82.155:8000/v3/generation3d"

    #image_path = "assets/example_image/T.png"
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
        output_file = "test.zip"
        print(f"Time taken: {end_time - start_time} seconds")
        with open(output_file, "wb") as f:
            f.write(response.content)
                
        print(f"✅ File saved as: {output_file}")

    else:
        print(f"err")
    
if __name__ == "__main__":
    main()