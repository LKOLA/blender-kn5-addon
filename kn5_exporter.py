"""
KN5 File Exporter for Blender
"""

import bpy
import bmesh
from mathutils import Matrix
from . import kn5_format


class KN5Exporter:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.kn5 = kn5_format.KN5File()
        self.material_map = {}
    
    def export_kn5(self, export_selected=False, apply_modifiers=True, triangulate=True):
        """Export Blender scene to KN5 file"""
        # Collect objects to export
        if export_selected:
            objects = bpy.context.selected_objects
        else:
            objects = bpy.context.scene.objects
        
        # Create materials
        for obj in objects:
            if obj.type == 'MESH':
                for mat in obj.data.materials:
                    if mat and mat.name not in self.material_map:
                        kn5_mat = self._create_kn5_material(mat)
                        self.material_map[mat.name] = self.kn5.add_material(kn5_mat)
        
        # Export objects hierarchy
        for obj in objects:
            if obj.parent is None:  # Root level only
                self._export_object(obj, self.kn5.root_node, apply_modifiers, triangulate)
        
        # Write KN5 file
        writer = kn5_format.KN5Writer()
        writer.write_file(self.kn5, self.filepath)
    
    def _create_kn5_material(self, blender_mat):
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
    
    def _export_object(self, obj, parent_node: kn5_format.Node, apply_modifiers, triangulate):
        """Recursively export object hierarchy"""
        # Create KN5 node
        kn5_node = kn5_format.Node(
            name=obj.name,
            node_type=kn5_format.NodeType.Mesh if obj.type == 'MESH' else kn5_format.NodeType.Base,
            transform=self._blender_matrix_to_kn5(obj.matrix_local)
        )
        
        # Export mesh if applicable
        if obj.type == 'MESH':
            kn5_node.mesh = self._export_mesh(obj, apply_modifiers, triangulate)
        
        parent_node.children.append(kn5_node)
        
        # Export children
        for child in obj.children:
            self._export_object(child, kn5_node, apply_modifiers, triangulate)
    
    def _export_mesh(self, obj, apply_modifiers, triangulate):
        """Export Blender mesh to KN5 mesh"""
        # Get mesh data
        if apply_modifiers:
            depsgraph = bpy.context.evaluated_depsgraph_get()
            mesh = obj.evaluated_get(depsgraph).to_mesh()
        else:
            mesh = obj.data
        
        # Triangulate if needed
        if triangulate:
            bm = bmesh.new()
            bm.from_mesh(mesh)
            bmesh.ops.triangulate(bm, faces=bm.faces[:])
            bm.to_mesh(mesh)
            bm.free()
        
        # Extract vertices and indices
        vertices = []
        indices = []
        
        # Ensure UV map exists
        if not mesh.uv_layers:
            mesh.uv_layers.new(name="UVMap")
        
        uv_layer = mesh.uv_layers.active
        
        for face in mesh.polygons:
            for loop_idx in face.loop_indices:
                loop = mesh.loops[loop_idx]
                vert = mesh.vertices[loop.vertex_index]
                
                uv = (0, 0)
                if uv_layer:
                    uv = uv_layer.data[loop_idx].uv[:]
                
                vertex = kn5_format.Vertex(
                    position=kn5_format.Vector3(vert.co.x, vert.co.y, vert.co.z),
                    normal=kn5_format.Vector3(vert.normal.x, vert.normal.y, vert.normal.z),
                    uv=tuple(uv)
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
        
        if apply_modifiers:
            bpy.data.meshes.remove(mesh)
        
        return kn5_mesh
    
    def _blender_matrix_to_kn5(self, matrix):
        """Convert Blender matrix to KN5 matrix"""
        kn5_matrix = kn5_format.Matrix44()
        for i in range(4):
            for j in range(4):
                kn5_matrix.m[i][j] = matrix[i][j]
        return kn5_matrix