"""Convert STL to basic 3MF for Bambu Lab printer."""
import zipfile
import os
import sys
import trimesh
from pathlib import Path

def stl_to_3mf(stl_path, output_path=None):
    """Convert STL file to 3MF format that Bambu Lab printers accept."""
    stl_path = Path(stl_path)
    if not stl_path.exists():
        print(f"Error: {stl_path} not found")
        return None

    if output_path is None:
        output_path = stl_path.with_suffix('.3mf')
    output_path = Path(output_path)

    # Load mesh
    mesh = trimesh.load(str(stl_path))
    if isinstance(mesh, trimesh.Scene):
        meshes = list(mesh.geometry.values())
        mesh = meshes[0] if meshes else None
    if mesh is None:
        print("Error: No mesh data found")
        return None

    verts = mesh.vertices
    faces = mesh.faces
    print(f"Mesh: {len(faces)} faces, {len(verts)} vertices")

    # Build 3D Model XML
    model_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    model_xml += '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">\n'
    model_xml += '  <resources>\n'
    model_xml += '    <object id="1" type="model">\n'
    model_xml += '      <mesh>\n'

    # Vertices
    model_xml += '        <vertices>\n'
    for v in verts:
        model_xml += f'          <vertex x="{v[0]:.6f}" y="{v[1]:.6f}" z="{v[2]:.6f}" />\n'
    model_xml += '        </vertices>\n'

    # Triangles
    model_xml += '        <triangles>\n'
    for f in faces:
        model_xml += f'          <triangle v1="{f[0]}" v2="{f[1]}" v3="{f[2]}" />\n'
    model_xml += '        </triangles>\n'

    model_xml += '      </mesh>\n'
    model_xml += '    </object>\n'
    model_xml += '  </resources>\n'
    model_xml += '  <build>\n'
    model_xml += '    <item objectid="1" />\n'
    model_xml += '  </build>\n'
    model_xml += '</model>\n'

    # Content Types
    content_types = '<?xml version="1.0" encoding="UTF-8"?>\n'
    content_types += '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
    content_types += '  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml" />\n'
    content_types += '  <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml" />\n'
    content_types += '</Types>\n'

    # Relationships
    rels = '<?xml version="1.0" encoding="UTF-8"?>\n'
    rels += '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
    rels += '  <Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel" />\n'
    rels += '</Relationships>\n'

    # Write 3MF (ZIP archive)
    with zipfile.ZipFile(str(output_path), 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('[Content_Types].xml', content_types)
        zf.writestr('_rels/.rels', rels)
        zf.writestr('3D/3dmodel.model', model_xml)

    size_kb = os.path.getsize(output_path) / 1024
    print(f"Saved: {output_path} ({size_kb:.0f} KB)")
    return str(output_path)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python stl_to_3mf.py input.stl [output.3mf]")
        sys.exit(1)
    out = sys.argv[2] if len(sys.argv) > 2 else None
    result = stl_to_3mf(sys.argv[1], out)
    if result:
        print(f"Done: {result}")
