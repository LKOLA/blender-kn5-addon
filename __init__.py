bl_info = {
    "name": "KN5 Assetto Corsa Import/Export",
    "author": "LKOLA",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "File > Import/Export",
    "description": "Import and export KN5 files (Assetto Corsa car models) without needing ksEditor",
    "category": "Import-Export",
    "support": "COMMUNITY",
}

import bpy
from bpy_extras.io_utils import ImportHelper, ExportHelper
from bpy.props import StringProperty, BoolProperty, FloatProperty
import os

from . import kn5_format
from . import kn5_importer
from . import kn5_exporter


class ImportKN5(bpy.types.Operator, ImportHelper):
    """Import a KN5 file (Assetto Corsa car model)"""
    bl_idname = "import_scene.kn5"
    bl_label = "Import KN5"
    bl_options = {'PRESET', 'UNDO'}
    
    filename_ext = ".kn5"
    filter_glob: StringProperty(default="*.kn5", options={'HIDDEN'})
    
    import_materials: BoolProperty(
        name="Import Materials",
        description="Import material definitions from the KN5 file",
        default=True
    )
    
    import_textures: BoolProperty(
        name="Import Textures",
        description="Import texture references and create material nodes",
        default=True
    )
    
    def execute(self, context):
        try:
            importer = kn5_importer.KN5Importer(self.filepath)
            importer.import_kn5(
                import_materials=self.import_materials,
                import_textures=self.import_textures
            )
            self.report({'INFO'}, "KN5 imported successfully")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to import KN5: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}


class ExportKN5(bpy.types.Operator, ExportHelper):
    """Export selected objects to KN5 format (Assetto Corsa)"""
    bl_idname = "export_scene.kn5"
    bl_label = "Export KN5"
    bl_options = {'PRESET', 'UNDO'}
    
    filename_ext = ".kn5"
    filter_glob: StringProperty(default="*.kn5", options={'HIDDEN'})
    
    export_selected: BoolProperty(
        name="Export Selected Only",
        description="Export only selected objects",
        default=False
    )
    
    apply_modifiers: BoolProperty(
        name="Apply Modifiers",
        description="Apply all modifiers before export",
        default=True
    )
    
    triangulate: BoolProperty(
        name="Triangulate Meshes",
        description="Convert all faces to triangles (required for KN5)",
        default=True
    )
    
    def execute(self, context):
        try:
            exporter = kn5_exporter.KN5Exporter(self.filepath)
            exporter.export_kn5(
                export_selected=self.export_selected,
                apply_modifiers=self.apply_modifiers,
                triangulate=self.triangulate
            )
            self.report({'INFO'}, "KN5 exported successfully")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to export KN5: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}


def menu_func_import(self, context):
    self.layout.operator(ImportKN5.bl_idname, text="KN5 - Assetto Corsa (.kn5)")


def menu_func_export(self, context):
    self.layout.operator(ExportKN5.bl_idname, text="KN5 - Assetto Corsa (.kn5)")


def register():
    bpy.utils.register_class(ImportKN5)
    bpy.utils.register_class(ExportKN5)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(ImportKN5)
    bpy.utils.unregister_class(ExportKN5)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
    register()