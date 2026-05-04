from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum

class Language(Enum):
    EN = "en"

class Branch(Enum):
    NONE = "none"
    EN_ORI = "en-ori"
    EN_EXT = "en-ext"
    PT_BR = "pt-br"
    
    @classmethod
    def list_values(cls):
        return [member.value for member in cls]

class LauncherConfig(BaseModel):
    GamePath: Optional[Path] = Field(default=None)
    Language: Language
    Branch: Branch
    CloseOnLaunch: Optional[bool] = True
    
def load_config(file_path: Path) -> LauncherConfig:
    return LauncherConfig.model_validate_json(file_path.read_text())

def save_config(config: LauncherConfig, file_path: Path) -> None:
    json_data = config.model_dump_json(indent=4)
    file_path.write_text(json_data)