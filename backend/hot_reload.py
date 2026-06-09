# -*- coding: utf-8 -*-
"""Obserwator `mission_config.json` do przeładowania aktywnego zadania.
Наблюдатель `mission_config.json` для обновления активного задания.

Moduł działa samodzielnie, ale może też być podpięty do `run.py` albo
`app.api`. Dzięki temu wybór z `navigate.py` można odświeżyć bez restartu.
Модуль работает автономnie, ale może być też podpięty do `run.py` lub
`app.api`. Dzięki temu wybór z `navigate.py` można odświeżyć bez restartu.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


# Konfiguracja jest tworzona przez `navigate.py` i leży obok `run.py`.
# Конфигурацию tworzy `navigate.py`, a plik leży obok `run.py`.
DEFAULT_CONFIG_PATH = Path(__file__).with_name("mission_config.json")
ALT_R_KEYS = {"alt+r"}


@dataclass(frozen=True)
class ConfigSnapshot:
    path: Path
    exists: bool
    mtime_ns: int | None = None
    size: int | None = None
    digest: str | None = None


@dataclass(frozen=True)
class HotReloadEvent:
    path: Path
    previous: ConfigSnapshot
    current: ConfigSnapshot
    payload: dict | None
    reason: str


@dataclass(frozen=True)
class RestartEvent:
    path: Path
    payload: dict | None
    reason: str = "manual_alt_r"
    command: str | None = None


def read_json_config(path: Path) -> dict | None:
    # Brak pliku konfiguracyjnego nie jest błędem: serwer może działać w trybie domyślnym.
    # Отсутствие pliku konfiguracyjnego nie jest błędem: serwer może działać w trybie domyślnym.
    if not path.exists():
        return None

    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Nieprawidłowy JSON konfiguracyjny w {path}: {exc}") from exc


def make_snapshot(path: Path) -> ConfigSnapshot:
    if not path.exists():
        return ConfigSnapshot(path=path, exists=False)

    raw = path.read_bytes()
    stat = path.stat()
    return ConfigSnapshot(
        path=path,
        exists=True,
        mtime_ns=stat.st_mtime_ns,
        size=stat.st_size,
        digest=hashlib.sha256(raw).hexdigest(),
    )


def describe_change(previous: ConfigSnapshot, current: ConfigSnapshot) -> str:
    # Powód zapisujemy do logów, żeby łatwiej było ustalić, co zmienił navigate.py.
    # Powód zapisujemy w logach, żeby łatwiej było zobaczyć, co zmienił navigate.py.
    if not previous.exists and current.exists:
        return "created"
    if previous.exists and not current.exists:
        return "deleted"
    if previous.digest != current.digest:
        return "content_changed"
    if previous.mtime_ns != current.mtime_ns:
        return "timestamp_changed"
    return "unchanged"


class MissionConfigWatcher:
    def __init__(self, config_path: Path = DEFAULT_CONFIG_PATH, poll_interval: float = 1.0):
        self.config_path = config_path
        self.poll_interval = poll_interval
        self._snapshot = make_snapshot(config_path)

    @property
    def snapshot(self) -> ConfigSnapshot:
        return self._snapshot

    def poll(self) -> HotReloadEvent | None:
        current = make_snapshot(self.config_path)
        reason = describe_change(self._snapshot, current)

        if reason == "unchanged":
            return None

        previous = self._snapshot
        self._snapshot = current
        payload = read_json_config(self.config_path) if current.exists else None
        return HotReloadEvent(
            path=self.config_path,
            previous=previous,
            current=current,
            payload=payload,
            reason=reason,
        )

    def watch_forever(
        self,
        on_reload: Callable[[HotReloadEvent], None],
        on_restart: Callable[[RestartEvent], None],
        restart_command: str | None = None,
    ) -> None:
        # Na razie prosty polling.
        # Сейчас zwykłe odpytywanie w pętli.
        # Później можно to podmienić na watchdog.
        while True:
            event = self.poll()
            if event is not None:
                on_reload(event)
            if read_hotkey() in ALT_R_KEYS:
                payload = read_json_config(self.config_path)
                on_restart(
                    RestartEvent(
                        path=self.config_path,
                        payload=payload,
                        command=restart_command,
                    )
                )
            time.sleep(self.poll_interval)


def read_hotkey() -> str | None:
    # Czytanie klawiatury bez blokowania.
    # Неблокирующее czytanie klawiatury.
    # Alt+R działa jako ESC+r albo kod Windows.
    if os.name == "nt":
        import msvcrt

        if not msvcrt.kbhit():
            return None

        char = msvcrt.getwch()
        if char in ("\x00", "\xe0"):
            code = msvcrt.getwch()
            if code in ("r", "R", "\x13"):
                return "alt+r"
            return None
        if char == "\x1b" and msvcrt.kbhit():
            code = msvcrt.getwch()
            if code.lower() == "r":
                return "alt+r"
        return None

    import select
    import termios
    import tty

    if not select.select([sys.stdin], [], [], 0)[0]:
        return None

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        char = sys.stdin.read(1)
        if char == "\x1b" and select.select([sys.stdin], [], [], 0.01)[0]:
            code = sys.stdin.read(1)
            if code.lower() == "r":
                return "alt+r"
        return None
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def on_reload(event: HotReloadEvent) -> None:
    # Tu logujemy zmianę aktywnego zadania.
    # Здесь logujemy zmianę aktywnego zadania.
    # Później можно dodać automatyczne odświeżenie stanu.
    task = (event.payload or {}).get("selected_task", "none")
    title = (event.payload or {}).get("task_title", "No task")
    print(f"[HOT-RELOAD] {event.reason}: {event.path}")
    print(f"[HOT-RELOAD] selected_task={task} title={title}")


def on_restart(event: RestartEvent) -> None:
    # Tu uruchamiamy restart.
    # Tutaj uruchamiamy restart.
    # Później можно podpiąć pełny restart procesu `uvicorn`.
    task = (event.payload or {}).get("selected_task", "none")
    title = (event.payload or {}).get("task_title", "No task")
    print("[HOT-RELOAD] zgłoszono restart przez Alt+R")
    print(f"[HOT-RELOAD] selected_task={task} title={title}")

    if event.command is None:
        print("[HOT-RELOAD] nie ustawiono komendy restartu; wykonano tylko hook")
        return

    print(f"[HOT-RELOAD] uruchamianie komendy restartu: {event.command}")
    subprocess.Popen(event.command, shell=True)


def print_once(config_path: Path) -> None:
    snapshot = make_snapshot(config_path)
    payload = read_json_config(config_path)

    print("[HOT-RELOAD] podgląd konfiguracji")
    print(f"path={config_path}")
    print(f"exists={snapshot.exists}")
    if snapshot.exists:
        print(f"size={snapshot.size}")
        print(f"digest={snapshot.digest}")
        print(f"selected_task={(payload or {}).get('selected_task', 'none')}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Narzędzie do przeładowania konfiguracji misji / Инструмент перезагрузки конфигурации миссии.")
    parser.add_argument("--config-path", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--interval", type=float, default=1.0, help="Odstęp odpytywania w sekundach / Интервал опроса в секундах.")
    parser.add_argument("--once", action="store_true", help="Pokaż stan konfiguracji i zakończ / Показать состояние конфигурации и выйти.")
    parser.add_argument("--watch", action="store_true", help="Obserwuj zmiany konfiguracji w pętli / Наблюдать изменения конфигурации в цикле.")
    parser.add_argument("--restart-command", help="Opcjonalna komenda powłoki po Alt+R / Необязательная команда оболочки после Alt+R.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.once:
        print_once(args.config_path)
        return 0

    if args.watch:
        watcher = MissionConfigWatcher(args.config_path, args.interval)
        print(f"[HOT-RELOAD] obserwowanie {args.config_path} co {args.interval:.2f}s")
        print("[HOT-RELOAD] naciśnij Alt+R, aby poprosić o restart")
        watcher.watch_forever(on_reload, on_restart, restart_command=args.restart_command)
        return 0

    print("Użyj `--once`, aby podejrzeć konfigurację, albo `--watch`, aby uruchomić obserwator.")
    print("Используй `--once`, чтобы посмотреть конфигурацию, или `--watch`, чтобы запустить наблюдатель.")
    print("Alt+R działa w trybie `--watch` / Alt+R działa w trybie `--watch`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
