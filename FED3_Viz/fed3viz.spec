# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

files = [('fed_inspect','fed_inspect'),('getdata','getdata'),('groups','groups'),
         ('img','img'),('load','load'),('plots','plots'),('settings','settings'),
	 ('_version.py', '.')]

a = Analysis(['fed3viz.py'],
             pathex=['/Users/barbaraearnest/Documents/GitHub/FED3_Viz/FED3_Viz'],
             binaries=[],
             datas=files,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='fed3viz',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='fed3viz')
