from typing import Dict, List, Optional
from pydantic import BaseModel, Field
import hashlib

class File(BaseModel):
    name: str
    content: str
    metadata: Dict[str, str] = Field(default_factory=dict)

class VFS:
    def __init__(self):
        self._files: Dict[str, File] = {}

    def list_files(self) -> List[str]:
        """Returns a list of filenames in the VFS."""
        return list(self._files.keys())

    def read_file(self, filename: str) -> str:
        """Reads the content of a file."""
        if filename not in self._files:
            raise FileNotFoundError(f"File {filename} not found in VFS.")
        return self._files[filename].content

    def write_file(self, filename: str, content: str, metadata: Optional[Dict[str, str]] = None):
        """Writes content to a file. Overwrites if exists."""
        if metadata is None:
            metadata = {}
        self._files[filename] = File(name=filename, content=content, metadata=metadata)

    def exists(self, filename: str) -> bool:
        """Checks if a file exists."""
        return filename in self._files

    def get_file(self, filename: str) -> File:
        """Returns the File object (including metadata)."""
        if filename not in self._files:
            raise FileNotFoundError(f"File {filename} not found in VFS.")
        return self._files[filename]
