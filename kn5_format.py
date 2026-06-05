"""
KN5 Binary Format Handler
Handles reading and writing of Assetto Corsa KN5 files
Based on community reverse-engineering of the format

Blender 5.1.2+ Compatible
Supports multiple KN5 format variants
"""

import struct
import math
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class NodeType(Enum):
    """Node types in KN5 hierarchy"""
    Base = 0
    Mesh = 1
    SkinnedMesh = 2


@dataclass
class Vector3:
    """3D Vector"""
    x: float
    y: float
    z: float
    
    def to_tuple(self) -> Tuple[float, float, float]:
        return (self.x, self.y, self.z)
    
    def __mul__(self, scalar: float) -> 'Vector3':
        """Scalar multiplication"""
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)
    
    def __rmul__(self, scalar: float) -> 'Vector3':
        return self.__mul__(scalar)
    
    @classmethod
    def from_tuple(cls, t: Tuple[float, float, float]) -> 'Vector3':
        return cls(t[0], t[1], t[2])


@dataclass
class Matrix44:
    """4x4 Transformation matrix"""
    m: List[List[float]]
    
    def __init__(self):
        # Identity matrix
        self.m = [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ]
    
    @classmethod
    def from_list(cls, values: List[float]) -> 'Matrix44':
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
    
    def scale(self, scalar: float) -> 'Matrix44':
        """Create scaled copy"""
        scaled = Matrix44()
        for i in range(4):
            for j in range(4):
                scaled.m[i][j] = self.m[i][j]
        # Scale translation components
        scaled.m[0][3] *= scalar
        scaled.m[1][3] *= scalar
        scaled.m[2][3] *= scalar
        return scaled


@dataclass
class Vertex:
    """Mesh vertex with attributes"""
    position: Vector3
    normal: Vector3
    uv: Tuple[float, float]
    tangent: Optional[Vector3] = None
    color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)


@dataclass
class Material:
    """KN5 Material definition"""
    name: str
    shader_name: str
    texture_diffuse: Optional[str] = None
    texture_normal: Optional[str] = None
    texture_specular: Optional[str] = None
    properties: Dict[str, float] = field(default_factory=dict)


@dataclass
class Mesh:
    """KN5 Mesh data"""
    name: str
    vertices: List[Vertex]
    indices: List[int]  # Triangle indices
    material_id: int
    layer_id: int = 0


@dataclass
class Node:
    """KN5 Scene node"""
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
    
    # Multiple signature variants supported
    SIGNATURE_KN5 = b'KN5\x00'      # Standard KN5
    SIGNATURE_SC69 = b'sc69'         # ksEditor scene variant
    SIGNATURE_KN56 = b'KN56'         # Alternative variant
    
    # Supported versions
    VERSIONS = [4, 5, 6, 7]  # Support versions 4-7
    
    def __init__(self):
        self.version: int = 6
        self.root_node: Node = Node("root", NodeType.Base, Matrix44())
        self.materials: List[Material] = []
        self.textures: Dict[str, bytes] = {}  # Embedded textures
    
    def add_material(self, material: Material) -> int:
        """Add material and return its ID"""
        self.materials.append(material)
        return len(self.materials) - 1
    
    def add_node(self, node: Node, parent: Optional[Node] = None) -> None:
        """Add node to hierarchy"""
        if parent is None:
            parent = self.root_node
        parent.children.append(node)


