# tools/acta_draft_store.py
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Optional

from .storage import JsonStore


class ActaDraftStore(JsonStore):
    def __init__(self):
        env_root = os.environ.get("MCP_DATA_DIR")
        root = Path(env_root) if env_root else Path(tempfile.gettempdir())
        super().__init__(root / "mcp_data" / "acta_drafts.json")

    def save_acta(self, acta_id: str, acta_payload: dict) -> None:
        self.set(acta_id, acta_payload)

    def get_acta(self, acta_id: str) -> Optional[dict]:
        return self.get(acta_id)