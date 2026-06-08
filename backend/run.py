# -*- coding: utf-8 -*-
"""
Launcher + nadzorca (supervisor) misji ARES.

Czyta wybór zadania z mission_config.json (zapisywany przez navigate.py),
uruchamia odpowiednią komendę i OBSERWUJE konfig: gdy zmienisz zadanie w
navigate.py, ten proces automatycznie restartuje się na nowe zadanie
(hot-reload). Działa też ręczny restart klawiszem Alt+R.

Uruchomienie (z katalogu backend/):
    python run.py              # nadzorca + hot-reload (domyślnie)
    python run.py --once       # uruchom raz, bez obserwowania konfigu
"""

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

# hot_reload.py leży obok -- katalog skryptu jest automatycznie w sys.path.
import hot_reload as hr

BACKEND_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BACKEND_DIR / "mission_config.json"

# Serwer FastAPI obsługuje zadania "na żywo" (wyszukiwanie + sieć neuronowa).
SERVER_CMD = [sys.executable, "-m", "uvicorn", "app.main:app",
              "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Mapowanie wybranego zadania -> komenda do uruchomienia (z katalogu backend/).
TASK_COMMANDS = {
    "project-3-uninformed-search": SERVER_CMD,
    "project-4-informed-search":   SERVER_CMD,
    "project-6-neural-networks":   SERVER_CMD,
    "project-5-decision-trees":    [sys.executable, "-m", "app.core.decision_tree_agent"],
    "project-7-genetic-algorithms": [sys.executable, "demo_genetyczny.py"],
}


def command_for(config: dict | None) -> list[str]:
    task = (config or {}).get("selected_task")
    return TASK_COMMANDS.get(task, SERVER_CMD)


def describe(config: dict | None) -> str:
    if not config:
        return "domyślne (serwer CNN) — brak mission_config.json"
    return f"{config.get('selected_task', '?')} — {config.get('task_title', '?')}"


def spawn(cmd: list[str]) -> subprocess.Popen:
    """Uruchamia komendę jako podproces we własnej grupie procesów (by dało się ją czysto ubić)."""
    kwargs: dict = {"cwd": str(BACKEND_DIR)}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True  # własna sesja => os.killpg ubije też dzieci (reloader uvicorna)
    return subprocess.Popen(cmd, **kwargs)


def terminate(proc: subprocess.Popen | None) -> None:
    """Czysto kończy podproces wraz z jego dziećmi (np. workerem uvicorna)."""
    if proc is None or proc.poll() is not None:
        return
    try:
        if os.name == "nt":
            proc.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except Exception:
        proc.terminate()
    try:
        proc.wait(timeout=8)
    except subprocess.TimeoutExpired:
        try:
            if os.name == "nt":
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                               capture_output=True)
            else:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except Exception:
            proc.kill()


def banner(config: dict | None) -> None:
    print("=" * 64)
    print("  ARES MISSION LAUNCHER (supervisor + hot-reload)")
    print("=" * 64)
    print(f"[RUN] Zadanie: {describe(config)}")
    print(f"[RUN] Komenda: {' '.join(command_for(config))}")
    print("[RUN] Zmień zadanie w navigate.py -> nastąpi auto-restart.")
    print("[RUN] Ręczny restart: Alt+R   |   Wyjście: Ctrl+C")
    print("=" * 64)


def main() -> int:
    parser = argparse.ArgumentParser(description="ARES launcher / hot-reload supervisor.")
    parser.add_argument("--once", action="store_true",
                        help="Uruchom wybrane zadanie raz, bez obserwowania konfigu.")
    parser.add_argument("--interval", type=float, default=1.0,
                        help="Częstotliwość sprawdzania konfigu (s).")
    args = parser.parse_args()

    config = hr.read_json_config(CONFIG_PATH)
    banner(config)

    cmd = command_for(config)
    proc = spawn(cmd)

    # Tryb --once: po prostu czekamy aż zadanie się skończy (bez hot-reloadu).
    if args.once:
        try:
            proc.wait()
        except KeyboardInterrupt:
            terminate(proc)
        return 0

    watcher = hr.MissionConfigWatcher(CONFIG_PATH, poll_interval=args.interval)

    try:
        while True:
            time.sleep(args.interval)

            restart_reason: str | None = None

            event = watcher.poll()
            if event is not None and event.reason != "unchanged":
                config = event.payload
                restart_reason = f"konfig: {event.reason}"

            # Ręczny restart Alt+R (nieblokujący; błędy ignorujemy, by nie zabić nadzorcy)
            try:
                if hr.read_hotkey() in hr.ALT_R_KEYS:
                    config = hr.read_json_config(CONFIG_PATH)
                    restart_reason = "Alt+R"
            except Exception:
                pass

            if restart_reason:
                print(f"\n[RUN] RESTART ({restart_reason}) -> {describe(config)}")
                terminate(proc)
                cmd = command_for(config)
                proc = spawn(cmd)
                print(f"[RUN] Uruchomiono: {' '.join(cmd)}\n")
            elif proc.poll() is not None:
                # Zadanie jednorazowe (np. demo GA / drzewo decyzyjne) zakończyło się.
                # Nie restartujemy w kółko -- czekamy na zmianę konfigu.
                pass

    except KeyboardInterrupt:
        print("\n[RUN] Zatrzymywanie...")
        terminate(proc)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
