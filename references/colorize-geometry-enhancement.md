# Colorize Geometry Enhancement — Small Feature Protection (Eyes, Buttons, etc.)

## Problem Analysis

Why small features like eyes and buttons are easily lost:

| Level | Cause |
|-------|-------|
| **Texture** | Pixel ratio < min_pct, not selected as an independent color; or < island_size, merged during cleanup |
| **Texture** | preserve_salient_regions relies on "region vs. neighborhood contrast" — eyes close in color to skin tone may be missed |
| **3D** | Vertex color sampling is uniform; if the eye region has UV stretching or insufficient subdivision, resolution is too low |
| **Root cause** | Current logic relies purely on texture pixels without leveraging 3D geometry (eyes are typically convex) |

## Possible Approaches

### Approach A: Blender Curvature Bake (Recommended)

**Idea**: Eyes, noses, buttons, etc. are **convex surfaces** (high curvature). Bake curvature to a texture in Blender using the same UV layout, producing a "geometry saliency map".

**Pipeline**:
1. Import GLB → use Geometry Nodes Pointiness/Curvature output to vertex colors
2. Bake to UV texture (same resolution as base color)
3. In colorize: `protected_mask |= (curvature_map > threshold)`, merged with existing preserve_salient_regions
4. High-curvature regions are excluded from island cleanup and smoothing

**Pros**: Uses Blender built-in capabilities, no trimesh dependency; curvature maps 1:1 to UV  
**Cons**: Requires an extra Blender call (can be combined with texture extraction)

---

### Approach B: Trimesh Vertex Curvature → UV Rasterization

**Idea**: Use trimesh `vertex_defects` (convex=positive, concave=negative) to compute per-vertex curvature, then rasterize to texture space via UV.

**Pipeline**:
1. Parse GLB with pygltflib: vertices, faces, TEXCOORD_0
2. Build mesh with trimesh, compute `vertex_defects`
3. For each face: the 3 vertex UVs form a triangle, rasterize to texture, pixel value = max(3 vertex curvatures)
4. Produce curvature_map, merge into protected_mask (same as Approach A)

**Pros**: Pure Python, no extra Blender dependency  
**Cons**: UV rasterization must be implemented manually; must handle multi-material/multi-mesh

---

### Approach C: Adaptive Subdivision (within Blender)

**Idea**: In the `apply_vertex_colors` Blender script, apply additional subdivision to high-curvature regions.

**Implementation**:
- Use Geometry Nodes or Python to compute per-face curvature
- Subdivide faces where curvature > threshold, leave the rest unchanged
- Or: apply one extra global subdivision but only in high-curvature regions

**Pros**: Changes are confined to the Blender script  
**Cons**: Increases face count, slower export; requires a curvature threshold

---

### Approach D: Vertex Color Post-processing (after OBJ export)

**Idea**: After exporting OBJ, resample high-curvature vertices from the **original texture** (non-quantized), then snap to the 8-color palette.

**Pipeline**:
1. Export with UV preserved (`export_uv=True`)
2. Load OBJ with trimesh, compute vertex_defects
3. High-curvature vertices: sample from **original texture** via UV, find nearest of the 8 colors
4. Write back to OBJ vertex colors

**Pros**: Does not alter the main pipeline, acts as post-processing  
**Cons**: Requires retaining and passing the original texture; OBJ must include UV

---

## Implemented: Approach B (Trimesh + UV Rasterization)

Implemented in colorize v4 as `--geometry-protect` (enabled by default):

- Uses trimesh `vertex_defects` to compute per-vertex curvature (convex=positive)
- Rasterizes high-curvature faces to texture space, merged with `preserve_salient_regions`
- High-curvature regions (eyes, buttons, etc.) are excluded from island cleanup and smoothing
- Use `--no-geometry-protect` to disable

**Dependencies**: trimesh (already included), pygltflib (already included). Optional: scikit-image for faster triangle rasterization.

## Other Approaches (Not Implemented)

1. **Approach A**: Blender curvature bake — can be combined with Approach B
2. **Approach D**: Vertex color post-processing — optional post-processing step

## Recommended Parameters

- Curvature threshold: `vertex_defects > 0.1` or top 5% convex vertices
- `preserve_salient_regions` `min_region`: can be lowered to 32 to preserve smaller eyes
- `contrast_delta`: can be lowered to 12 to treat more small regions as "high contrast"
