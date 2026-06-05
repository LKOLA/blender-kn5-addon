# Blender KN5 Import/Export Add-on

[![Blender 5.1.2+](https://img.shields.io/badge/Blender-5.1.2%2B-blue)](https://www.blender.org/)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-green)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A professional Blender add-on for directly importing and exporting Assetto Corsa KN5 car model files without the need for ksEditor.

## Features

- 🚗 **Import KN5 files** - Load Assetto Corsa car models directly into Blender
- 💾 **Export to KN5** - Save your Blender models as KN5 format
- 🎨 **Material support** - Preserves material definitions and properties
- 🖼️ **Texture references** - Maintains texture slot information
- 📦 **Node hierarchy** - Preserves object hierarchy and transformations
- ⚡ **Automatic triangulation** - Ensures geometry compatibility with Assetto Corsa
- 🗺️ **UV mapping** - Full support for UV coordinates
- 🔄 **Transformation matrices** - Preserves precise positioning and rotation
- 📏 **Scale support** - Export with custom scaling factors

## Requirements

- **Blender**: 5.1.2 or higher
- **Python**: 3.11+ (included with Blender)

## Installation

### Method 1: From GitHub (Recommended)

1. Clone or download this repository:
   ```bash
   git clone https://github.com/LKOLA/blender-kn5-addon.git
   ```

2. Find your Blender add-ons directory:
   - **Windows**: `C:\Users\[YourUsername]\AppData\Roaming\Blender Foundation\Blender\5.1\scripts\addons`
   - **Mac**: `/Users/[YourUsername]/Library/Application Support/Blender/5.1/scripts/addons`
   - **Linux**: `~/.config/blender/5.1/scripts/addons`

3. Copy the entire `blender-kn5-addon` folder to your addons directory

4. Restart Blender

5. Enable the add-on:
   - Go to **Edit > Preferences > Add-ons**
   - Search for "KN5"
   - Enable "KN5 Assetto Corsa Import/Export"

### Method 2: From Blender (Quick Install)

1. In Blender: **Edit > Preferences > Add-ons > Install**
2. Select the downloaded addon folder
3. Search for "KN5" and enable it

## Usage

### Importing KN5 Files

1. Go to **File > Import > KN5 - Assetto Corsa (.kn5)**
2. Select your KN5 file
3. Configure import options:
   - **Import Materials** - Load material definitions from the file
   - **Import Textures** - Create material nodes and texture references
4. Click **Import KN5**
5. Your car model will be imported with all components, materials, and textures

### Exporting to KN5

1. Select objects to export (leave unselected to export all)
2. Go to **File > Export > KN5 - Assetto Corsa (.kn5)**
3. Configure export options:
   - **Export Selected Only** - Export only selected objects
   - **Apply Modifiers** - Bake all modifiers before export
   - **Triangulate Meshes** - Convert all faces to triangles (required)
   - **Scale Factor** - Scale geometry (1.0 = no scaling)
4. Click **Export KN5**
5. Your file will be ready to use in Assetto Corsa

## Supported Features

| Feature | Status | Notes |
|---------|--------|-------|
| Mesh geometry (vertices, normals, UVs) | ✅ | Full support |
| Materials and shaders | ✅ | ksStandard shader |
| Texture references | ✅ | Diffuse, Normal, Specular |
| Object hierarchy | ✅ | Preserves parent-child relationships |
| Transformations | ✅ | Position, rotation, scale |
| Automatic triangulation | ✅ | On export |
| Modifier baking | ✅ | On export |
| Custom scaling | ✅ | On export |
| Skeletal animations | ⚠️ | Basic support only |
| Embedded textures | ⚠️ | Referenced but not embedded |
| Skinned meshes | ⚠️ | Limited support |

## Troubleshooting

### "Invalid KN5 signature" Error

**Cause**: File is corrupted or not a valid Assetto Corsa KN5 file

**Solution**:
- Verify the file is a valid KN5 exported from ksEditor or another AC tool
- Try opening the file with ksEditor to confirm it's not corrupted
- Check file permissions and integrity

### Missing Textures After Import

**Cause**: Texture files are not in the expected location

**Solution**:
- Textures are referenced by path, not embedded in KN5
- Ensure `.dds` texture files are in the same folder as the KN5 file
- Manually link textures in Blender's Shader Editor if needed
- Update texture paths in material nodes

### Export Failed or Corrupted File

**Cause**: Invalid mesh data or missing materials

**Solution**:
- Ensure all objects have valid mesh data
- Assign at least one material to each mesh
- Check the Blender console (Window > Toggle System Console) for error messages
- Try exporting with "Apply Modifiers" enabled
- Verify mesh has no degenerate triangles

### File Too Large

**Cause**: High polygon count or complex models

**Solution**:
- Reduce polygon count using Blender's Decimation modifier
- Bake textures to reduce file size
- Split large models into multiple objects
- Use the Scale Factor option to reduce geometry size

### Models Import Incorrectly Scaled

**Cause**: Unit mismatch between Blender and Assetto Corsa

**Solution**:
- Use the **Scale Factor** option in export settings
- Typical AC models use 0.1 to 1.0 scale
- Test with a known-good model to determine the correct scale

## KN5 Format Information

### File Structure

KN5 is a binary format used by Assetto Corsa:

```
KN5 File
├── Header (signature + version)
├── Materials (shader names, textures, properties)
├── Node Tree
│   ├── Root Node
│   └── Child Nodes (recursive)
│       ├── Mesh Data (vertices, normals, UVs, indices)
│       └── Child Nodes...
└── Texture References
```

### Supported Shaders

- `ksStandard` - Standard material with diffuse, normal, specular maps
- `ksLight` - Emissive materials
- `ksTree` - Vegetation (with alpha blending)

### Material Properties

- `Roughness` - Surface roughness (0.0 - 1.0)
- `Metallic` - Metallic value (0.0 - 1.0)
- Custom numeric properties

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Test thoroughly with various KN5 files
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## Development

### File Structure

```
blender-kn5-addon/
├── __init__.py           # Main addon entry point
├── kn5_format.py        # KN5 binary format handler
├── kn5_importer.py      # Import functionality
├── kn5_exporter.py      # Export functionality
├── README.md            # This file
└── .gitignore          # Git ignore rules
```

### Blender 5.1.2 Compatibility

This addon is compatible with:
- Blender 5.1.2 and later
- Python 3.11+
- Uses modern Blender API (`bmesh`, `mathutils`, etc.)

## License

MIT License - See [LICENSE](LICENSE) file for details

## Disclaimer

This add-on is created by the community and is **not affiliated with Kunos Simulazioni**.

- **Assetto Corsa** is a product of Kunos Simulazioni
- Use this tool at your own risk and always backup your original files
- Respect copyright and licensing of car models you modify

## Credits

- **KN5 Format Reference**: [ac-custom-shaders-patch/kn5-converter](https://github.com/ac-custom-shaders-patch/kn5-converter)
- **Community Contributors**: Assetto Corsa modding community
- **Blender**: [Blender Foundation](https://www.blender.org/)

## Support

For issues, questions, or suggestions:

1. Check the [GitHub Issues](https://github.com/LKOLA/blender-kn5-addon/issues)
2. Open a new issue with:
   - Blender version
   - Python version
   - Detailed error message
   - Steps to reproduce
   - Attachment of problematic KN5 file (if possible)

## Resources

- [Assetto Corsa Mods](https://assettocorsamods.net/)
- [KN5 Format Wiki](https://assettocorsamods.net/threads/kn5-file-format.998/)
- [Blender Documentation](https://docs.blender.org/)
- [Assetto Corsa Custom Shaders Patch](https://assettocorsamods.net/threads/custom-shaders-patch.1244/)
- [ksEditor Documentation](https://assettocorsamods.net/threads/kseditor-assetto-corsa-editor-and-tips-thread.915/)

---

**Made by the community, for the community** 🏁

*Last Updated: June 2026 | Blender 5.1.2+*
