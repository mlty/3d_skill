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
**Style** → realistic or Q版手办 (chibi figurine)?

Don't ask these as a checklist. If the user says "我想 3D 打印一个手办", you already
know the what (figurine), where (printing), and can just confirm style.

If the user is vague ("帮我做个龙"), ask one natural follow-up:
"做出来是要放游戏里、3D 打印出来、还是放 PPT 里？这三个的技术要求不太一样。"

### Step 2: Offer Key Choices

Once you know the scenario, offer 2-4 quick choices on the things that matter.
Don't overwhelm. Keep it like:

```
确认几个选项：

1. 风格
    A 写实   B Q版/手办风

2. 细节程度
    A 高细节   B 中等   C 低细节(更快)

选一下（如：1A 2B），或者直接告诉我你的偏好。
```

If the user already gave concrete choices (for example: "50mm 标准 柴犬"), skip this menu and proceed directly.

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
🎮 即将为你生成游戏资产模型：
    - 主体：[描述]
    - 风格：[写实/Q版]
    - 目标面数：[N] 三角面
    - 贴图：[尺寸] PBR（含 albedo/normal/roughness/metallic）
    - 输出格式：[FBX/GLB]
    - 适用引擎：[Unity/Unreal/Godot/通用]

开始生成？
```

For **3D Printing**:
```
🖨️ 即将为你生成 3D 打印模型：
    - 主体：[描述]
    - 风格：[写实/Q版]
    - 目标尺寸：[W] × [D] × [H] mm
    - 面数：不限（打印无实时渲染限制，越高越平滑）
    - 输出格式：STL
    - 打印优化：加厚几何体、减少悬挑、实心结构
    - 生成后将自动检测水密性、壁厚、底面平整度

开始生成？
```

For **PowerPoint**:
```
📊 即将为你生成 PPT 用 3D 模型：
    - 主体：[描述]
    - 风格：[写实/Q版]
    - 目标面数：≤[25K-30K] 三角面
    - 贴图：1024×1024
    - 输出格式：GLB（PowerPoint 原生支持）
    - 文件大小：控制在 10MB 以内

开始生成？
```

**Prompt**: Write both English and Chinese versions of the generation prompt.
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
我先给你看 3D 预览（缩略图 + 360 GIF）。
要继续做检测/交付，还是基于这个结果重新生成？
```

Proceed to Step 4 only when user confirms continue.

---

If user selects **Q版手办风格 (chibi/figurine style)** in Step 2, activate this specialized workflow instead of direct 3D generation.

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
我为你生成了 3 个手办风格效果图。请选择你最喜欢的：
[Image 1]  [Image 2]  [Image 3]
选择（如：图1、图2、图3）
```

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
3D 预览已生成：
- 缩略图：model.png
- 360 预览：model.gif

要继续进入打印检测，还是我按这个方向重新生成一版？
```

If user says "继续/可以/就这个", proceed to Step 4.
If user says "重生/改一下", go back to Step 2 or 2.5 with their feedback.

---

### Step 4: Validate

After getting the generated model, check it against the scenario's hard requirements.

**Game Asset checks:**
- Tri count within budget
- Has UV maps and PBR textures (albedo, normal, roughness, metallic)
- Correct format (FBX for Unity/Unreal, GLB for Godot/web)

**3D Printing checks** (run trimesh if in a Python environment):
- Manifold (watertight) — auto-repair small issues with trimesh
- Wall thickness ≥1.2mm for FDM
- Physical dimensions match user's requested size
- Has a flat base for bed adhesion
- Flag overhangs >45° (needs supports in slicer)

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
✅ 游戏资产生成完成！

📦 文件：[filename.fbx]
📋 模型参数：
    - 面数：[实际面数] 三角面（目标 [N]）
    - 贴图：[尺寸] PBR 全套（albedo ✓ normal ✓ roughness ✓ metallic ✓）
    - UV：已展开 ✓
    - 格式：[FBX/GLB] ✓

可以直接导入 [Unity/Unreal/Godot] 使用。
```

For **3D Printing**:
```
✅ 3D 打印模型生成完成！

📦 文件：[filename.stl]
📋 模型检测结果：
    - 水密性（manifold）：✅ 通过 [已自动修复 / 原生通过]
    - 壁厚：最薄 [X]mm（≥1.2mm 要求）✅
    - 尺寸：[W] × [D] × [H] mm ✅
    - 底面：平整 ✅
    - 悬挑：[无 / X处需要支撑] ⚠️

📋 Print Brief：
    - 建议层高：[0.12/0.20] mm
    - 建议填充：[N]%
    - 支撑：[无需/树状支撑]
    - 建议材料：[PLA]
```

For **PowerPoint**:
```
✅ PPT 3D 模型生成完成！

📦 文件：[filename.glb]
📋 模型参数：
    - 面数：[实际面数] 三角面（≤40K 限制）✅
    - 文件大小：[X] MB（≤10MB 限制）✅
    - 贴图：[尺寸]，已内嵌 ✅
    - 格式：GLB ✓

使用方法：PowerPoint → 插入 → 3D 模型 → 从文件，选择此 GLB 文件即可。
```

For **3D printing**, also include the full **Print Brief** (see above).

After the delivery summary for **3D Printing**, always ask:
"是否需要我现在连接 Bambu 打印机并开始打印？"

### Step 6: Optional Print via Bambu (3D Printing only)

If the user asks to print now, switch from model delivery to printer workflow.

**Hard rules (must follow):**
- NEVER auto-print without explicit user confirmation.
- MUST show preview before asking for print confirmation.
- MUST wait for a clear confirmation phrase (for example: "可以打印", "print it", "looks good").
- If user has not sliced yet, ask them to inspect/slice in Bambu Studio first.

**Print sequence:**
1. Check printer state (online/idle/errors)
2. Confirm target file and print intent
3. Start print with confirmed flag
4. Monitor progress and report key milestones

**Commands (reference):**
- Status: `python scripts/bambu.py status`
- Progress: `python scripts/bambu.py progress`
- Start print: `python scripts/bambu.py print <file> --confirmed`
- Pause/Resume/Cancel: `python scripts/bambu.py pause|resume|cancel`
- Monitor loop: `python scripts/monitor.py --auto-pause`

**Print handoff summary format:**
```
✅ 已开始发送到 Bambu 打印机

🖨️ 打印任务： [filename]
📡 打印机状态： [online/idle/printing]
📊 当前进度： [X]%
🧵 材料/颜色： [PLA / AMS 槽位]

后续我会继续监控；你也可以随时说：暂停、继续、取消。
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
5. **Prompt in both languages.** Give English + Chinese generation prompts when user is Chinese-speaking.
6. **Prefer execution over repeated questions.** If enough info is already provided, act first and only ask blocking questions.
