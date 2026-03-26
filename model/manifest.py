from pathlib import Path
from pydantic import BaseModel
from typing import List, Optional

class GameFileInfo(BaseModel):
    OriginalFileName: str
    Path: str
    Hash: Optional[int] = 0

class GameManifest(BaseModel):
    PatchNote: Optional[str] = None
    UpdateDate: Optional[str] = None
    StringVersion: Optional[str] = None
    Files: List[GameFileInfo]
    
def load_manifest_memory(content: bytes) -> GameManifest:
    return GameManifest.model_validate_json(content)

def load_manifest(file_path: Path) -> GameManifest:
    return GameManifest.model_validate_json(file_path.read_text())

def save_manifest(config: GameManifest, file_path: Path) -> None:
    json_data = config.model_dump_json(indent=4)
    file_path.write_text(json_data)