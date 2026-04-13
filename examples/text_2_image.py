import os
from google import genai
from PIL import Image
from io import BytesIO

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
prompt = "XXX"

# Call API
response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=prompt,  # text only, no image input
)

# Save generated images
for i, part in enumerate(response.parts):
    if part.inline_data is not None:
        image = Image.open(BytesIO(part.inline_data.data))
        image.save(f"output_{i}.png")
    elif part.text is not None:
        print(part.text)
