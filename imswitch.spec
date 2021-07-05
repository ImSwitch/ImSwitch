# -*- mode: python ; coding: utf-8 -*-

import os
import sys

from vispy.app.backends import CORE_BACKENDS

from PyInstaller.building.api import TOC, PYZ, EXE, COLLECT
from PyInstaller.building.build_main import Analysis, BUNDLE
from PyInstaller.utils.hooks import collect_data_files, collect_submodules


mainFilePath = '.build_temp/__pyinstaller_main.py'
mainFileScript = '''
import os
os.environ['IMSWITCH_IS_BUNDLE'] = '1'
import imswitch.__main__
imswitch.__main__.main()
'''

datas = []
datas += collect_data_files('imswitch')
datas += collect_data_files('napari')
datas += collect_data_files('vispy')

hiddenImports = []
hiddenImports += collect_submodules('imswitch')
hiddenImports += ['vispy.ext._bundled.six']
hiddenImports += ['vispy.app.backends.' + b[1] for b in CORE_BACKENDS]
hiddenImports += ['vispy.app.backends._test']

blockCipher = None

try:
    os.makedirs(os.path.dirname(mainFilePath), exist_ok=True)

    with open(mainFilePath, 'w') as mainFile:
        mainFile.write(mainFileScript)

    a = Analysis([mainFilePath],
                 binaries=[],
                 datas=datas,
                 hiddenimports=hiddenImports,
                 hookspath=[],
                 runtime_hooks=[],
                 excludes=['matplotlib'],
                 win_no_prefer_redirects=False,
                 win_private_assemblies=False,
                 cipher=blockCipher,
                 noarchive=False)

    a.binaries = TOC([x for x in a.binaries if (
        not x[0].lower().startswith('api-ms-') and
        not x[0].lower().startswith('d3dcompiler') and
        not x[0].lower().startswith('msvcp') and
        not x[0].lower().startswith('ucrtbase') and
        not x[0].lower().startswith('vcomp') and
        not x[0].lower().startswith('vcruntime')
    )])

    pyz = PYZ(a.pure, a.zipped_data,
              cipher=blockCipher)

    exe = EXE(pyz,
              a.scripts,
              [],
              exclude_binaries=True,
              name='ImSwitch',
              icon='imswitch/_data/icon.ico',
              debug=False,
              bootloader_ignore_signals=False,
              strip=False,
              upx=True,
              console=True)

    if sys.platform != 'darwin':
        coll = COLLECT(exe,
                       a.binaries,
                       a.zipfiles,
                       a.datas,
                       strip=False,
                       upx=True,
                       upx_exclude=[],
                       name='ImSwitch')
    else:
        app = BUNDLE(exe,
                     a.binaries,
                     a.zipfiles,
                     a.datas,
                     name='ImSwitch.app',
                     icon=None,
                     bundle_identifier=None,
                     info_plist={
                        'NSPrincipalClass': 'NSApplication',
                        'NSHighResolutionCapable': 'True'
                     })
finally:
    try:
        os.remove(mainFilePath)
    except Exception:
        pass
