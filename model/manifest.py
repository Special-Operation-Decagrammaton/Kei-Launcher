from pathlib import Path
from pydantic import BaseModel
from typing import List, Optional

class PatchFileInfo(BaseModel):
    OriginalFileName: str
    FinalizedFileName: str
    OriginalDownloadUrl: str
    FolderPath: str
    Hash: Optional[int] = 0

class PatchManifest(BaseModel):
    PatchNote: Optional[str] = None
    UpdateDate: Optional[str] = None
    StringVersion: Optional[str] = None
    Files: List[PatchFileInfo]
    
def load_manifest_memory(content: bytes) -> PatchManifest:
    return PatchManifest.model_validate_json(content)

def load_manifest(file_path: Path) -> PatchManifest:
    return PatchManifest.model_validate_json(file_path.read_text())

def save_manifest(config: PatchManifest, file_path: Path) -> None:
    json_data = config.model_dump_json(indent=4)
    file_path.write_text(json_data)