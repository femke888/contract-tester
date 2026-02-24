# PyInstaller spec for local-api-contract-tester

from PyInstaller.utils.hooks import collect_submodules

hidden = (
    collect_submodules("jsonschema")
    + collect_submodules("yaml")
    + collect_submodules("cryptography")
)

a = Analysis(
    ["run_cli.py"],
    pathex=[".", "src"],
    binaries=[],
    datas=[("README.md", "."), ("CHANGELOG.md", ".")],
    hiddenimports=hidden,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="contract-tester",
    console=True,
    version="version.txt",
)
