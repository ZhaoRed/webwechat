# -*- mode: python -*-

block_cipher = None


a = Analysis(['/home/zhaohongxing/workspace/python/webwechat/wechatlauncher.py'],
             pathex=['/home/zhaohongxing/Downloads/PyInstaller-3.3.1/wechat'],
             binaries=[],
             datas=[('./resource','resource')
             ],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='wechat',
          debug=False,
          strip=False,
          upx=True,
          console=False )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='wechat')
