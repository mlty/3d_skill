"""Decimate GLB to target tri count for mobile game asset."""
import trimesh
import os

model_path = 'output/model_bundle/model.glb'
output_path = 'output/model_bundle/model_game.glb'
target_tris = 12000

print(f'Loading {model_path}...')
scene = trimesh.load(model_path)

if isinstance(scene, trimesh.Scene):
    meshes = list(scene.geometry.values())
    mesh = meshes[0]  # single component
else:
    mesh = scene

original = mesh.faces.shape[0]
print(f'Original: {original} tris, {mesh.vertices.shape[0]} verts')

# Decimate
print(f'Decimating to ~{target_tris} tris...')
ratio = 1.0 - (target_tris / original)
decimated = mesh.simplify_quadric_decimation(face_count=target_tris)

new_tris = decimated.faces.shape[0]
new_verts = decimated.vertices.shape[0]
print(f'Result: {new_tris} tris, {new_verts} verts')
print(f'Reduction: {(1 - new_tris/original)*100:.1f}%')

# Export as GLB
decimated.export(output_path, file_type='glb')
new_size = os.path.getsize(output_path)
print(f'Saved: {output_path} ({new_size/1024:.0f} KB)')

# Validate
if 5000 <= new_tris <= 15000:
    print('PASS: Within mobile budget (5K-15K)')
elif new_tris <= 50000:
    print('WARN: Above mobile but OK for PC')
else:
    print('FAIL: Still too high')

print(f'File size: {new_size/1024:.0f} KB - PASS' if new_size < 10*1024*1024 else f'FAIL: >10MB')
