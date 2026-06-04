# Blender KN5 Import/Export Add-on

A professional Blender add-on for directly importing and exporting Assetto Corsa KN5 car model files without the need for ksEditor.

## Features

- **Import KN5 files** - Load Assetto Corsa car models directly into Blender
- **Export to KN5** - Save your Blender models as KN5 format
- **Material support** - Preserves material definitions and properties
- **Texture references** - Maintains texture slot information
- **Node hierarchy** - Preserves object hierarchy and transformations
- **Automatic triangulation** - Ensures geometry compatibility with Assetto Corsa
- **UV mapping** - Full support for UV coordinates
- **Transformation matrices** - Preserves precise positioning and rotation

## Installation

### Method 1: From Repository

1. Clone or download this repository
2. In Blender, go to **Edit > Preferences > Add-ons**
3. Click **Install** and select the add-on folder
4. Search for "KN5" and enable it

### Method 2: Direct Folder Copy

1. Find your Blender add-ons directory:
   - **Windows**: `C:\Users\[YourUsername]\AppData\Roaming\Blender Foundation\Blender\[Version]\scripts\addons`
   - **Mac**: `/Users/[YourUsername]/Library/Application Support/Blender/[Version]/scripts/addons`
   - **Linux**: `~/.config/blender/[Version]/scripts/addons`

2. Copy this entire folder into the addons directory
3. Restart Blender
4. Enable the add-on in **Edit > Preferences > Add-ons**

## Usage

### Importing KN5 Files

1. Go to **File > Import > KN5 - Assetto Corsa (.kn5)**
2. Select your KN5 file
3. Configure import options:
   - **Import Materials** - Import material definitions from the file
   - **Import Textures** - Create material nodes and texture references
4. Click **Import KN5**
5. Your car model will be imported with all components, materials, and textures

### Exporting to KN5

1. Select objects to export (or leave unselected to export all)
2. Go to **File > Export > KN5 - Assetto Corsa (.kn5)**
3. Configure export options:
   - **Export Selected Only** - Export only selected objects
   - **Apply Modifiers** - Bake all modifiers into the mesh before export
   - **Triangulate Meshes** - Convert all faces to triangles (required for Assetto Corsa)
4. Click **Export KN5**
5. Your file will be ready to use in Assetto Corsa

## Requirements

- Blender 4.0 or higher
- Python 3.7+

## Supported Features

- ✅ Mesh geometry (vertices, normals, UVs)
- ✅ Materials and shaders
- ✅ Texture references (Diffuse, Normal, Specular)
- ✅ Object hierarchy and transformations
- ✅ Multiple meshes per object
- ✅ Automatic mesh triangulation
- ✅ Modifier baking on export
- ✅ Custom properties preservation

## Known Limitations

- Skeleton/rigged animations are not yet supported (static models only)
- Embedded textures are referenced but not embedded in the KN5 file
- Skinned meshes have basic support
- Some advanced AC shader features may not be fully represented

## Troubleshooting

### "Invalid KN5 signature" Error

**Cause**: The file is corrupted or not a valid Assetto Corsa KN5 file

**Solution**: 
- Ensure the file is a valid KN5 exported from ksEditor or another AC tool
- Try importing the file with ksEditor to verify it's not corrupted

### Missing Textures After Import

**Cause**: Texture files are not in the expected location

**Solution**:
- Textures are referenced by path, not embedded
- Ensure texture files (.dds) are in the same folder as the KN5 file
- Manually link textures in Blender's Shader Editor if needed

### Export Failed / Corrupted File

**Cause**: Invalid mesh data or missing materials

**Solution**:
- Ensure all objects have valid mesh data
- Assign at least one material to each mesh
- Check the Blender console for detailed error messages
- Try exporting with "Apply Modifiers" enabled

### File Too Large

**Cause**: Too many vertices or very high resolution meshes

**Solution**:
- Reduce polygon count using Blender's decimation modifier
- Bake textures to reduce file size
- Split large models into multiple objects

## File Format Information

### KN5 Structure

The KN5 format is a proprietary binary format used by Assetto Corsa. This add-on implements the community-reverse-engineered specification:

- **Header**: File signature and version
- **Materials**: Material definitions with shader names and texture slots
- **Nodes**: Hierarchical object structure with transformations
- **Meshes**: Vertex data (positions, normals, UVs) and indices
- **Textures**: References to external DDS files

### Shader Support

The add-on exports materials with the "ksStandard" shader name, which is compatible with Assetto Corsa's rendering pipeline.

## Contributing

Contributions are welcome! Please:

1. Fork this repository
2. Create a feature branch
3. Test your changes thoroughly
4. Submit a pull request

## License

MIT License - See LICENSE file for details

## Disclaimer

This add-on is created by the community and is not affiliated with Kunos Simulazioni. Assetto Corsa is a product of Kunos Simulazioni. Use this tool at your own risk and always backup your original files.

## Resources

- [Assetto Corsa Mods](https://assettocorsamods.net/)
- [KN5 Converter (Reference Implementation)](https://github.com/ac-custom-shaders-patch/kn5-converter)
- [Blender Documentation](https://docs.blender.org/)
- [Assetto Corsa Custom Shaders Patch](https://assettocorsamods.net/threads/custom-shaders-patch.1244/)

## Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

**Made by the community, for the community** 🏎️
