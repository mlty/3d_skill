"""Repair STL model: merge parts, fix holes, make watertight."""
import pymeshlab
import trimesh
from pathlib import Path

input_path = "output/model_bundle/model.stl"
output_path = "output/model_bundle/model_repaired.stl"

print(f"Loading {input_path}...")
ms = pymeshlab.MeshSet()
ms.load_new_mesh(input_path)

print(f"Original: {ms.current_mesh().vertex_number()} verts, {ms.current_mesh().face_number()} faces")

# Step 1: Remove small isolated components (keep only largest)
print("Removing small disconnected components...")
ms.apply_filter("meshing_remove_connected_component_by_diameter", mincomponentdiag=pymeshlab.PercentageValue(10))

# Step 2: Remove duplicate faces and vertices
print("Cleaning duplicates...")
ms.apply_filter("meshing_remove_duplicate_faces")
ms.apply_filter("meshing_remove_duplicate_vertices")

# Step 3: Remove zero-area faces
print("Removing degenerate faces...")
ms.apply_filter("meshing_remove_null_faces")

# Step 4: Repair non-manifold edges and vertices
print("Repairing non-manifold geometry...")
ms.apply_filter("meshing_repair_non_manifold_edges")
ms.apply_filter("meshing_repair_non_manifold_vertices")

# Step 5: Close holes
print("Closing holes...")
ms.apply_filter("meshing_close_holes", maxholesize=100)

# Step 6: Re-orient normals coherently
print("Re-orienting normals...")
ms.apply_filter("meshing_re_orient_faces_coherentely")

print(f"Repaired: {ms.current_mesh().vertex_number()} verts, {ms.current_mesh().face_number()} faces")

ms.save_current_mesh(output_path)
print(f"Saved: {output_path}")

# Verify with trimesh
print("\nVerification:")
mesh = trimesh.load(output_path)
print(f"  Watertight: {'YES' if mesh.is_watertight else 'NO'}")
print(f"  Volume: {mesh.is_volume}")
print(f"  Faces: {len(mesh.faces):,}")
bounds = mesh.bounds
dims = bounds[1] - bounds[0]
print(f"  Dimensions: {dims[0]:.1f} x {dims[1]:.1f} x {dims[2]:.1f} mm")