class KN5Reader:
    """Reads KN5 binary files (multiple format variants)"""
    
    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.data: Optional[bytes] = None
        self.pos: int = 0
        self.format_variant: str = "unknown"
    
    def read_file(self) -> KN5File:
        """Read and parse a KN5 file (auto-detect format)"""
        with open(self.filepath, 'rb') as f:
            self.data = f.read()
        
        self.pos = 0
        
        # Read and detect signature
        signature = self._read_bytes(4)
        self.pos = 0  # Reset position
        
        print(f"[KN5] Detected signature: {signature}")
        
        # Detect format variant
        if signature == KN5File.SIGNATURE_KN5:
            self.format_variant = "KN5"
            return self._read_kn5_standard()
        elif signature == KN5File.SIGNATURE_SC69 or signature.startswith(b'sc'):
            self.format_variant = "ksEditor_Scene (sc69)"
            return self._read_kn5_scene_variant()
        elif signature.startswith(b'KN5') or signature.startswith(b'KN56'):
            self.format_variant = "KN5_Variant"
            return self._read_kn5_standard()
        else:
            # Try to read as standard anyway (might work)
            print(f"[KN5] Unknown signature {signature}, attempting standard read...")
            self.format_variant = "Unknown (attempting standard)"
            return self._read_kn5_standard()
    
    def _read_kn5_standard(self) -> KN5File:
        """Read standard KN5 format"""
        self.pos = 0
        
        # Read header (4 bytes signature or skip if not present)
        first_bytes = self._peek_bytes(4)
        
        if first_bytes in [KN5File.SIGNATURE_KN5, KN5File.SIGNATURE_SC69]:
            signature = self._read_bytes(4)
        else:
            # No signature, just read version
            signature = None
        
        version = self._read_uint32()
        
        # Clamp version to supported range
        if version not in KN5File.VERSIONS:
            print(f"[KN5] Warning: Unsupported version {version}, clamping to 6")
            version = 6
        
        kn5 = KN5File()
        kn5.version = version
        
        # Read materials
        try:
            material_count = self._read_uint32()
            if material_count > 10000:  # Sanity check
                print(f"[KN5] Warning: Suspiciously large material count {material_count}, treating as 0")
                material_count = 0
            
            for _ in range(material_count):
                try:
                    kn5.materials.append(self._read_material())
                except Exception as e:
                    print(f"[KN5] Warning: Failed to read material: {e}")
                    break
        except Exception as e:
            print(f"[KN5] Warning: Failed to read materials: {e}")
        
        # Read root node
        try:
            kn5.root_node = self._read_node()
        except Exception as e:
            print(f"[KN5] Warning: Failed to read node hierarchy: {e}")
            # Create empty root if reading failed
            kn5.root_node = Node("root", NodeType.Base, Matrix44())
        
        return kn5
    
    def _read_kn5_scene_variant(self) -> KN5File:
        """Read ksEditor scene variant (sc69 format)"""
        self.pos = 0
        
        # Skip scene signature
        signature = self._read_bytes(4)
        
        kn5 = KN5File()
        
        # Scene format has different structure
        # Try to read as much as possible
        try:
            # Skip/read scene-specific data
            self.pos = 4  # Start after signature
            
            # Attempt to read node tree directly
            if self.pos < len(self.data):
                kn5.root_node = self._read_node()
        except Exception as e:
            print(f"[KN5] Note: Scene variant has limited support: {e}")
            kn5.root_node = Node("root", NodeType.Base, Matrix44())
        
        return kn5
    
    def _peek_bytes(self, count: int) -> bytes:
        """Peek at bytes without advancing position"""
        if self.data is None:
            return b''
        return self.data[self.pos:self.pos + count]
    
    def _read_bytes(self, count: int) -> bytes:
        """Read raw bytes"""
        if self.data is None:
            raise RuntimeError("No data loaded")
        result = self.data[self.pos:self.pos + count]
        self.pos += count
        return result
    
    def _read_uint32(self) -> int:
        """Read unsigned 32-bit integer"""
        if self.data is None:
            raise RuntimeError("No data loaded")
        if self.pos + 4 > len(self.data):
            raise RuntimeError("Not enough data to read uint32")
        value = struct.unpack_from('<I', self.data, self.pos)[0]
        self.pos += 4
        return value
    
    def _read_float(self) -> float:
        """Read single-precision float"""
        if self.data is None:
            raise RuntimeError("No data loaded")
        if self.pos + 4 > len(self.data):
            raise RuntimeError("Not enough data to read float")
        value = struct.unpack_from('<f', self.data, self.pos)[0]
        self.pos += 4
        return value
    
    def _read_string(self) -> str:
        """Read length-prefixed UTF-8 string"""
        if self.data is None:
            raise RuntimeError("No data loaded")
        length = self._read_uint32()
        
        # Sanity check for string length
        if length > 10000 or length < 0:
            raise RuntimeError(f"Invalid string length: {length}")
        
        if self.pos + length > len(self.data):
            raise RuntimeError(f"Not enough data to read string of length {length}")
        
        string = self.data[self.pos:self.pos + length].decode('utf-8', errors='ignore')
        self.pos += length
        return string
    
    def _read_vector3(self) -> Vector3:
        """Read 3D vector"""
        x = self._read_float()
        y = self._read_float()
        z = self._read_float()
        return Vector3(x, y, z)
    
    def _read_matrix44(self) -> Matrix44:
        """Read 4x4 matrix"""
        values = [self._read_float() for _ in range(16)]
        return Matrix44.from_list(values)
    
    def _read_material(self) -> Material:
        """Read material definition"""
        name = self._read_string()
        shader_name = self._read_string()
        
        material = Material(name, shader_name)
        
        # Read texture slots
        texture_count = self._read_uint32()
        for _ in range(texture_count):
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
        """Read scene node"""
        name = self._read_string()
        node_type_val = self._read_uint32()
        
        # Safe node type parsing
        try:
            node_type = NodeType(node_type_val)
        except ValueError:
            print(f"[KN5] Warning: Unknown node type {node_type_val}, treating as Base")
            node_type = NodeType.Base
        
        transform = self._read_matrix44()
        
        active = bool(self._read_uint32())
        cast_shadow = bool(self._read_uint32())
        visible = bool(self._read_uint32())
        
        node = Node(name, node_type, transform, active, cast_shadow, visible)
        
        # Read mesh if present
        if node_type in [NodeType.Mesh, NodeType.SkinnedMesh]:
            try:
                node.mesh = self._read_mesh()
            except Exception as e:
                print(f"[KN5] Warning: Failed to read mesh for node {name}: {e}")
        
        # Read children
        try:
            child_count = self._read_uint32()
            if child_count > 1000:  # Sanity check
                print(f"[KN5] Warning: Suspiciously large child count {child_count}, treating as 0")
                child_count = 0
            
            for _ in range(child_count):
                node.children.append(self._read_node())
        except Exception as e:
            print(f"[KN5] Warning: Failed to read children for node {name}: {e}")
        
        return node
    
    def _read_mesh(self) -> Mesh:
        """Read mesh data"""
        name = self._read_string()
        layer_id = self._read_uint32()
        material_id = self._read_uint32()
        
        # Read vertices
        vertex_count = self._read_uint32()
        if vertex_count > 1000000:  # Sanity check
            raise RuntimeError(f"Suspiciously large vertex count: {vertex_count}")
        
        vertices: List[Vertex] = []
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
        if index_count > 3000000:  # Sanity check
            raise RuntimeError(f"Suspiciously large index count: {index_count}")
        
        indices = [self._read_uint32() for _ in range(index_count)]
        
        return Mesh(name, vertices, indices, material_id, layer_id)


