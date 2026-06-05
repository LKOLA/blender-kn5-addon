"""
KN5 File Exporter for Blender 5.1.2+
"""

import bpy
import bmesh
from mathutils import Matrix
from pathlib import Path
from typing import Dict, Optional, List

from . import kn5_format


class KN5Exporter:
    """Exports Blender scenes to KN5 format"""
    
    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.kn5 = kn5_format.KN5File()
        self.material_map: Dict[str, int] = {}
    
    def export_kn5(self, export_selected: bool = False, apply_modifiers: bool = True, 
                   triangulate: bool = True, scale_factor: float = 1.0) -> None:
        """Export Blender scene to KN5 file"""
        # Collect objects to export
        if export_selected:
            objects = bpy.context.selected_objects
        else:
            objects = [obj for obj in bpy.context.scene.objects if obj.type in ('MESH', 'EMPTY')]
        
        # Create materials
        for obj in objects:
            if obj.type == 'MESH':
                for mat in obj.data.materials:
                    if mat and mat.name not in self.material_map:
                        kn5_mat = self._create_kn5_material(mat)
                        self.material_map[mat.name] = self.kn5.add_material(kn5_mat)
        
        # Export objects hierarchy (root level only)
        for obj in objects:
            if obj.parent is None:
                self._export_object(obj, self.kn5.root_node, apply_modifiers, triangulate, scale_factor)
        
        # Write KN5 file
        writer = kn5_format.KN5Writer()
        writer.write_file(self.kn5, str(self.filepath))
    
    def _create_kn5_material(self, blender_mat: bpy.types.Material) -> kn5_format.Material:
        """Convert Blender material to KN5 material"""
        kn5_mat = kn5_format.Material(blender_mat.name, "ksStandard")
        
        # Extract material properties from nodes
        if blender_mat.use_nodes:
            for node in blender_mat.node_tree.nodes:
                if node.type == 'BSDF_PRINCIPLED':
                    roughness = node.inputs['Roughness'].default_value
                    metallic = node.inputs['Metallic'].default_value
                    kn5_mat.properties['Roughness'] = roughness
                    kn5_mat.properties['Metallic'] = metallic
        
        return kn5_mat
    
    def _export_object(self, obj: bpy.types.Object, parent_node: kn5_format.Node, 
                      apply_modifiers: bool, triangulate: bool, scale_factor: float) -> None:
        """Recursively export object hierarchy"""
        # Create KN5 node
        node_type = kn5_format.NodeType.Mesh if obj.type == 'MESH' else kn5_format.NodeType.Base
        transform = self._blender_matrix_to_kn5(obj.matrix_local, scale_factor)
        
        kn5_node = kn5_format.Node(
            name=obj.name,
            node_type=node_type,
            transform=transform,
            visible=not obj.hide_viewport,
            active=obj.name != "Camera" and obj.name != "Light"
        )
        
        # Export mesh if applicable
        if obj.type == 'MESH':
            kn5_node.mesh = self._export_mesh(obj, apply_modifiers, triangulate, scale_factor)
        
        parent_node.children.append(kn5_node)
        
        # Export children
        for child in obj.children:
            self._export_object(child, kn5_node, apply_modifiers, triangulate, scale_factor)
    
    def _export_mesh(self, obj: bpy.types.Object, apply_modifiers: bool, 
                    triangulate: bool, scale_factor: float) -> kn5_format.Mesh:
        """Export Blender mesh to KN5 mesh"""
        # Get mesh data
        if apply_modifiers:
            try:
                depsgraph = bpy.context.evaluated_depsgraph_get()
                mesh = obj.evaluated_get(depsgraph).to_mesh()
            except Exception:
                mesh = obj.data.copy()
        else:
            mesh = obj.data
        
        # Triangulate if needed
        if triangulate:
            bm = bmesh.new()
            bm.from_mesh(mesh)
            bmesh.ops.triangulate(bm, faces=bm.faces[:])
            bm.to_mesh(mesh)
            bm.free()
            mesh.update()
        
        # Extract vertices and indices
        vertices: List[kn5_format.Vertex] = []
        indices: List[int] = []
        
        # Ensure UV map exists
        if not mesh.uv_layers:
            mesh.uv_layers.new(name="UVMap")
        
        uv_layer = mesh.uv_layers.active
        
        for face in mesh.polygons:
            for loop_idx in face.loop_indices:
                loop = mesh.loops[loop_idx]
                vert = mesh.vertices[loop.vertex_index]
                
                uv = (0.0, 0.0)
                if uv_layer:
                    uv = tuple(uv_layer.data[loop_idx].uv)
                
                # Apply scale to position
                position = kn5_format.Vector3(
                    vert.co.x * scale_factor,
                    vert.co.y * scale_factor,
                    vert.co.z * scale_factor
                )
                
                vertex = kn5_format.Vertex(
                    position=position,
                    normal=kn5_format.Vector3(vert.normal.x, vert.normal.y, vert.normal.z),
                    uv=uv
                )
                vertices.append(vertex)
                indices.append(len(vertices) - 1)
        
        # Get material
        material_id = 0
        if obj.data.materials:
            mat = obj.data.materials[0]
            if mat and mat.name in self.material_map:
                material_id = self.material_map[mat.name]
        
        kn5_mesh = kn5_format.Mesh(
            name=obj.name,
            vertices=vertices,
            indices=indices,
            material_id=material_id
        )
        
        if apply_modifiers and mesh != obj.data:
            bpy.data.meshes.remove(mesh)
        
        return kn5_mesh
    
    def _blender_matrix_to_kn5(self, matrix: Matrix, scale_factor: float = 1.0) -> kn5_format.Matrix44:
        """Convert Blender matrix to KN5 matrix"""
        kn5_matrix = kn5_format.Matrix44()
        for i in range(4):
            for j in range(4):
                kn5_matrix.m[i][j] = float(matrix[i][j])
        
        # Apply scale to translation components
        if scale_factor != 1.0:
            kn5_matrix.m[0][3] *= scale_factor
            kn5_matrix.m[1][3] *= scale_factor
            kn5_matrix.m[2][3] *= scale_factor
        
        return kn5_matrix
