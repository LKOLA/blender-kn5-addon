"""
KN5 Binary Format Handler
Handles reading and writing of Assetto Corsa KN5 files
Based on community reverse-engineering of the format
"""

import struct
import math
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum


class NodeType(Enum):
    """Node types in KN5 hierarchy"""
    Base = 0
    Mesh = 1
    SkinnedMesh = 2


@dataclass
class Vector3:
    x: float
    y: float
    z: float
    
    def to_tuple(self) -> Tuple[float, float, float]:
        return (self.x, self.y, self.z)
    
    @classmethod
    def from_tuple(cls, t: Tuple[float, float, float]):
        return cls(t[0], t[1], t[2])


@dataclass
class Matrix44:
    """4x4 Transformation matrix"""
    m: List[List[float]]
    
    def __init__(self):
        # Identity matrix
        self.m = [
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ]
    
    @classmethod
    def from_list(cls, values: List[float]):
        """Create from 16 floats"""
        m = cls()
        for i in range(4):
            for j in range(4):
                m.m[i][j] = values[i * 4 + j]
        return m
    
    def to_list(self) -> List[float]:
        """Convert to 16 floats"""
        result = []
        for row in self.m:
            result.extend(row)
        return result


@dataclass
class Vertex:
    position: Vector3
    normal: Vector3
    uv: Tuple[float, float]
    tangent: Vector3 = None
    color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)


@dataclass
class Material:
    name: str
    shader_name: str
    texture_diffuse: Optional[str] = None
    texture_normal: Optional[str] = None
    texture_specular: Optional[str] = None
    properties: Dict[str, float] = field(default_factory=dict)


@dataclass
class Mesh:
    name: str
    vertices: List[Vertex]
    indices: List[int]  # Triangle indices
    material_id: int
    layer_id: int = 0


@dataclass
class Node:
    name: str
    node_type: NodeType
    transform: Matrix44
    active: bool = True
    cast_shadow: bool = True
    visible: bool = True
    children: List['Node'] = field(default_factory=list)
    mesh: Optional[Mesh] = None


class KN5File:
    """KN5 file structure container"""
    
    SIGNATURE = b'KN5\x00'
    VERSION = 6  # Assetto Corsa uses version 6
    
    def __init__(self):
        self.version = self.VERSION
        self.root_node: Node = Node("root", NodeType.Base, Matrix44())
        self.materials: List[Material] = []
        self.textures: Dict[str, bytes] = {}  # Embedded textures
    
    def add_material(self, material: Material) -> int:
        """Add material and return its ID"""
        self.materials.append(material)
        return len(self.materials) - 1
    
    def add_node(self, node: Node, parent: Optional[Node] = None):
        """Add node to hierarchy"""
        if parent is None:
            parent = self.root_node
        parent.children.append(node)


class KN5Reader:
    """Reads KN5 binary files"""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.data = None
        self.pos = 0
    
    def read_file(self) -> KN5File:
        """Read and parse a KN5 file"""
        with open(self.filepath, 'rb') as f:
            self.data = f.read()
        
        self.pos = 0
        
        # Read header
        signature = self._read_bytes(4)
        if signature != KN5File.SIGNATURE:
            raise ValueError(f"Invalid KN5 signature: {signature}")
        
        version = self._read_uint32()
        
        kn5 = KN5File()
        kn5.version = version
        
        # Read materials
        material_count = self._read_uint32()
        for _ in range(material_count):
            kn5.materials.append(self._read_material())
        
        # Read root node
        kn5.root_node = self._read_node()
        
        return kn5
    
    def _read_bytes(self, count: int) -> bytes:
        result = self.data[self.pos:self.pos + count]
        self.pos += count
        return result
    
    def _read_uint32(self) -> int:
        value = struct.unpack_from('<I', self.data, self.pos)[0]
        self.pos += 4
        return value
    
    def _read_float(self) -> float:
        value = struct.unpack_from('<f', self.data, self.pos)[0]
        self.pos += 4
        return value
    
    def _read_string(self) -> str:
        length = self._read_uint32()
        string = self.data[self.pos:self.pos + length].decode('utf-8', errors='ignore')
        self.pos += length
        return string
    
    def _read_vector3(self) -> Vector3:
        x = self._read_float()
        y = self._read_float()
        z = self._read_float()
        return Vector3(x, y, z)
    
    def _read_matrix44(self) -> Matrix44:
        values = [self._read_float() for _ in range(16)]
        return Matrix44.from_list(values)
    
    def _read_material(self) -> Material:
        name = self._read_string()
        shader_name = self._read_string()
        
        material = Material(name, shader_name)
        
        # Read texture slots
        texture_count = self._read_uint32()
        for i in range(texture_count):
            slot_name = self._read_string()
            texture_name = self._read_string()
            
            if slot_name == "Diffuse":
                material.texture_diffuse = texture_name
            elif slot_name == "NormalMap":
                material.texture_normal = texture_name
            elif slot_name == "Specular":
                material.texture_specular = texture_name
        
        # Read material properties
        property_count = self._read_uint32()
        for _ in range(property_count):
            prop_name = self._read_string()
            prop_value = self._read_float()
            material.properties[prop_name] = prop_value
        
        return material
    
    def _read_node(self) -> Node:
        name = self._read_string()
        node_type = NodeType(self._read_uint32())
        transform = self._read_matrix44()
        
        active = bool(self._read_uint32())
        cast_shadow = bool(self._read_uint32())
        visible = bool(self._read_uint32())
        
        node = Node(name, node_type, transform, active, cast_shadow, visible)
        
        # Read mesh if present
        if node_type in [NodeType.Mesh, NodeType.SkinnedMesh]:
            node.mesh = self._read_mesh()
        
        # Read children
        child_count = self._read_uint32()
        for _ in range(child_count):
            node.children.append(self._read_node())
        
        return node
    
    def _read_mesh(self) -> Mesh:
        name = self._read_string()
        layer_id = self._read_uint32()
        material_id = self._read_uint32()
        
        # Read vertices
        vertex_count = self._read_uint32()
        vertices = []
        for _ in range(vertex_count):
            pos = self._read_vector3()
            normal = self._read_vector3()
            uv_u = self._read_float()
            uv_v = self._read_float()
            
            vertex = Vertex(
                position=pos,
                normal=normal,
                uv=(uv_u, uv_v)
            )
            vertices.append(vertex)
        
        # Read indices
        index_count = self._read_uint32()
        indices = [self._read_uint32() for _ in range(index_count)]
        
        return Mesh(name, vertices, indices, material_id, layer_id)