class KN5Writer:
    """Writes KN5 binary files"""
    
    def __init__(self):
        self.data: bytearray = bytearray()
    
    def write_file(self, kn5: KN5File, filepath: str) -> None:
        """Write KN5 file to disk"""
        self.data = bytearray()
        
        # Write header
        self._write_bytes(KN5File.SIGNATURE_KN5)
        self._write_uint32(kn5.version)
        
        # Write materials
        self._write_uint32(len(kn5.materials))
        for material in kn5.materials:
            self._write_material(material)
        
        # Write root node
        self._write_node(kn5.root_node)
        
        filepath_obj = Path(filepath)
        filepath_obj.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath_obj, 'wb') as f:
            f.write(self.data)
    
    def _write_bytes(self, data: bytes) -> None:
        """Write raw bytes"""
        self.data.extend(data)
    
    def _write_uint32(self, value: int) -> None:
        """Write unsigned 32-bit integer"""
        self.data.extend(struct.pack('<I', value))
    
    def _write_float(self, value: float) -> None:
        """Write single-precision float"""
        self.data.extend(struct.pack('<f', value))
    
    def _write_string(self, value: str) -> None:
        """Write length-prefixed UTF-8 string"""
        encoded = value.encode('utf-8')
        self._write_uint32(len(encoded))
        self._write_bytes(encoded)
    
    def _write_vector3(self, vec: Vector3) -> None:
        """Write 3D vector"""
        self._write_float(vec.x)
        self._write_float(vec.y)
        self._write_float(vec.z)
    
    def _write_matrix44(self, matrix: Matrix44) -> None:
        """Write 4x4 matrix"""
        for value in matrix.to_list():
            self._write_float(value)
    
    def _write_material(self, material: Material) -> None:
        """Write material definition"""
        self._write_string(material.name)
        self._write_string(material.shader_name)
        
        # Write texture slots
        textures: List[Tuple[str, str]] = []
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
    
    def _write_node(self, node: Node) -> None:
        """Write scene node"""
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
    
    def _write_mesh(self, mesh: Mesh) -> None:
        """Write mesh data"""
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
