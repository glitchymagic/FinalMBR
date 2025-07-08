# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Tech Spot FY26 Report - Windows
Builds a standalone executable for Windows distribution
"""

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(SPEC))

# Collect all data files
datas = []

# Add Excel data files
excel_files = [
    'Combined_Incidents_Report_Feb_to_June_2025.xlsx',
    'Pre-TSQ Data-FebTOJune2025.xlsx',
    'Regions-Groups.xlsx'
]

for excel_file in excel_files:
    if os.path.exists(os.path.join(current_dir, excel_file)):
        datas.append((excel_file, '.'))

# Add templates directory
templates_dir = os.path.join(current_dir, 'templates')
if os.path.exists(templates_dir):
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith(('.html', '.css', '.js')):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, current_dir)
                dest_dir = os.path.dirname(rel_path)
                datas.append((rel_path, dest_dir))

# Add Python modules data
datas += collect_data_files('flask')
datas += collect_data_files('pandas')
datas += collect_data_files('numpy')
datas += collect_data_files('openpyxl')

# Hidden imports
hiddenimports = []
hiddenimports += collect_submodules('flask')
hiddenimports += collect_submodules('pandas')
hiddenimports += collect_submodules('numpy')
hiddenimports += collect_submodules('openpyxl')
hiddenimports += [
    'flask.templating',
    'flask.json',
    'pandas.io.formats.style',
    'pandas.plotting',
    'numpy.random.common',
    'numpy.random.bounded_integers',
    'numpy.random.entropy',
    'openpyxl.chart',
    'openpyxl.styles',
    'werkzeug.security',
    'jinja2.ext'
]

a = Analysis(
    ['main.py'],
    pathex=[current_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'PIL',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'test',
        'unittest',
        'pydoc',
        'doctest'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Tech Spot FY26 Report',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.txt'
) 