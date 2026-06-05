"""
KN5 File Importer for Blender 5.1.2+
Supports multiple KN5 format variants
"""

import bpy
import bmesh
from mathutils import Matrix, Vector
from pathlib import Path
from typing import Dict, Optional

from . import kn5_format


class KN5Importer:
    """Imports KN5 files into Blender scenes"""
    
    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.kn5: Optional[kn5_format.KN5File] = None
        self.collection: Optional[bpy.types.Collection] = None
    
    def import_kn5(self, import_materials: bool = True, import_textures: bool = True) -> None:
        """Import KN5 file into Blender"""
        print(f"[KN5 Import] Starting import of: {self.filepath.name}")
        
        # Create a collection for imported objects
        collection_name = self.filepath.stem
        self.collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(self.collection)
        print(f"[KN5 Import] Created collection: {collection_name}")
        
        # Read KN5 file
        try:
            reader = kn5_format.KN5Reader(str(self.filepath))
            self.kn5 = reader.read_file()
            print(f"[KN5 Import] Successfully read file (variant: {reader.format_variant})")
            print(f"[KN5 Import] Found {len(self.kn5.materials)} materials")
        except Exception as e:
            print(f"[KN5 Import] Error reading file: {e}")
            raise
        
        # Create materials
        material_map: Dict[int, bpy.types.Material] = {}
        if import_materials:
            for i, material in enumerate(self.kn5.materials):
                try:
                    material_map[i] = self._create_material(material, import_textures)
                    print(f"[KN5 Import] Created material: {material.name}")
                except Exception as e:
                    print(f"[KN5 Import] Warning: Failed to create material {material.name}: {e}")
        
        # Create node hierarchy
        print(f"[KN5 Import] Importing node hierarchy...")
        try:
            self._import_node(self.kn5.root_node, None, material_map)
            print(f"[KN5 Import] Successfully imported node hierarchy")
        except Exception as e:
            print(f"[KN5 Import] Error importing nodes: {e}")
            raise
    
    def _create_material(self, kn5_material: kn5_format.Material, import_textures: bool) -> bpy.types.Material:
        """Create Blender material from KN5 material"""
        mat = bpy.data.materials.new(name=kn5_material.name)
        mat.use_nodes = True
        mat.blend_method = 'BLEND'
        mat.shadow_method = 'HASHED'  # Blender 5.1.2 compatible
        
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()
        
        # Create principled BSDF (compatible with Blender 5.1.2)
        bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
        output = nodes.new(type='ShaderNodeOutputMaterial')
        links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
        
        # Set base color
        bsdf.inputs['Base Color'].default_value = (0.8, 0.8, 0.8, 1.0)
        
        # Set roughness
        roughness = kn5_material.properties.get('Roughness', 0.5)
        bsdf.inputs['Roughness'].default_value = roughness
        
        # Set metallic
        metallic = kn5_material.properties.get('Metallic', 0.0)
        bsdf.inputs['Metallic'].default_value = metallic
        
        return mat
    
    def _import_node(self, kn5_node: kn5_format.Node, parent_obj: Optional[bpy.types.Object], 
                     material_map: Dict[int, bpy.types.Material]) -> Optional[bpy.types.Object]:
        """Recursively import node hierarchy"""
        # Create object for this node
        obj = None
        if kn5_node.mesh:
            obj = self._import_mesh(kn5_node, material_map)
        else:
            # Create empty object for non-mesh nodes
            empty_data = bpy.data.objects.new(kn5_node.name, None)
            if self.collection:
                self.collection.objects.link(empty_data)
            obj = empty_data
        
        if obj is None:
            return None
        
        # Set transformation
        try:
            obj.matrix_world = self._matrix44_to_blender(kn5_node.transform)
        except Exception as e:
            print(f"[KN5 Import] Warning: Failed to set transform for {kn5_node.name}: {e}")
        
        # Set object properties
        obj.hide_render = not kn5_node.visible
        obj.hide_viewport = not kn5_node.visible
        
        # Parent to parent object
        if parent_obj:
            obj.parent = parent_obj
        
        # Import children
        for child in kn5_node.children:
            self._import_node(child, obj, material_map)
        
        return obj
    
    def _import_mesh(self, kn5_node: kn5_format.Node, 
                     material_map: Dict[int, bpy.types.Material]) -> Optional[bpy.types.Object]:
        """Import mesh data"""
        mesh_data = kn5_node.mesh
        if mesh_data is None:
            return None
        
        try:
            # Create mesh
            mesh = bpy.data.meshes.new(name=mesh_data.name)
            obj = bpy.data.objects.new(name=kn5_node.name, object_data=mesh)
            
            # Link to collection
            if self.collection:
                self.collection.objects.link(obj)
            
            # Extract vertex data
            vertices = []
            normals = []
            for vertex in mesh_data.vertices:
                vertices.append(vertex.position.to_tuple())
                normals.append(vertex.normal.to_tuple())
            
            if not vertices:
                print(f"[KN5 Import] Warning: Mesh {mesh_data.name} has no vertices")
                return obj
            
            # Create mesh geometry
            faces = self._get_faces(mesh_data.indices)
            if faces:
                mesh.from_pydata(vertices, [], faces)
            else:
                mesh.from_pydata(vertices, [], [])
            
            # Set custom normals (Blender 5.1.2 compatible)
            if normals:
                try:
                    mesh.normals_split_custom_set_from_vertices(normals)
                    mesh.use_auto_smooth = True
                except Exception as e:
                    print(f"[KN5 Import] Warning: Failed to set normals: {e}")
            
            # Apply UV map
            if mesh_data.vertices:
                uv_layer = mesh.uv_layers.new(name="UVMap")
                for i, loop in enumerate(mesh.loops):
                    vertex_idx = loop.vertex_index
                    if vertex_idx < len(mesh_data.vertices):
                        uv = mesh_data.vertices[vertex_idx].uv
                        uv_layer.data[i].uv = uv
            
            # Apply material
            if mesh_data.material_id in material_map:
                obj.data.materials.append(material_map[mesh_data.material_id])
            
            print(f"[KN5 Import] Imported mesh: {mesh_data.name} ({len(mesh_data.vertices)} vertices)")
            return obj
        
        except Exception as e:
            print(f"[KN5 Import] Error importing mesh {mesh_data.name}: {e}")
            return None
    
    def _get_faces(self, indices: list) -> list:
        """Convert triangle indices to face tuples"""
        faces = []
        for i in range(0, len(indices), 3):
            if i + 2 < len(indices):
                faces.append((indices[i], indices[i+1], indices[i+2]))
        return faces
    
    def _matrix44_to_blender(self, matrix44: kn5_format.Matrix44) -> Matrix:
        """Convert KN5 matrix to Blender matrix"""
        values = matrix44.to_list()
        return Matrix([
            values[0:4],
            values[4:8],
            values[8:12],
            values[12:16]
        ])
