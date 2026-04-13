---
name: ai-3d-model
description: >
  AI 3D model generation skill for game assets, 3D printing, and PowerPoint. Use whenever the
  user wants to generate a 3D model, create game-ready assets, prepare models for 3D printing,
  make 3D content for presentations, or create figurines/chibi characters. Also trigger on
    mentions of STL, GLB, FBX, Bambu Lab, manifold, polygon count, printer status, print monitor,
    or any AI 3D generation tool. Covers the full flow: conversational requirement gathering →
    style choices → generation → validation → delivery of a scene-compliant model file → ask
    whether to connect Bambu printer for printing → optional print monitoring.
---

# AI 3D Model Generation Skill

Turn a user's idea into a scene-compliant 3D model file through natural conversation.

## What This Skill Does

1. Chat with user to understand what they want and what it's for
2. Translate that into a generation prompt + technical constraints
3. Generate the model (via user's configured API)
4. Validate and auto-repair if needed
5. Deliver a file that's ready to use in the target scenario
6. After 3D printing delivery summary, ask whether to connect Bambu printer and start printing

## Three Scenarios

| Scenario | Output | Key Constraints |
|---|---|---|
| **Game Asset** | FBX or GLB | Tri budget by platform, PBR textures, clean UVs |
| **3D Printing** | STL | Manifold, wall thickness ≥1.2mm, correct physical size |
| **PowerPoint** | GLB | ≤40K tris, ≤10MB file, textures embedded |

---

## Conversation Flow

### Interaction Policy (Important)

- Minimize unnecessary back-and-forth.
- If user already provided key constraints (scenario, style, size, detail), do not re-ask as a checklist.
- Use sensible defaults for non-critical missing values and state them in one short line before execution.
- Ask follow-up questions only when missing info would block generation/printing.

### Step 1: Understand the Request

When a user comes in, figure out three things through natural conversation:

**What** → what do they want to model?
**Where** → where will it be used? (game / print / PPT)
**Style** → realistic or chibi figurine?

Don't ask these as a checklist. If the user says "I want to 3D print a figurine", you already
know the what (figurine), where (printing), and can just confirm style.

If the user is vague ("make me a dragon"), ask one natural follow-up:
"Is this for a game, 3D printing, or PowerPoint? The technical requirements are quite different."

### Step 2: Offer Key Choices

Once you know the scenario, offer 2-4 quick choices on the things that matter.
Don't overwhelm. Keep it like:

```
A few quick choices:

1. Style
    A Realistic   B Chibi / Figurine

2. Detail Level
    A High detail   B Medium   C Low detail (faster)

Pick one (e.g. 1A 2B), or just tell me your preference.
```

If the user already gave concrete choices (e.g. "50mm standard Shiba Inu"), skip this menu and proceed directly.

What choices to offer depends on the scenario:

**Game Asset**: style, detail level, platform (mobile/PC)
**3D Printing**: style, size (cm), detail level
**PowerPoint**: style, whether animated

For **figurine/chibi style** — if the user wants it, workflow moves to **Step 2.5 (Chibi Workflow)** for interactive image selection. Otherwise, proceed to Step 3.

### Step 3: Generate

Translate the user's choices into a prompt + parameters for their 3D generation API.

**Confirmation rule:**
- If key specs are ambiguous or incomplete, show a brief summary and ask for confirmation.
- If key specs are already clear, provide a one-line execution notice and start generation directly.

When a summary is needed, use a brief and clear format:

For **Game Asset**:
```
🎮 About to generate a game asset model:
    - Subject: [description]
    - Style: [realistic / chibi]
    - Target poly count: [N] triangles
    - Textures: [size] PBR (albedo/normal/roughness/metallic)
    - Output format: [FBX/GLB]
    - Target engine: [Unity/Unreal/Godot/general]

Proceed with generation?
```

For **3D Printing**:
```
🖨️ About to generate a 3D printing model:
    - Subject: [description]
    - Style: [realistic / chibi]
    - Target size: [W] × [D] × [H] mm
    - Poly count: unlimited (no real-time rendering constraints; higher = smoother)
    - Output format: STL
    - Print optimization: thicker geometry, reduced overhangs, solid forms
    - Will auto-check watertightness, wall thickness, and base flatness after generation

Proceed with generation?
```

For **PowerPoint**:
```
📊 About to generate a 3D model for PowerPoint:
    - Subject: [description]
    - Style: [realistic / chibi]
    - Target poly count: ≤[25K-30K] triangles
    - Textures: 1024×1024
    - Output format: GLB (native PowerPoint support)
    - File size: kept under 10MB

Proceed with generation?
```

**Prompt**: Write the generation prompt in English.
Optimize the prompt for the scenario — e.g., for 3D printing, include phrases like
"optimized for 3D printing, thicker geometry, reduced overhangs, solid forms."

**Parameters** (set based on scenario):

| Parameter | Game (Mobile) | Game (PC) | 3D Printing | PowerPoint |
|---|---|---|---|---|
| Tri count | 5K-15K | 15K-50K | 100K+ | 20K-30K |
| Texture | 1024 PBR | 2048 PBR | Optional | 1024 |
| Format | FBX/GLB | FBX/GLB | STL | GLB |
| File size | — | — | — | ≤10MB |

For 3D printing, also confirm physical size (in cm/mm) before generating.

**After user confirms:** Call `generate_3d()` API to generate the 3D model

**Call:** `generate_3d(prompt, height=[height_mm], format=[target_format])`

**Example calls by scenario:**
- Game Asset: `generate_3d(game_asset_prompt, format='FBX')` → asset.fbx
- 3D Printing: `generate_3d(print_prompt, height=80, format='STL')` → model.stl
- PowerPoint: `generate_3d(ppt_prompt, format='GLB')` → model.glb

#### 3.5: Preview Gate (Before Validate)

After any 3D generation, show preview assets first, then let user decide whether to continue:
- Prefer `model.png` (thumbnail) + `model.gif` (360) if API provides them.
- If API does not provide preview files, generate equivalent static preview and turntable GIF from the mesh.

Ask a short decision question:
```
Here's the 3D preview (thumbnail + 360 GIF).
Shall I continue to validation/delivery, or regenerate based on this result?
```

Proceed to Step 4 only when user confirms continue.

---

If user selects **chibi/figurine style** in Step 2, activate this specialized workflow instead of direct 3D generation.

**Workflow sequence:**

#### 2.5.1: Generate Candidate Images (text_2_image API)

Use chibi prompt template to generate **3 candidate images** for user to choose:

```
Chibi 3D character of [SUBJECT], full body, centered, front view, blind box collectible
style, Pop Mart style, delicate and detailed clay texture, soft and cute proportions,
big head small body, rounded and smooth modeling, fine handcrafted details, pastel color
palette, dreamy lighting, soft shadows, matte finish, premium quality rendering.
The background should be a solid, minimal color that contrasts clearly with the subject.
```

**Call:** `text_2_image(prompt, count=3)`

**Output:** Show user 3 different chibi character image variations. Ask them to select the one they like best:
- MUST render/show the actual generated images (inline images or local file links), not only text labels.
- Add a short caption for each image so user can quickly compare.
```
I've generated 3 figurine-style concept images. Pick your favorite:
[Image 1]  [Image 2]  [Image 3]
Choose (e.g. Image 1, Image 2, Image 3)
```

**Fallback — when text_2_image fails:**
If the `text_2_image` call fails (invalid API key, network error, service unavailable, etc.), automatically fall back to local candidate images:
1. Scan `output/candidates/` for existing image files (`.png`, `.jpg`, `.jpeg`, `.webp`).
2. If images are found, show them for user selection, same flow as normal generation:
```
⚠️ Image generation failed. Loading local candidates from output/candidates/:
[Image 1]  [Image 2]  ...
Choose (e.g. Image 1, Image 2), or provide your own image path.
```
3. If `output/candidates/` is empty or does not exist, prompt user to provide an image manually:
```
⚠️ Image generation failed and no local candidates found.
Please place a reference image in output/candidates/, or provide an image path directly.
```
4. After user selects an image, continue to Step 2.5.2 (image_2_3d).

#### 2.5.2: Convert Selected Image to 3D Model (image_2_3d API)

Once user selects an image, convert it to 3D using the image-to-3D API:

**Call:** `image_2_3d(selected_image, height=[target_height_mm])`

**Output:** API returns a `.zip` package that contains:
- `model.glb` (3D asset)
- `model.stl` (3D printing)
- `model.png` (preview)
- `model.gif` (360 preview)

For 3D printing, use `model.stl` directly from this ZIP for validation and delivery.
Do not run an extra STL conversion step.

Immediately after generation, show `model.png` and `model.gif` to user as a preview gate.
Ask user to choose:
- Continue to validation/printing workflow
- Regenerate with adjusted prompt/style

**Then continue to Step 4 (Validate) only after user approves preview.** Skip Step 3, model is already ready for validation.

#### 2.5.3: Preview Gate (Before Validate)

Show both assets from the ZIP:
- Thumbnail: `model.png`
- 360 preview: `model.gif`

Use a concise prompt:
```
3D preview is ready:
- Thumbnail: model.png
- 360 preview: model.gif

Shall I continue to print validation, or regenerate in a different direction?
```

If user confirms (e.g. "continue", "looks good", "go ahead"), proceed to Step 4.
If user wants changes (e.g. "redo", "try again"), go back to Step 2 or 2.5 with their feedback.

---

### Step 4: Validate

After getting the generated model, check it against the scenario's hard requirements.

**Game Asset checks:**
- Tri count within budget
- Has UV maps and PBR textures (albedo, normal, roughness, metallic)
- Correct format (FBX for Unity/Unreal, GLB for Godot/web)

**3D Printing checks** (run trimesh if in a Python environment):
- Physical dimensions match user's requested size

Read `references/print-validation.md` for the automated validation script.

**PowerPoint checks:**
- GLB format
- File size ≤10MB
- Tri count ≤40K
- Textures embedded (not external files)

### Step 5: Deliver

**Always deliver a model file.** Three possible outcomes:

**✅ Clean pass** → deliver the file with a result summary.

**🔧 Auto-repaired** → deliver the repaired file, note what was fixed.

**⚠️ Best effort** → if issues remain after up to 3 regeneration attempts, deliver the
best version with:
- What passed, what didn't
- Specific Blender fix steps for each remaining issue (menu paths, parameter values)
- Estimated repair time

**Always include a delivery summary.** Match the format to the scenario:

For **Game Asset**:
```
✅ Game asset generation complete!

📦 File: [filename.fbx]
📋 Model specs:
    - Poly count: [actual] triangles (target [N])
    - Textures: [size] PBR full set (albedo ✓ normal ✓ roughness ✓ metallic ✓)
    - UV: unwrapped ✓
    - Format: [FBX/GLB] ✓

Ready to import into [Unity/Unreal/Godot].
```

For **3D Printing**:
```
✅ 3D printing model generation complete!

📦 File: [filename.stl]
📋 Validation results:
    - Watertight (manifold): ✅ Passed [auto-repaired / natively clean]
    - Wall thickness: thinnest [X]mm (≥1.2mm requirement) ✅
    - Dimensions: [W] × [D] × [H] mm ✅
    - Base: flat ✅
    - Overhangs: [none / X areas need supports] ⚠️

📋 Print Brief:
    - Suggested layer height: [0.12/0.20] mm
    - Suggested infill: [N]%
    - Supports: [none needed / tree supports]
    - Suggested material: [PLA]
```

For **PowerPoint**:
```
✅ PowerPoint 3D model generation complete!

📦 File: [filename.glb]
📋 Model specs:
    - Poly count: [actual] triangles (≤40K limit) ✅
    - File size: [X] MB (≤10MB limit) ✅
    - Textures: [size], embedded ✅
    - Format: GLB ✓

Usage: PowerPoint → Insert → 3D Models → From File, select this GLB file.
```

For **3D printing**, also include the full **Print Brief** (see above).

After the delivery summary for **3D Printing**, always ask:
"Would you like me to connect the Bambu printer and start printing now?"

### Step 6: Optional Print via Bambu (3D Printing only)

If the user asks to print now, switch from model delivery to printer workflow.

**Hard rules (must follow):**
- NEVER auto-print without explicit user confirmation.
- MUST show preview before asking for print confirmation.
- MUST wait for a clear confirmation phrase (for example: "go ahead", "print it", "looks good").

**Automated slice + print pipeline (6 sub-steps):**

#### 6.1 Check printer state
```bash
python scripts/bambu.py status
```
Verify printer is online and idle before proceeding.

#### 6.2 Validate & repair STL
```bash
python scripts/analyze.py <model.stl> --repair --keep-main
```
Ensure the model is watertight and manifold (target: printability score ≥ 8.0/10).
Output: repaired/scaled STL file ready for slicing.

#### 6.3 Slice via Bambu Studio CLI

Bambu Studio CLI is used to slice the STL into a printable 3MF with embedded G-code.

**Profile paths** (under `C:\Program Files\Bambu Studio\resources\profiles\BBL\`):
- Machine: `machine\Bambu Lab H2D 0.4 nozzle.json`
- Process: `process\0.20mm Balanced Strength @BBL H2D.json`
- Filament: `filament\Bambu PLA Basic @BBL H2D.json`

> **H2D dual-extruder workaround:** The stock H2D machine profile has `nozzle_diameter: ['0.4', '0.4']` (dual extruder), which causes a "filaments cannot be mapped under auto mode for multi extruder printer" error in CLI slicing. Use a **modified single-nozzle machine profile** (`config/h2d_machine.json`) that sets `nozzle_diameter: ['0.4']` (single entry). This file is a copy of the stock profile with only the nozzle_diameter array trimmed to one element.

**Slice command:**
```powershell
$bambu = "C:\Program Files\Bambu Studio\bambu-studio.exe"
$machine = "config\h2d_machine.json"  # Modified single-nozzle H2D profile
$process = "C:\Program Files\Bambu Studio\resources\profiles\BBL\process\0.20mm Balanced Strength @BBL H2D.json"
$filament = "C:\Program Files\Bambu Studio\resources\profiles\BBL\filament\Bambu PLA Basic @BBL H2D.json"
$stl = "output\model_bundle\model_scaled.stl"
$output = "output\model_bundle\model_sliced.3mf"

& $bambu --load-settings "$machine;$process" --load-filaments "$filament" --slice 0 --export-3mf "$output" --ensure-on-bed "$stl"
```

**Verification:** After slicing, check that `model_sliced.3mf` contains `Metadata/plate_1.gcode`:
```powershell
python -c "import zipfile; z=zipfile.ZipFile('output/model_bundle/model_sliced.3mf'); [print(f'{i.filename}: {i.file_size//1024} KB') for i in z.infolist() if 'gcode' in i.filename.lower()]"
```
If no G-code is found, slicing failed — check error output and retry with adjusted profiles.

#### 6.4 Confirm with user

Show the user:
- Model preview (thumbnail/gif from model_bundle)
- Print settings summary (layer height, material, estimated time if available)
- Ask for explicit confirmation: "Confirm to start printing?"

#### 6.5 Upload & print
```bash
python scripts/bambu.py print output/model_bundle/model_sliced.3mf --confirmed
```
This uploads via FTP (port 990, implicit FTPS) and sends the MQTT print command.

#### 6.6 Monitor progress
```bash
python scripts/bambu.py progress
python scripts/monitor.py --auto-pause
```

**Commands (reference):**
- Status: `python scripts/bambu.py status`
- Progress: `python scripts/bambu.py progress`
- Start print: `python scripts/bambu.py print <file> --confirmed`
- Pause/Resume/Cancel: `python scripts/bambu.py pause|resume|cancel`
- Monitor loop: `python scripts/monitor.py --auto-pause`

**Print handoff summary format:**
```
✅ Print job sent to Bambu printer

🖨️ Print job: [filename]
📡 Printer state: [online/idle/printing]
📊 Progress: [X]%
🧵 Material/Color: [PLA / AMS slot]
⚙️ Slice settings: [layer height / infill / supports]

I'll keep monitoring. You can say: pause, resume, or cancel at any time.
```

---

## Technical Reference Files

Read these when you need detailed specs for a specific scenario:

| File | Contents |
|---|---|
| `references/game-assets.md` | Poly budgets by platform, PBR texture specs, engine format details, LOD strategy |
| `references/3d-printing.md` | Manifold rules, wall thickness by tech, overhang analysis, repair guide |
| `references/powerpoint.md` | Microsoft 3D performance targets, GLB optimization, animation support |
| `references/print-validation.md` | trimesh validation script, auto-repair logic, best-effort delivery with Blender fix guides |
| `references/bambu-printing.md` | Print setting recommendations by model type (layer height, infill, supports) |
| `references/api-guide.md` | Known API capabilities (Tripo, Meshy, etc.) — factual reference, no recommendations |

---

## API Configuration

This skill requires three API endpoints, all user-provided. No specific vendors are recommended.

**Three API slots:**

1. **text_2_image(prompt, count=3) → list of image URLs/files**
   - Purpose: Generate multiple candidate images from text prompt
   - Used in: Step 2.5 (chibi figurine workflow) to create 3 variations for user selection
   - Input: Text description + desired count (default 3)
   - Output: List of image files/URLs
   - Example: `text_2_image(chibi_prompt, count=3)` → [image_url_1, image_url_2, image_url_3]

2. **image_2_3d(image_path, height=None) → ZIP package**
   - Purpose: Convert image to 3D model
   - Used in: Step 2.5 (after user selects an image from text_2_image)
    - Input: Selected image file, target height (mm)
    - Output: ZIP package with `model.glb`, `model.stl`, `model.png`, `model.gif`
    - Preview usage: show `model.png` + `model.gif` to user for continue/regenerate decision
    - Example: `image_2_3d(selected_image, height=80)` → model_bundle.zip

3. **generate_3d(prompt, height=None, format='STL') → 3D model file**
   - Purpose: Direct text-to-3D generation (non-chibi workflows)
   - Used in: Step 3 for game assets, printing, PowerPoint scenarios
   - Input: Text description + dimensional constraints
   - Output: 3D model file
   - Example: `generate_3d(game_asset_prompt, format='FBX')` → asset.fbx

If user asks which API to use, answer neutrally and focus on parameters instead of vendors.

---

## Key Principles

1. **Keep it conversational.** Choices, not forms. 2-4 options, not 20 parameters.
2. **Always deliver a file.** Never end with "sorry, couldn't do it."
3. **Be honest about limits.** If the model has issues, say what and how to fix.
4. **Match depth to scenario.** Printing needs more validation. PPT needs less.
5. **Prompt in English.** Write generation prompts in English for best API results.
6. **Prefer execution over repeated questions.** If enough info is already provided, act first and only ask blocking questions.