class KN5Writer:
    """Writes KN5 binary files"""
    
    def __init__(self):
        self.data = bytearray()
    
    def write_file(self, kn5: KN5File, filepath: str):
        """Write KN5 file to disk"""
        self.data = bytearray()
        
        # Write header
        self._write_bytes(KN5File.SIGNATURE)
        self._write_uint32(kn5.version)
        
        # Write materials
        self._write_uint32(len(kn5.materials))
        for material in kn5.materials:
            self._write_material(material)
        
        # Write root node
        self._write_node(kn5.root_node)
        
        with open(filepath, 'wb') as f:
            f.write(self.data)
    
    def _write_bytes(self, data: bytes):
        self.data.extend(data)
    
    def _write_uint32(self, value: int):
        self.data.extend(struct.pack('<I', value))
    
    def _write_float(self, value: float):
        self.data.extend(struct.pack('<f', value))
    
    def _write_string(self, value: str):
        encoded = value.encode('utf-8')
        self._write_uint32(len(encoded))
        self._write_bytes(encoded)
    
    def _write_vector3(self, vec: Vector3):
        self._write_float(vec.x)
        self._write_float(vec.y)
        self._write_float(vec.z)
    
    def _write_matrix44(self, matrix: Matrix44):
        for value in matrix.to_list():
            self._write_float(value)
    
    def _write_material(self, material: Material):
        self._write_string(material.name)
        self._write_string(material.shader_name)
        
        # Write texture slots
        textures = []
        if material.texture_diffuse:
            textures.append(("Diffuse", material.texture_diffuse))
        if material.texture_normal:
            textures.append(("NormalMap", material.texture_normal))
        if material.texture_specular:
            textures.append(("Specular", material.texture_specular))
        
        self._write_uint32(len(textures))
        for slot_name, texture_name in textures:
            self._write_string(slot_name)
            self._write_string(texture_name)
        
        # Write properties
        self._write_uint32(len(material.properties))
        for prop_name, prop_value in material.properties.items():
            self._write_string(prop_name)
            self._write_float(prop_value)
    
    def _write_node(self, node: Node):
        self._write_string(node.name)
        self._write_uint32(node.node_type.value)
        self._write_matrix44(node.transform)
        
        self._write_uint32(int(node.active))
        self._write_uint32(int(node.cast_shadow))
        self._write_uint32(int(node.visible))
        
        # Write mesh if present
        if node.mesh:
            self._write_mesh(node.mesh)
        
        # Write children
        self._write_uint32(len(node.children))
        for child in node.children:
            self._write_node(child)
    
    def _write_mesh(self, mesh: Mesh):
        self._write_string(mesh.name)
        self._write_uint32(mesh.layer_id)
        self._write_uint32(mesh.material_id)
        
        # Write vertices
        self._write_uint32(len(mesh.vertices))
        for vertex in mesh.vertices:
            self._write_vector3(vertex.position)
            self._write_vector3(vertex.normal)
            self._write_float(vertex.uv[0])
            self._write_float(vertex.uv[1])
        
        # Write indices
        self._write_uint32(len(mesh.indices))
        for index in mesh.indices:
            self._write_uint32(index)