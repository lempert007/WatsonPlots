from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

_TITLE_FONT_SIZE = 18
_BODY_FONT_SIZE = 12
_TITLE_ROW_HEIGHT = 0.12
_BODY_ROW_HEIGHT = 0.08


@dataclass
class Text:
    text: str
    variant: Literal["title", "body"] = "title"

    def _is_body(self) -> bool:
        return self.variant == "body"

    def pdf_font_size(self) -> int:
        return _BODY_FONT_SIZE if self._is_body() else _TITLE_FONT_SIZE

    def pdf_row_height(self) -> float:
        return _BODY_ROW_HEIGHT if self._is_body() else _TITLE_ROW_HEIGHT

    def html_tag(self) -> str:
        if self._is_body():
            return f'<p class="block-text">{self.text}</p>'
        return f'<h2 class="block-title">{self.text}</h2>'

    def __str__(self) -> str:
        return self.text
