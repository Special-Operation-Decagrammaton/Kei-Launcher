from pathlib import Path

from model.config import LauncherConfig
from model.manifest import PatchManifest

def check_new_update(launcher_config: LauncherConfig, old_game_manifest: PatchManifest, new_game_manifest: PatchManifest) -> tuple[str, str]:
    if old_game_manifest is None:
        return "No local manifest found. Update required.", "orange"
    if old_game_manifest.StringVersion != new_game_manifest.StringVersion:
        return f"New version available!", "orange"
    
    old_files_map = {f"{f.FolderPath}/{f.FinalizedFileName}": f for f in old_game_manifest.Files}
    
    for asset in new_game_manifest.Files:
        if launcher_config.GamePath is None or not launcher_config.GamePath.exists():
            return "Please set Game Folder first!", "orange"
        
        full_path_asset = launcher_config.GamePath / asset.FolderPath / asset.FinalizedFileName
        
        if not full_path_asset.exists():
            return f"Missing file: {asset.OriginalFileName}", "orange"
        old_asset = old_files_map.get(f"{asset.FolderPath}/{asset.FinalizedFileName}")
        if not old_asset or old_asset.Hash != asset.Hash:
            return f"Update required for {asset.OriginalFileName}", "orange"

    return "Everything up to date!", "green"

def check_game_executable(game_path: Path) -> bool:
    base = game_path.resolve()
    return (base / "BlueArchive.exe").exists() and (base / "run.bat").exists()