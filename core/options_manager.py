import os
import json
from typing import Callable, Dict, List, Any

class OptionsManager:
    def __init__(self):
        self.settings_file = "gvpa_settings.json"
        self._settings: Dict[str, Any] = {
            "theme": "Nord",
            "visual_style": "minimal",
            "language": "English",
            "auto_analyze": True,
            "max_recursion_depth": 10,
            "show_minimap": False,
            "infinite_canvas": True,
            "min_spacing": 30,
            "number_decimals": 2,
            "thousand_sep": True
        }
        self._observers: List[Callable[[Dict[str, Any]], None]] = []
        self._undo_stack: List[Dict[str, Any]] = []
        self._redo_stack: List[Dict[str, Any]] = []
        self.load()

    @property
    def settings(self) -> Dict[str, Any]:
        return dict(self._settings)

    def add_observer(self, cb: Callable[[Dict[str, Any]], None]) -> None:
        if cb not in self._observers:
            self._observers.append(cb)

    def remove_observer(self, cb: Callable[[Dict[str, Any]], None]) -> None:
        if cb in self._observers:
            self._observers.remove(cb)

    def _notify(self) -> None:
        for cb in self._observers:
            try:
                cb(self.settings)
            except Exception:
                # Observers should never crash app
                pass

    def set_option(self, key: str, value: Any) -> None:
        prev = self.settings
        self._undo_stack.append(prev)
        self._redo_stack.clear()
        self._settings[key] = value
        self.save()
        self._notify()

    def undo(self) -> None:
        if not self._undo_stack:
            return
        current = self.settings
        prev = self._undo_stack.pop()
        self._redo_stack.append(current)
        self._settings = prev
        self.save()
        self._notify()

    def redo(self) -> None:
        if not self._redo_stack:
            return
        current = self.settings
        nxt = self._redo_stack.pop()
        self._undo_stack.append(current)
        self._settings = nxt
        self.save()
        self._notify()

    def load(self) -> None:
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    self._settings.update(data)
            except Exception:
                # Ignore invalid file contents
                pass

    def save(self) -> None:
        try:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=2)
        except Exception:
            # Ignore saving errors to prevent crash
            pass

options_manager = OptionsManager()
