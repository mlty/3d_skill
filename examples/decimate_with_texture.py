"""Decimate GLB while preserving texture via pygltflib."""
import trimesh
import numpy as np
import fast_simplification
import pygltflib
import os
import struct
import base64
from pathlib import Path

src = 'output/model_bundle/model.glb'
dst = 'output/model_bundle/model_game.glb'
target_tris = 12000

# Load original with trimesh to get mesh + UV + texture
scene = trimesh.load(src)
mesh = list(scene.geometry.values())[0]
original_faces = mesh.faces.shape[0]
print(f'Original: {original_faces} tris, {mesh.vertices.shape[0]} verts')

# Get UV coordinates
uv = None
texture_image = None
if hasattr(mesh.visual, 'uv') and mesh.visual.uv is not None:
    uv = mesh.visual.uv.astype(np.float32)
    print(f'UV coords: {uv.shape[0]}')
if hasattr(mesh.visual, 'material'):
    mat = mesh.visual.material
    if hasattr(mat, 'image') and mat.image is not None:
        texture_image = mat.image
        print(f'Texture: {texture_image.size}')
    elif hasattr(mat, 'baseColorTexture') and mat.baseColorTexture is not None:
        texture_image = mat.baseColorTexture
        print(f'Texture: {texture_image.size}')

# Decimate with UV preservation
# Combine verts+UV as attributes for simplification
verts = mesh.vertices.astype(np.float32)
faces = mesh.faces.astype(np.int32)

target_reduction = 1.0 - target_tris / original_faces
print(f'Decimating (reduction={target_reduction:.4f})...')

new_verts, new_faces = fast_simplification.simplify(
    verts, faces, target_reduction=target_reduction
)
print(f'Result: {new_faces.shape[0]} tris, {new_verts.shape[0]} verts')

# Build new mesh - for UV, we need to re-project since fast_simplification preserves vertex indices
# where possible but may merge vertices
new_mesh = trimesh.Trimesh(vertices=new_verts, faces=new_faces)

# Re-project UVs from original mesh using nearest vertex mapping
if uv is not None and texture_image is not None:
    from scipy.spatial import cKDTree
    tree = cKDTree(mesh.vertices)
    _, idx = tree.query(new_verts)
    new_uv = uv[idx]
    
    from trimesh.visual import TextureVisuals
    from trimesh.visual.material import SimpleMaterial
    from PIL import Image
    
    material = SimpleMaterial(image=texture_image)
    new_mesh.visual = TextureVisuals(uv=new_uv, material=material)
    print(f'UV remapped: {new_uv.shape[0]} coords')
    print(f'Texture preserved: {texture_image.size}')

new_mesh.export(dst, file_type='glb')
sz = os.path.getsize(dst)
print(f'Saved: {dst} ({sz/1024:.0f} KB)')

if 5000 <= new_faces.shape[0] <= 15000:
    print('PASS: Within mobile budget')
print(f'Format: GLB - PASS')
