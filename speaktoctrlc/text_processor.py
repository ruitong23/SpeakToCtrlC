from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class ProcessedText:
    latest: str
    history: str
    should_copy: bool


@dataclass
class TextProcessor:
    append_history: bool = True
    auto_copy: bool = True
    _last_text: str = ""
    _history_items: List[str] = field(default_factory=list)

    def process(self, raw_text: str) -> ProcessedText:
        text = " ".join(raw_text.strip().split())
        if not text:
            return ProcessedText(latest="", history="\n".join(self._history_items), should_copy=False)
        if text == self._last_text:
            return ProcessedText(latest=self._last_text, history="\n".join(self._history_items), should_copy=False)

        self._last_text = text
        if self.append_history:
            self._history_items.append(text)
        return ProcessedText(
            latest=text,
            history="\n".join(self._history_items),
            should_copy=self.auto_copy,
        )

    def clear(self) -> None:
        self._last_text = ""
        self._history_items.clear()

    def full_text(self) -> str:
        return "\n".join(self._history_items)
