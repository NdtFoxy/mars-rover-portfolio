# -*- coding: utf-8 -*-
"""Rich CLI navigator for future neural-network tasks.

Run from the backend folder:
    python navigate.py

For a non-interactive preview:
    python navigate.py --preview
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable

try:
    from rich import box
    from rich.align import Align
    from rich.console import Console, Group
    from rich.panel import Panel
    from rich.prompt import Confirm, IntPrompt, Prompt
    from rich.table import Table
    from rich.text import Text
except ImportError as exc:  # pragma: no cover - полезно, если Rich еще не установлен.
    raise SystemExit(
        "Rich is required for navigate.py. Install it with: pip install rich"
    ) from exc


# Конфиг лежит рядом с backend/run.py, чтобы сервер мог читать его при старте.
DEFAULT_CONFIG_PATH = Path(__file__).with_name("mission_config.json")


@dataclass(frozen=True)
class TaskSpec:
    key: str
    project_number: int
    title: str
    description: str
    algorithm: str
    algorithm_description: str
    source_pdf: str
    planned_command: str
    accent: str
    future_settings: tuple[str, ...] = ()


@dataclass
class NavigatorSettings:
    model_name: str = "cnn_mlp_v1"
    endpoint: str = "http://127.0.0.1:8000"
    max_steps: int = 25
    dry_run: bool = True
    auto_open_dashboard: bool = False
    notes: list[str] = field(default_factory=list)


# Эти режимы соответствуют темам проектных заданий из PDF.
TASKS: tuple[TaskSpec, ...] = (
    TaskSpec(
        key="project-3-uninformed-search",
        project_number=3,
        title="Zadanie projektowe 3: Niepoinformowane strategie przeszukiwania",
        description="Route planning without a heuristic estimate of the goal.",
        algorithm="Breadth-First Search (BFS)",
        algorithm_description="Explores the map level by level and finds the shortest path on an unweighted grid.",
        source_pdf="route-planning (1).pdf",
        planned_command="python run.py --mode project-3-uninformed-search",
        accent="blue",
        future_settings=("algorithm", "start_cell", "goal_cell", "grid_size"),
    ),
    TaskSpec(
        key="project-4-informed-search",
        project_number=4,
        title="Zadanie projektowe 4: Poinformowane strategie przeszukiwania",
        description="Route planning with a heuristic estimate of distance to the target.",
        algorithm="A* Search",
        algorithm_description="Uses path cost plus a heuristic, for example Manhattan distance, to guide the rover faster.",
        source_pdf="route-planning-2.pdf",
        planned_command="python run.py --mode project-4-informed-search",
        accent="green",
        future_settings=("heuristic", "priority_weight", "terrain_costs", "goal_cell"),
    ),
    TaskSpec(
        key="project-5-decision-trees",
        project_number=5,
        title="Zadanie projektowe 5: Drzewa decyzyjne",
        description="Interpretable decisions based on telemetry and environment features.",
        algorithm="Decision Tree (CART)",
        algorithm_description="Splits telemetry into readable rules, useful for explaining rover decisions.",
        source_pdf="decision-trees.pdf",
        planned_command="python -m app.core.decision_tree_agent",
        accent="magenta",
        future_settings=("dataset_path", "criterion", "max_depth", "export_tree_png"),
    ),
    TaskSpec(
        key="project-6-neural-networks",
        project_number=6,
        title="Zadanie projektowe 6: Sieci neuronowe",
        description="Neural decisions using camera frames and rover telemetry input.",
        algorithm="CNN + MLP Neural Network",
        algorithm_description="Combines image features from CNN with tabular telemetry processed by MLP.",
        source_pdf="neural-networks (1).pdf",
        planned_command="python -m app.api --mode project-6-neural-networks",
        accent="cyan",
        future_settings=("epochs", "learning_rate", "batch_size", "model_path"),
    ),
    TaskSpec(
        key="project-7-genetic-algorithms",
        project_number=7,
        title="Zadanie projektowe 7: Algorytmy genetyczne",
        description="Optimization mode for mineral selection and parameter tuning.",
        algorithm="Genetic Algorithm (GA)",
        algorithm_description="Evolves candidate solutions through selection, crossover, and mutation.",
        source_pdf="genetic-algorithms.pdf",
        planned_command="python demo_genetyczny.py",
        accent="yellow",
        future_settings=("population_size", "generations", "mutation_rate", "capacity"),
    ),
)


def build_header() -> Panel:
    title = Text("ARES NEURAL NAVIGATOR", style="bold cyan")
    subtitle = Text("AI task launcher | config-first placeholder mode", style="white")
    body = Group(Align.center(title), Align.center(subtitle))
    return Panel(body, border_style="cyan", box=box.ASCII, padding=(1, 2))


def load_active_task_key(config_path: Path) -> str | None:
    # Навигатор только читает выбранный режим; если JSON битый, считаем что активного нет.
    if not config_path.exists():
        return None

    try:
        payload = json.loads(config_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return None

    selected_task = payload.get("selected_task")
    return selected_task if isinstance(selected_task, str) else None


def build_task_table(tasks: Iterable[TaskSpec], selected_index: int, active_task_key: str | None) -> Table:
    table = Table(
        title="Course Mode Selection",
        box=box.ASCII,
        border_style="bright_black",
        header_style="bold white",
        expand=True,
    )
    table.add_column("", justify="center", no_wrap=True)
    table.add_column("Nr", justify="center", no_wrap=True)
    table.add_column("Temat", style="bold")
    table.add_column("Algorithm", style="cyan")
    table.add_column("Config", justify="center", no_wrap=True)

    for index, task in enumerate(tasks, start=1):
        is_selected = index - 1 == selected_index
        is_active = task.key == active_task_key
        marker = ">" if is_selected else " "
        row_style = f"bold {task.accent}" if is_selected else None
        config_state = Text("ACTIVE", style="bold green") if is_active else Text("-", style="bright_black")
        table.add_row(
            marker,
            f"{task.project_number}",
            Text(task.title, style=task.accent),
            task.algorithm,
            config_state,
            style=row_style,
        )
    return table


def build_settings_panel(settings: NavigatorSettings) -> Panel:
    grid = Table.grid(padding=(0, 1))
    grid.add_column(style="bold white", no_wrap=True)
    grid.add_column(style="cyan")
    grid.add_row("Model", settings.model_name)
    grid.add_row("API endpoint", settings.endpoint)
    grid.add_row("Mission steps", str(settings.max_steps))
    grid.add_row("Dry-run", "ON" if settings.dry_run else "OFF")
    grid.add_row("Dashboard", "auto-open" if settings.auto_open_dashboard else "manual")

    return Panel(
        grid,
        title="Future Launch Settings",
        border_style="green",
        box=box.ASCII,
        padding=(1, 2),
    )


def build_config_payload(task: TaskSpec, settings: NavigatorSettings) -> dict:
    # Этот JSON специально простой: run.py сможет читать его без импорта navigate.py.
    return {
        "schema_version": 1,
        "generated_by": "navigate.py",
        "selected_task": task.key,
        "project_number": task.project_number,
        "task_title": task.title,
        "algorithm": task.algorithm,
        "algorithm_description": task.algorithm_description,
        "source_pdf": task.source_pdf,
        "planned_command": task.planned_command,
        "restart_required": True,
        "settings": asdict(settings),
        "future_settings": list(task.future_settings),
    }


def write_config(task: TaskSpec, settings: NavigatorSettings, config_path: Path) -> Path:
    # Навигатор только сохраняет выбор; реальный запуск подключим позже отдельно.
    payload = build_config_payload(task, settings)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return config_path


def build_task_details(
    task: TaskSpec,
    settings: NavigatorSettings,
    config_path: Path,
    saved_path: Path | None = None,
) -> Panel:
    settings_list = ", ".join(task.future_settings) if task.future_settings else "none yet"

    details = Table.grid(padding=(0, 1))
    details.add_column(style="bold white", no_wrap=True)
    details.add_column()
    details.add_row("Project", f"#{task.project_number}")
    details.add_row("Temat", Text(task.title, style=f"bold {task.accent}"))
    details.add_row("Algorithm", Text(task.algorithm, style="bold cyan"))
    details.add_row("Short idea", task.algorithm_description)
    details.add_row("Description", task.description)
    details.add_row("Source PDF", Text(task.source_pdf, style="bright_black"))
    details.add_row("Command", Text(task.planned_command, style="cyan"))
    details.add_row("Config file", Text(str(config_path), style="green"))
    details.add_row("Future fields", Text(settings_list, style="yellow"))
    details.add_row("Current mode", Text("placeholder: command is not executed", style="bold yellow"))

    if saved_path is not None:
        details.add_row("Saved", Text(str(saved_path), style="bold green"))

    return Panel(
        details,
        title="Task Card",
        border_style=task.accent,
        box=box.ASCII,
        padding=(1, 2),
    )


def build_selected_task_panel(
    task: TaskSpec,
    settings: NavigatorSettings,
    config_path: Path,
    active_task_key: str | None,
) -> Panel:
    is_active = task.key == active_task_key
    details = Table.grid(padding=(0, 1))
    details.add_column(style="bold white", no_wrap=True)
    details.add_column()
    details.add_row(
        "Config state",
        Text("ACTIVE IN CONFIG" if is_active else "not active", style="bold green" if is_active else "bright_black"),
    )
    details.add_row("Nr", f"{task.project_number}")
    details.add_row("Temat", Text(task.title, style=f"bold {task.accent}"))
    details.add_row("Algorithm", Text(task.algorithm, style="bold cyan"))
    details.add_row("Idea", task.algorithm_description)
    details.add_row("PDF", Text(task.source_pdf, style="bright_black"))
    details.add_row("Config", Text(str(config_path), style="green"))

    return Panel(
        details,
        title="Selected Assignment",
        border_style=task.accent,
        box=box.ASCII,
        padding=(1, 2),
    )


def build_dashboard(
    settings: NavigatorSettings,
    width: int = 100,
    selected_index: int = 0,
    config_path: Path = DEFAULT_CONFIG_PATH,
) -> Group:
    selected_task = TASKS[selected_index]
    active_task_key = load_active_task_key(config_path)
    help_line = Text()
    help_line.append("[UP/DOWN]", style="bold cyan")
    help_line.append(" move   ")
    help_line.append("[ENTER]", style="bold green")
    help_line.append(" save config   ")
    help_line.append("[S]", style="bold green")
    help_line.append(" settings   ")
    help_line.append("[Q]", style="bold red")
    help_line.append(" quit")

    separator = Text("-" * 79, style="bright_black")

    if width >= 110:
        layout = Table.grid(expand=True)
        layout.add_column(ratio=3)
        layout.add_column(ratio=2)
        layout.add_row(
            build_task_table(TASKS, selected_index, active_task_key),
            build_selected_task_panel(selected_task, settings, config_path, active_task_key),
        )
        return Group(build_header(), layout, separator, Align.center(help_line))

    return Group(
        build_header(),
        build_task_table(TASKS, selected_index, active_task_key),
        build_selected_task_panel(selected_task, settings, config_path, active_task_key),
        separator,
        Align.center(help_line),
    )


def render_dashboard(
    console: Console,
    settings: NavigatorSettings,
    selected_index: int,
    config_path: Path,
) -> None:
    console.clear()
    console.print(build_dashboard(settings, console.width, selected_index, config_path))


def select_task(
    console: Console,
    settings: NavigatorSettings,
    index: int,
    config_path: Path,
) -> None:
    task = TASKS[index - 1]
    saved_path = write_config(task, settings, config_path)
    console.print()
    console.print(build_task_details(task, settings, config_path, saved_path))
    console.print()
    console.print(
        Panel(
            Text(
                "This is a safe dry-run. run.py will read the saved config on startup; "
                "the real subprocess or direct Python call can be wired later.",
                style="white",
            ),
            title="Integration Plan",
            border_style="bright_black",
            box=box.ASCII,
        )
    )
    Prompt.ask("Press Enter to return to the menu", default="")


def read_key() -> str:
    # Читаем одну клавишу, чтобы стрелки работали без Enter.
    if os.name == "nt":
        import msvcrt

        char = msvcrt.getwch()
        if char in ("\x00", "\xe0"):
            code = msvcrt.getwch()
            return {"H": "up", "P": "down", "K": "left", "M": "right"}.get(code, "unknown")
        if char == "\r":
            return "enter"
        if char == "\x03":
            raise KeyboardInterrupt
        return char.lower()

    import termios
    import tty

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        char = sys.stdin.read(1)
        if char == "\x1b":
            sequence = sys.stdin.read(2)
            return {"[A": "up", "[B": "down", "[D": "left", "[C": "right"}.get(sequence, "escape")
        if char in ("\r", "\n"):
            return "enter"
        if char == "\x03":
            raise KeyboardInterrupt
        return char.lower()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def edit_settings(console: Console, settings: NavigatorSettings) -> None:
    console.print()
    console.print(build_settings_panel(settings))
    console.print()

    field_choice = Prompt.ask(
        "Edit field",
        choices=["model", "endpoint", "steps", "dry", "dashboard", "back"],
        default="back",
    )

    if field_choice == "model":
        settings.model_name = Prompt.ask("Model", default=settings.model_name)
    elif field_choice == "endpoint":
        settings.endpoint = Prompt.ask("API endpoint", default=settings.endpoint)
    elif field_choice == "steps":
        settings.max_steps = IntPrompt.ask("Mission steps", default=settings.max_steps)
    elif field_choice == "dry":
        settings.dry_run = Confirm.ask("Keep dry-run mode", default=settings.dry_run)
    elif field_choice == "dashboard":
        settings.auto_open_dashboard = Confirm.ask(
            "Open dashboard automatically",
            default=settings.auto_open_dashboard,
        )


def run_interactive(console: Console, settings: NavigatorSettings, config_path: Path) -> int:
    selected_index = 0
    while True:
        render_dashboard(console, settings, selected_index, config_path)
        key = read_key()

        if key == "q":
            console.print(Text("Navigator closed.", style="bold cyan"))
            return 0
        if key == "s":
            edit_settings(console, settings)
            continue
        if key == "up":
            selected_index = (selected_index - 1) % len(TASKS)
            continue
        if key == "down":
            selected_index = (selected_index + 1) % len(TASKS)
            continue
        if key == "enter":
            select_task(console, settings, selected_index + 1, config_path)
            continue
        if key.isdigit() and 1 <= int(key) <= len(TASKS):
            selected_index = int(key) - 1
            continue

        console.print(Text("Unknown key. Use arrows, Enter, S, Q, or 1-5.", style="bold red"))
        Prompt.ask("Press Enter to continue", default="")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rich navigator for Ares neural tasks.")
    parser.add_argument("--preview", action="store_true", help="Render menu once and exit.")
    parser.add_argument("--task", choices=[task.key for task in TASKS], help="Show one task card and exit.")
    parser.add_argument("--write-config", action="store_true", help="Save the selected task into mission_config.json.")
    parser.add_argument("--config-path", type=Path, default=DEFAULT_CONFIG_PATH, help="Path for the generated config file.")
    parser.add_argument("--no-clear", action="store_true", help="Do not clear terminal before rendering.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    console = Console()
    settings = NavigatorSettings()
    config_path = args.config_path

    if args.write_config and not args.task:
        raise SystemExit("--write-config requires --task so the selected task is explicit.")

    if args.preview:
        if not args.no_clear:
            console.clear()
        console.print(build_dashboard(settings, console.width, config_path=config_path))
        return 0

    if args.task:
        task = next(task for task in TASKS if task.key == args.task)
        saved_path = write_config(task, settings, config_path) if args.write_config else None
        if not args.no_clear:
            console.clear()
        console.print(build_header())
        console.print(build_task_details(task, settings, config_path, saved_path))
        return 0

    return run_interactive(console, settings, config_path)


if __name__ == "__main__":
    raise SystemExit(main())
