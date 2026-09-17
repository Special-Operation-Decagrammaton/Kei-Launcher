import json, os, datetime
from pathlib import Path
from pydantic import BaseModel
from typing import List, Optional, Union, Any

class PatchFileInfo(BaseModel):
    OriginalFileName: str
    FinalizedFileName: str
    OriginalDownloadUrl: Optional[str] = ""
    FolderPath: str
    Hash: Optional[Any] = 0
    Size: Optional[int] = 0
    DownloadKey: Optional[str] = ""

class PatchManifest(BaseModel):
    PatchNote: Optional[str] = None
    UpdateDate: Optional[str] = None
    StringVersion: Optional[str] = None
    Type: Optional[str] = None
    TotalImages: Optional[int] = 0
    TotalBundles: Optional[int] = 0
    ZipFile: Optional[str] = ""
    ZipSize: Optional[int] = 0
    ZipHash: Optional[str] = ""
    Files: Optional[List[PatchFileInfo]] = []
    
def load_manifest_memory(content: bytes) -> PatchManifest:
    try:
        data = json.loads(content.decode("utf-8"))
        if isinstance(data, dict):
            if "Files" in data:
                return PatchManifest.model_validate(data)
            elif "files" in data:
                files_list = []
                for rel_path, file_info in data.get("files", {}).items():
                    fn = os.path.basename(rel_path)
                    dirname = os.path.dirname(rel_path).replace("\\", "/")
                    folder_path = f"BlueArchive_Data/StreamingAssets/{dirname}" if dirname else "BlueArchive_Data/StreamingAssets"
                    files_list.append(PatchFileInfo(
                        OriginalFileName=fn,
                        FinalizedFileName=fn,
                        OriginalDownloadUrl="",
                        FolderPath=folder_path,
                        Hash=file_info.get("sha256", 0),
                        Size=file_info.get("size", 0),
                        DownloadKey=file_info.get("key", rel_path)
                    ))
                up_ts = data.get("updated_at", 0)
                up_date = datetime.datetime.fromtimestamp(up_ts).strftime("%Y-%m-%d %H:%M:%S") if up_ts else ""
                return PatchManifest(
                    PatchNote="Cloudflare R2 Patch",
                    UpdateDate=up_date,
                    StringVersion="1.0.0",
                    Files=files_list
                )
            else:
                return PatchManifest.model_validate(data)
    except Exception:
        pass
    return PatchManifest.model_validate_json(content)

def load_manifest(file_path: Path) -> PatchManifest:
    return load_manifest_memory(file_path.read_bytes())

def save_manifest(config: PatchManifest, file_path: Path) -> None:
    json_data = config.model_dump_json(indent=4)
    file_path.write_text(json_data, encoding="utf-8")