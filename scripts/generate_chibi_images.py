"""Generate 3 chibi Shiba Inu candidate images for figurine workflow."""
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
from pathlib import Path
import time

client = genai.Client(
    api_key="XXX",
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

output_dir = Path("output/chibi_candidates")
output_dir.mkdir(parents=True, exist_ok=True)

for idx in range(1, 4):
    # Skip if already generated
    out_path = output_dir / f"candidate_{idx}.png"
    if out_path.exists():
        print(f"Candidate {idx} already exists, skipping.")
        continue
    for attempt in range(3):
        print(f"Generating candidate image {idx}/3 (attempt {attempt+1})...")
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

print("Done! 3 candidates generated.")
