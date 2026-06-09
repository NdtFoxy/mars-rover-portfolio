# -*- coding: utf-8 -*-
"""
Aktywne zadanie misji -- wspólne źródło prawdy dla API i agenta.

navigate.py zapisuje wybór do backend/mission_config.json.
Serwer (api.py) i agent czytają stąd, JAKIE zadanie jest aktywne.
Przeładowanie jest JAWNE (reload) -- wywoływane przez Alt+R w run.py
albo przez UE5 (POST /mission/reload). Dzięki temu serwer nie restartuje
się przy każdej zmianie (brak ponownego treningu sieci, brak przerwy dla UE5).
"""
import json
from pathlib import Path
from typing import Any, Dict

CONFIG_PATH = Path(__file__).resolve().parents[2] / "mission_config.json"  # backend/mission_config.json

_DEFAULT: Dict[str, Any] = {
    "selected_task": None,
    "project_number": None,
    "task_title": "Tryb domyślny (pełna symulacja)",
    "algorithm": "A* + sieć CNN + algorytm genetyczny",
    "algorithm_description": "Łazik działa w pełnym trybie gry.",
    "source_pdf": None,
}

_cache: Dict[str, Any] = {"loaded": False, "data": dict(_DEFAULT)}


def get_active_task(force: bool = False) -> Dict[str, Any]:
    """Zwraca aktualnie aktywne zadanie. Czyta plik tylko przy starcie i przy force=True."""
    if force or not _cache["loaded"]:
        try:
            _cache["data"] = json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))
        except Exception:
            _cache["data"] = dict(_DEFAULT)
        _cache["loaded"] = True
    return dict(_cache["data"])


def reload_active_task() -> Dict[str, Any]:
    """Wymusza ponowne wczytanie mission_config.json (Alt+R / POST /mission/reload)."""
    return get_active_task(force=True)


def active_task_summary() -> Dict[str, Any]:
    """Skrót dla JSON-a wysyłanego do Unreal Engine."""
    d = get_active_task()
    return {
        "selected_task": d.get("selected_task"),
        "project_number": d.get("project_number"),
        "task_title": d.get("task_title", "?"),
        "algorithm": d.get("algorithm", "?"),
        "algorithm_description": d.get("algorithm_description", ""),
        "source_pdf": d.get("source_pdf"),
    }
