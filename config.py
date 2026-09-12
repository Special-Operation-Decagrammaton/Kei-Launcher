import sys
from pathlib import Path

ptbr = "--ptbr" in sys.argv

REPO = "Special-Operation-Decagrammaton/Build-Assets"
LAUNCHER_REPO = "Special-Operation-Decagrammaton/Kei-Launcher"

# Cloudflare R2 Public Development URLs
R2_URL_EN = "https://pub-5015e736aee54dd4a2455d7e23124ea0.r2.dev"     # Public URL for EN bucket (en-ext / en-ori)
R2_URL_PTBR = "https://pub-47a39da16fb849bd811f09ec299bd6e8.r2.dev"   # Public URL for PT-BR bucket (pt-br)

VERSION = "1.3.0"
CONFIG_DIR = Path(Path.home()).joinpath('Kei-Launcher')
CONFIG_PATH = CONFIG_DIR.joinpath('Config.json')
MANIFEST_PATH = CONFIG_DIR.joinpath('Manifest.json')

def get_r2_url(branch_value: str) -> str:
    if branch_value in ["en-ext", "en-ori"]:
        return R2_URL_EN
    elif branch_value == "pt-br":
        return R2_URL_PTBR
    return R2_URL_EN

def get_bundle_source(branch_value: str) -> str:
    if branch_value in ["en-ext", "en-ori"]:
        return "en-bundles"
    elif branch_value == "pt-br":
        return "pt-bundles"
    return branch_value
