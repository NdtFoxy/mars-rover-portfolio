# -*- coding: utf-8 -*-
"""Config hot-reload scaffold for the Ares neural mission.

This file is intentionally standalone for now. Later it can be imported from
run.py or app.api and connected to the real neural-network task switcher.

Examples:
    python hot_reload.py --once
    python hot_reload.py --watch
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


# Конфиг создается navigate.py и лежит рядом с run.py.
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
    # Отсутствующий конфиг не ошибка: сервер может работать в default режиме.
    if not path.exists():
        return None

    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid config JSON in {path}: {exc}") from exc


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
    # Причина нужна для логов: потом проще понять, что именно поменял navigate.py.
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
        # Бесконечный цикл пока простой polling; later можно заменить на watchdog.
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
    # Неблокирующее чтение клавиатуры: Alt+R работает как ESC+r или Win32 scan-code.
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
    # TODO: здесь потом подключить обновление активного AI-задания без перезапуска.
    task = (event.payload or {}).get("selected_task", "none")
    title = (event.payload or {}).get("task_title", "No task")
    print(f"[HOT-RELOAD] {event.reason}: {event.path}")
    print(f"[HOT-RELOAD] selected_task={task} title={title}")


def on_restart(event: RestartEvent) -> None:
    # TODO: сюда потом подключить настоящий restart AI pipeline или uvicorn process.
    task = (event.payload or {}).get("selected_task", "none")
    title = (event.payload or {}).get("task_title", "No task")
    print("[HOT-RELOAD] Alt+R restart requested")
    print(f"[HOT-RELOAD] selected_task={task} title={title}")

    if event.command is None:
        print("[HOT-RELOAD] no restart command configured; hook executed only")
        return

    print(f"[HOT-RELOAD] running restart command: {event.command}")
    subprocess.Popen(event.command, shell=True)


def print_once(config_path: Path) -> None:
    snapshot = make_snapshot(config_path)
    payload = read_json_config(config_path)

    print("[HOT-RELOAD] config probe")
    print(f"path={config_path}")
    print(f"exists={snapshot.exists}")
    if snapshot.exists:
        print(f"size={snapshot.size}")
        print(f"digest={snapshot.digest}")
        print(f"selected_task={(payload or {}).get('selected_task', 'none')}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mission config hot-reload scaffold.")
    parser.add_argument("--config-path", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--interval", type=float, default=1.0, help="Polling interval in seconds.")
    parser.add_argument("--once", action="store_true", help="Print current config state and exit.")
    parser.add_argument("--watch", action="store_true", help="Watch config changes forever.")
    parser.add_argument("--restart-command", help="Optional shell command executed after Alt+R.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.once:
        print_once(args.config_path)
        return 0

    if args.watch:
        watcher = MissionConfigWatcher(args.config_path, args.interval)
        print(f"[HOT-RELOAD] watching {args.config_path} every {args.interval:.2f}s")
        print("[HOT-RELOAD] press Alt+R to request restart")
        watcher.watch_forever(on_reload, on_restart, restart_command=args.restart_command)
        return 0

    print("Use --once to probe config or --watch to start the scaffold watcher. Alt+R works in --watch mode.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
