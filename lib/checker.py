from pathlib import Path

from model.config import LauncherConfig
from model.manifest import GameManifest

def check_new_update(launcher_config: LauncherConfig, old_game_manifest: GameManifest, new_game_manifest: GameManifest) -> tuple[str, str]:
    if old_game_manifest is None:
        return "No local manifest found. Update required.", "orange"
    if old_game_manifest.StringVersion != new_game_manifest.StringVersion:
        return f"New version {new_game_manifest.StringVersion} available!", "orange"
    
    old_files_map = {f.Path: f for f in old_game_manifest.Files}
    
    for asset in new_game_manifest.Files:
        if launcher_config.GamePath is None or not launcher_config.GamePath.exists():
            return "Please set Game Folder first!", "orange"
        
        full_path_asset = launcher_config.GamePath / asset.Path
        
        if not full_path_asset.exists():
            return f"Missing file: {asset.OriginalFileName}", "orange"
        old_asset = old_files_map.get(asset.Path)
        if not old_asset or old_asset.Hash != asset.Hash:
            return f"Update required for {asset.OriginalFileName}", "orange"

    return "Everything up to date!", "green"

def check_game_executable(game_path: Path) -> bool:
    base = game_path.resolve()
    return (base / "BlueArchive.exe").exists() and (base / "run.bat").exists()