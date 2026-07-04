from __future__ import annotations

import re
from typing import Optional, Union

from .llm_service import LLMService
from .schemas import ActaFormData, ActaSession, Draft
from .storage import DraftStore


class DraftManager:
    def __init__(self):
        self.store = DraftStore()
        self.llm = LLMService()

    def create_draft(self, data: Union[ActaFormData, ActaSession], context: Optional[str] = None) -> Draft:
        form_data = data.data if isinstance(data, ActaSession) else data
        markdown = self.llm.generate_markdown_draft(form_data, context)
        session_id = data.session_id if isinstance(data, ActaSession) else None
        draft = Draft(session_id=session_id, draft_markdown=markdown)
        self.store.save_draft(draft)
        return draft

    def get_draft(self, draft_id: str) -> Optional[Draft]:
        return self.store.get_draft(draft_id)

    def update_draft(self, draft_id: str, instruction: str) -> Optional[Draft]:
        draft = self.get_draft(draft_id)
        if draft is None:
            return None
        if draft.status == "approved":
            return draft

        updated_markdown = self._apply_instruction(draft.draft_markdown, instruction)
        draft.draft_markdown = updated_markdown
        draft.touch()
        self.store.save_draft(draft)
        return draft

    def approve_draft(self, draft_id: str) -> Optional[Draft]:
        draft = self.get_draft(draft_id)
        if draft is None:
            return None
        if draft.status != "approved":
            draft.approve()
            self.store.save_draft(draft)
        return draft

    @staticmethod
    def _apply_instruction(markdown: str, instruction: str) -> str:
        lower = instruction.lower()
        if "reemplazar" in lower or "replace" in lower:
            match = re.search(r"[Rr]eemplazar\s+[\"'](.+?)[\"']\s+(?:por|with)\s+[\"'](.+?)[\"']", instruction)
            if match:
                old_text, new_text = match.groups()
                return markdown.replace(old_text, new_text)

        if "eliminar" in lower or "remove" in lower or "borrar" in lower:
            phrase = instruction.split(" ")[-1].strip('"\'')
            if phrase:
                return "\n".join(line for line in markdown.splitlines() if phrase not in line)

        if "agregar" in lower or "add" in lower or "append" in lower:
            return markdown.rstrip() + "\n\n" + instruction.strip()

        if "modificar" in lower or "modify" in lower:
            return markdown.rstrip() + "\n\n" + instruction.strip()

        return markdown.rstrip() + "\n\n" + instruction.strip()
