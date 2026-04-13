"""Generate N candidate images for figurine workflow."""
import os
import time

from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
from pathlib import Path

# Read API key from environment variable or config file
_api_key = os.environ.get("GEMINI_API_KEY", "")
if not _api_key:
    import json as _json
    _key_path = Path(__file__).resolve().parent.parent / "config" / "image_gen_api_key.json"
    if _key_path.exists():
        with open(_key_path) as _f:
            _api_key = _json.load(_f).get("genai_api_key", "")
if not _api_key:
    raise RuntimeError("Set GEMINI_API_KEY env var or config/image_gen_api_key.json")

client = genai.Client(
    api_key=_api_key,
    http_options=types.HttpOptions(timeout=300_000),
)

prompt = (
    "Chibi 3D character of a Shiba Inu dog, full body, centered, front view, "
    "blind box collectible style, Pop Mart style, delicate and detailed clay texture, "
    "soft and cute proportions, big head small body, rounded and smooth modeling, "
    "fine handcrafted details, pastel color palette, dreamy lighting, soft shadows, "
    "matte finish, premium quality rendering. "
    "The background should be a solid, minimal color that contrasts clearly with the subject."
)

output_dir = Path("output/candidates")
output_dir.mkdir(parents=True, exist_ok=True)

# If generation fails, reuse existing images in output/candidates/ to avoid wasting API quota

num_candidates = 3
for idx in range(1, num_candidates + 1):
    # Skip if already generated
    out_path = output_dir / f"candidate_{idx}.png"
    if out_path.exists():
        print(f"Candidate {idx} already exists, skipping.")
        continue
    for attempt in range(3):
        print(f"Generating candidate image {idx}/{num_candidates} (attempt {attempt+1})...")
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                ),
            )
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    image = Image.open(BytesIO(part.inline_data.data))
                    image.save(str(out_path))
                    print(f"  Saved: {out_path}")
                    break
            else:
                print(f"  Warning: no image returned for candidate {idx}")
                continue
            break  # success
        except Exception as e:
            print(f"  Attempt {attempt+1} failed: {e}")
            if attempt < 2:
                time.sleep(5)

print(f"Done! {num_candidates} candidates generated.")
