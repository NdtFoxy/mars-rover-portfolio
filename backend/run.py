import json
from pathlib import Path

import uvicorn


CONFIG_PATH = Path(__file__).with_name("mission_config.json")


def load_mission_config(config_path: Path = CONFIG_PATH) -> dict | None:
    # Конфиг необязательный: если навигатор еще не запускали, сервер стартует как раньше.
    if not config_path.exists():
        return None

    try:
        return json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid mission config: {config_path} ({exc})") from exc


def print_selected_task(config: dict | None) -> None:
    # Пока это только точка подключения: позже app.api сможет читать эти настройки глубже.
    if config is None:
        print("[NAVIGATE] No mission_config.json found. Starting with default server mode.")
        return

    selected_task = config.get("selected_task", "unknown")
    task_title = config.get("task_title", "Unknown task")
    print(f"[NAVIGATE] Selected task: {selected_task} ({task_title})")
    print("[NAVIGATE] Config is loaded at startup. Restart run.py to apply another task.")


if __name__ == "__main__":
    print_selected_task(load_mission_config())
    # Эта команда говорит: "Запусти веб-сервер uvicorn"
    # "app.main:app" - значит: "внутри папки 'app' найди файл 'main' и в нем объект 'app'"
    # host="0.0.0.0" - чтобы сервер был доступен с других устройств в сети (полезно для Артема)
    # port=8000 - порт, на котором будет работать сервер
    # reload=True - СУПЕР-ФИЧА: сервер будет автоматически перезапускаться при каждом сохранении кода.
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
