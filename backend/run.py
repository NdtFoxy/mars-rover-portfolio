# -*- coding: utf-8 -*-
"""
Launcher serwera ARES dla Unreal Engine + przeładowanie zadania (Alt+R).

Przepływ:
  1) terminal A:  python run.py        -> uruchamia serwer (domyślnie szybkie drzewo)
  2) terminal B:  python navigate.py   -> wybierasz zadanie (zapis do mission_config.json)
  3) Navigator automatycznie wywołuje POST /mission/reload.
     Alt+R i przycisk w UE5 pozostają dodatkowymi sposobami przeładowania.
        CNN trenuje się leniwie tylko po wybraniu zadania 6.

API dla Unreal Engine:
  GET  /state            -> pole "mission" = aktywne zadanie
  GET  /mission          -> pełne dane aktywnego zadania
  POST /mission/reload   -> przeładowanie wyboru z navigate.py
"""

import json
import os
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import hot_reload as hr  # katalog skryptu jest w sys.path -> import działa

BACKEND_DIR = Path(__file__).resolve().parent
HOST, PORT = "0.0.0.0", 8000
SERVER_CMD = [sys.executable, "-m", "uvicorn", "app.main:app",
              "--host", HOST, "--port", str(PORT), "--reload"]
RELOAD_URL = f"http://127.0.0.1:{PORT}/mission/reload"


def spawn() -> subprocess.Popen:
    """Uruchamia serwer w osobnej grupie procesów (czysty ubój wraz z dziećmi)."""
    kwargs: dict = {"cwd": str(BACKEND_DIR)}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    return subprocess.Popen(SERVER_CMD, **kwargs)


def terminate(proc: subprocess.Popen | None) -> None:
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
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
            else:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except Exception:
            proc.kill()


def post_reload() -> dict:
    """Każe serwerowi ponownie wczytać wybrane zadanie (POST /mission/reload)."""
    try:
        req = urllib.request.Request(RELOAD_URL, method="POST")
        with urllib.request.urlopen(req, timeout=4) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        return {"error": str(exc)}


def main() -> int:
    print("=" * 64)
    print("  ARES SERVER + przeładowanie zadania (Alt+R)")
    print("=" * 64)
    print(f"[RUN] Start serwera: http://localhost:{PORT}/docs")
    print("[RUN] W drugim terminalu: python navigate.py  (wybierz zadanie)")
    print("[RUN] Wybór w navigate.py jest stosowany automatycznie.")
    print("[RUN] Alt+R tutaj lub POST /mission/reload z UE5 także wymusza przeładowanie.")
    print("[RUN] Wyjście: Ctrl+C")
    print("=" * 64)

    proc = spawn()
    try:
        while True:
            time.sleep(0.4)
            if proc.poll() is not None:
                print("[RUN] Serwer zakończył działanie.")
                break
            try:
                if hr.read_hotkey() in hr.ALT_R_KEYS:
                    res = post_reload()
                    if "error" in res:
                        print(f"[RUN] Alt+R: serwer jeszcze niegotowy ({res['error']})")
                    else:
                        m = res.get("mission", {})
                        print(f"\n[RUN] Alt+R -> aktywne zadanie: "
                              f"#{m.get('project_number')} {m.get('task_title')} | {m.get('algorithm')}\n")
            except Exception:
                pass
    except KeyboardInterrupt:
        print("\n[RUN] Zatrzymywanie serwera...")
        terminate(proc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
