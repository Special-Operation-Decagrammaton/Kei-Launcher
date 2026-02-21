from pathlib import Path
from pydantic import BaseModel
from typing import List

class GameFileInfo(BaseModel):
    OriginalFileName: str
    Path: str
    Hash: int

class GameManifest(BaseModel):
    StringVersion: str
    Files: List[GameFileInfo]
    
def load_manifest_memory(content: bytes) -> GameManifest:
    return GameManifest.model_validate_json(content)

def load_manifest(file_path: Path) -> GameManifest:
    return GameManifest.model_validate_json(file_path.read_text())

def save_manifest(config: GameManifest, file_path: Path) -> None:
    json_data = config.model_dump_json(indent=4)
    file_path.write_text(json_data)