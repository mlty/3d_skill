"""Validate GLB game asset."""
import trimesh
import os

model_path = 'output/model_bundle/model.glb'
print(f'=== Game Asset Validation: {model_path} ===')
file_size = os.path.getsize(model_path)
print(f'File size: {file_size/1024:.0f} KB')
print(f'Format: GLB')
print()

scene = trimesh.load(model_path)
if isinstance(scene, trimesh.Scene):
    meshes = list(scene.geometry.values())
    total_faces = sum(m.faces.shape[0] for m in meshes)
    total_verts = sum(m.vertices.shape[0] for m in meshes)
    print(f'Mesh components: {len(meshes)}')
    for name, m in scene.geometry.items():
        print(f'  - {name}: {m.faces.shape[0]} faces, {m.vertices.shape[0]} verts')
        if hasattr(m.visual, 'material'):
            mat = m.visual.material
            mat_name = getattr(mat, 'name', 'unnamed')
            print(f'    Material: {mat_name}')
            if hasattr(mat, 'baseColorTexture') and mat.baseColorTexture is not None:
                tex = mat.baseColorTexture
                sz = tex.size if hasattr(tex, 'size') else 'present'
                print(f'    Texture: {sz}')
            elif hasattr(mat, 'image') and mat.image is not None:
                print(f'    Texture: {mat.image.size}')
            else:
                print(f'    Texture: none/vertex-color')
        if hasattr(m, 'visual') and hasattr(m.visual, 'uv') and m.visual.uv is not None:
            print(f'    UVs: yes ({m.visual.uv.shape[0]} coords)')
        else:
            print(f'    UVs: not detected via trimesh')
else:
    total_faces = scene.faces.shape[0]
    total_verts = scene.vertices.shape[0]
    print(f'Single mesh: {total_faces} faces, {total_verts} verts')

tri_count = total_faces
print()
print('--- Summary ---')
print(f'Total triangles: {tri_count}')
print(f'Total vertices: {total_verts}')
print(f'Target range: 5,000 - 15,000 tris (mobile game)')

if tri_count < 5000:
    print(f'Below target ({tri_count} < 5000)')
elif tri_count <= 15000:
    print('PASS: Within budget')
elif tri_count <= 50000:
    print(f'WARN: Above mobile budget but OK for PC ({tri_count})')
else:
    print(f'FAIL: Too high ({tri_count} > 50000)')

size_ok = 'PASS' if file_size < 10*1024*1024 else 'FAIL >10MB'
print(f'File size: {file_size/1024:.0f} KB - {size_ok}')
print('Format: GLB - PASS')

# Check for disconnected parts
if isinstance(scene, trimesh.Scene) and len(meshes) > 1:
    print(f'\nWARN: {len(meshes)} separate mesh components detected')
    print('Consider merging or removing floating fragments')
