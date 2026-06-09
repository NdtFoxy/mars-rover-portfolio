from fastapi import APIRouter
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .models import GameState
from .core.environment import Environment, MINERAL_TYPES
from .core.agent import Agent
from zadania.zadanie_5_DrzewoDecyzyjne.drzewo import train_tree
from zadania.zadanie_6_SiecNeuronowa.siec import train_cnn
from .core import shop, mission
from zadania.zadanie_7_AlgorytmGenetyczny.genetyczny import items_from_minerals, compare_knapsack

router = APIRouter()

# =====================================================================
# MÓZG ŁAZIKA: drzewo decyzyjne zawsze + CNN tylko dla zadania 6
# Мозг ровера: дерево решений всегда + CNN только для задания 6
# =====================================================================
print("[SYSTEM] Trenuję drzewo decyzyjne / Обучаю дерево решений...")
tree_clf, _ = train_tree()

trained_nn = None
scaler = None
reverse_mapping = None


def ensure_cnn_loaded():
    """Leniwy trening sieci CNN -- tylko gdy aktywne jest zadanie 6.
    Ленивое обучение сети CNN -- только когда активно задание 6.
    """
    global trained_nn, scaler, reverse_mapping
    if trained_nn is not None:
        return
    trained_nn, scaler, reverse_mapping = train_cnn()


def active_decision_models():
    """CNN jest przekazywana agentowi wyłącznie w trybie zadania 6.
    CNN передается агенту только в режиме задания 6.
    """
    if mission.get_active_task().get("selected_task") == "project-6-neural-networks":
        ensure_cnn_loaded()
        return trained_nn, scaler, reverse_mapping
    return None, None, None


_active = mission.get_active_task()
_proj = _active.get("project_number")
_title = _active.get("task_title", "?")
if _active.get("selected_task") == "project-6-neural-networks":
    print(f"[SYSTEM] Aktywne zadanie: {_proj} ({_title}) -> mozg: siec CNN+MLP")
    ensure_cnn_loaded()
else:
    print(f"[SYSTEM] Aktywne zadanie: {_proj} ({_title}) -> mozg: drzewo decyzyjne (CNN tylko w zad. 6)")

# =====================================================================
# GLOBALNE OBIEKTY
# ГЛОБАЛЬНЫЕ ОБЪЕКTY
# =====================================================================
env = Environment(width=20, height=15)
start_x, start_y = env.reset()
agent = Agent(x=start_x, y=start_y)

# =====================================================================
# TERMINAL WIZUALIZACYJNY (DASHBOARD)
# ВИЗУАЛЬНЫЙ ТЕРМИНАЛ (DASHBOARD)
# =====================================================================
def print_pretty_console(environment: Environment, current_agent: Agent):
    console = Console()
    console.clear()

    dashboard_width = 72
    b_val = current_agent.battery
    battery_style = "green" if b_val > 50 else "yellow" if b_val > 20 else "red"
    filled = max(0, min(10, int(b_val / 10)))
    battery_bar = f"[{'█' * filled}{'░' * (10 - filled)}]"

    active_minerals_count = sum(
        1
        for obj in environment.objects
        if obj.type in ["Titanium", "Water Ice", "Hematite"] and obj.is_active
    )
    nn_conf = getattr(current_agent, "nn_confidence", {"MINING": 0.0, "CHARGE": 0.0})
    mining_p = nn_conf.get("MINING", 0.0)
    charge_p = nn_conf.get("CHARGE", 0.0)

    def value_text(value, style="white"):
        return Text(str(value), style=style)

    def add_metric(table, label, value):
        if not isinstance(value, Text):
            value = value_text(value)
        table.add_row(Text(f"{label:<14}: ", style="bold white"), value)

    stats = Table.grid(expand=True)
    stats.add_column(no_wrap=True)
    stats.add_column(ratio=1)

    battery = Text()
    battery.append(battery_bar, style=battery_style)
    battery.append(f" {b_val:>5.1f}%")

    upgrades = getattr(current_agent, "upgrade_levels", {})
    upgrades_text = Text()
    upgrades_text.append(f"SOL{upgrades.get('solar', 0)} ", style="cyan")
    upgrades_text.append(f"CMP{upgrades.get('compressor', 0)} ", style="cyan")
    upgrades_text.append(f"CRG{upgrades.get('cargo', 0)} ", style="cyan")
    upgrades_text.append(f"MOT{upgrades.get('motor', 0)} ", style="cyan")
    upgrades_text.append(f"BAT{upgrades.get('battery', 0)} ", style="cyan")
    upgrades_text.append(f"DRL{upgrades.get('drill', 0)}", style="cyan")

    thought = Text()
    thought.append("MINING ")
    thought.append(f"{mining_p:>5.1f}%", style="cyan")
    thought.append(" | CHARGE ")
    thought.append(f"{charge_p:>5.1f}%", style="cyan")

    add_metric(stats, "MISSION TIME", f"{environment.time_of_day:>5.2f} SOL")
    add_metric(stats, "WEATHER", environment.weather.replace("_", " "))
    add_metric(stats, "ENERGY LEVEL", battery)
    add_metric(stats, "ROVER STATUS", current_agent.status)
    add_metric(
        stats,
        "WAGA",
        f"{current_agent.current_weight():>4.1f}/{current_agent.capacity:.0f} kg ({len(current_agent.inventory)} szt.)",
    )
    add_metric(stats, "OBJETOSC", f"{current_agent.current_volume():>4.1f}/{current_agent.volume_capacity:.0f} l")
    add_metric(stats, "BUDGET", Text(f"${current_agent.money:>6.1f}", style="yellow"))
    add_metric(stats, "UPG", upgrades_text)

    last_knapsack = getattr(current_agent, "last_knapsack", None)
    if last_knapsack:
        add_metric(
            stats,
            f"KNAPSACK[{last_knapsack['method']}]",
            (
                f"{last_knapsack['count']}szt ${last_knapsack['value']:.0f} "
                f"{last_knapsack['weight']:.0f}kg/{last_knapsack.get('volume', 0):.0f}l"
            ),
        )

    add_metric(stats, "PEWNOŚĆ MODELU / УВЕРЕННОСТЬ МОДЕЛI", thought)

    def tile_for(x_idx, y_idx):
        if current_agent.x == x_idx and current_agent.y == y_idx:
            return "RV", "bold magenta"

        obj = next(
            (o for o in environment.objects if o.x == x_idx and o.y == y_idx and o.is_active),
            None,
        )
        if obj:
            if obj.type == "ChargingStation":
                return "CH", "bold yellow"
            if obj.type == "ScienceBase":
                return "BA", "bold cyan"
            if obj.type == "Titanium":
                return "Ti", "bright_white"
            if obj.type == "Water Ice":
                return "Wi", "bright_blue"
            if obj.type == "Hematite":
                return "He", "bright_red"
            return "Wi", "bright_blue"

        terrain = environment.get_terrain_type(x_idx, y_idx)
        if terrain == 1:
            return "##", "white"
        if terrain == 2:
            return "()", "grey54"
        return " ", "grey23"

    map_text = Text(no_wrap=True)
    for y_idx in range(environment.height):
        for x_idx in range(environment.width):
            symbol, style = tile_for(x_idx, y_idx)
            map_text.append(f"{symbol:<2}", style=style)
            if x_idx < environment.width - 1:
                map_text.append(" ")
        if y_idx < environment.height - 1:
            map_text.append("\n")

    weather_mult = current_agent.WEATHER_MULTIPLIERS.get(environment.weather, 1.0)
    selected_act = getattr(current_agent, "last_decision", "CONTINUE_MINING")
    decision_system = getattr(current_agent, "decision_system", "HEURISTIC")
    cnn_active = decision_system == "CNN + MLP"

    decision = Table.grid(expand=True)
    decision.add_column(no_wrap=True)
    decision.add_column(ratio=1)
    add_metric(decision, "TELEMETRIA", f"Bat:{b_val:.0f}% | Czas:{environment.time_of_day:.1f}h | Pogoda:{weather_mult:.1f}")
    add_metric(
        decision,
        "MODEL",
        "CNN (obraz UE5 32x32) + MLP (7 cech)"
        if cnn_active else "Drzewo decyzyjne ID3 (8 cech)",
    )
    add_metric(decision, "PROB", f"MINING {mining_p:.1f}% | CHARGE {charge_p:.1f}%")
    add_metric(decision, "DECYZJA", f"-> {selected_act}")

    footer = Text()
    footer.append("[ telemetry.link ]", style="bold cyan")
    footer.append(f" step: {environment.step_counter:04d} | data sync: OK")

    legend = Text()
    legend.append("BA Baza+Sklep", style="cyan")
    legend.append(" | ")
    legend.append("CH Ładowarka", style="yellow")
    legend.append(" | ")
    legend.append("Ti Tytan ($100/8kg)", style="bright_white")
    legend.append(" | ")
    legend.append("Wi Lód ($50/3kg)", style="bright_blue")
    legend.append(" | ")
    legend.append("He Hematyt ($30/5kg)", style="bright_red")
    legend.append(" | ")
    legend.append("## Skała", style="white")
    legend.append(" | ")
    legend.append("() Krater", style="grey54")
    legend.append(" | ")
    legend.append("RV Rover", style="magenta")

    console.print(
        Panel(
            stats,
            title=f"MARS | SPACE LABORATORY ({decision_system} ACTIVE)",
            subtitle="PROJECT ARES: SURFACE EXPLORATION UNIT",
            border_style="cyan",
            box=box.DOUBLE,
            width=dashboard_width,
        )
    )
    console.print(
        Panel(
            map_text,
            title=f"MINERALS MAP: {active_minerals_count:02d} ACTIVE",
            border_style="green",
            box=box.SQUARE,
            width=dashboard_width,
        )
    )
    console.print(
        Panel(
            decision,
            title=f"SYSTEM DECYZYJNY ({decision_system})",
            border_style="magenta",
            box=box.SQUARE,
            width=dashboard_width,
        )
    )
    console.print(Panel(footer, border_style="bright_black", box=box.SIMPLE, width=dashboard_width))
    console.print(Panel(legend, border_style="bright_black", box=box.SIMPLE, width=dashboard_width))

# =====================================================================
# API ENDPOINTS
# ENDPOINTY API / ЭНДПОИНТЫ API
# =====================================================================

@router.get("/state", response_model=GameState)
async def get_current_state():
    # Pakuje CALY stan symulacji w jeden JSON dla UE5: agent, srodowisko, krata,
    # obiekty (mineraly/stacje), sklep i aktywne zadanie. To "zdjecie" swiata.
    env_dict = env.to_dict()
    return GameState(
        agent=agent.to_dict(env),
        environment={
            "step_counter": env_dict["step_counter"],
            "time_of_day": env_dict["time_of_day"],
            "weather": env_dict["weather"]
        },
        grid=env_dict["grid"],
        objects=env_dict["objects"],
        shop=shop.get_shop_state(agent),
        mission=mission.active_task_summary()
    )

@router.post("/step", response_model=GameState)
async def make_next_step():
    # JEDEN KROK SYMULACJI (UE5 wola to w petli co 1-2 s):
    active_nn, active_scaler, active_mapping = active_decision_models()  # CNN tylko w zad.6, inaczej None
    agent.follow_plan_or_search(                # 1) mysl: znajdz/wykonaj plan (BFS/A* + decyzja)
        env,
        trained_nn=active_nn,
        scaler=active_scaler,
        reverse_mapping=active_mapping,
        tree_clf=tree_clf,                     #    drzewo zawsze dostepne jako bazowy mozg
    )
    agent.interact_and_recharge(env)           # 2) interakcja: kopanie / ladowanie / baza
    env.update_time_and_weather()              # 3) swiat: czas, pogoda, regeneracja
    print_pretty_console(env, agent)           # 4) podglad w terminalu serwera
    return await get_current_state()           # 5) odeslij nowy stan do UE5

@router.post("/step_multiple/{count}", response_model=GameState)
async def make_multiple_steps(count: int):
    active_nn, active_scaler, active_mapping = active_decision_models()
    for _ in range(count):
        if agent.status == "DEAD": break
        agent.follow_plan_or_search(
            env,
            trained_nn=active_nn,
            scaler=active_scaler,
            reverse_mapping=active_mapping,
            tree_clf=tree_clf,
        )
        agent.interact_and_recharge(env)
        env.update_time_and_weather()

    print_pretty_console(env, agent)
    return await get_current_state()

@router.post("/restart", response_model=GameState)
async def restart_simulation():
    global env, agent
    start_x, start_y = env.reset()
    agent = Agent(x=start_x, y=start_y)
    print_pretty_console(env, agent)
    return await get_current_state()

# =====================================================================
# SKLEP Z ULEPSZENIAMI (Shop)
# МАГАЗYN УЛУЧШЕНИЙ (Shop)
# =====================================================================
@router.get("/shop")
async def get_shop():
    return {
        "money": round(agent.money, 2),
        "inventory": agent.inventory,
        "items": shop.get_shop_state(agent),
    }

@router.post("/shop/buy/{upgrade_id}")
async def buy_upgrade(upgrade_id: str):
    """Ręczny zakup ulepszenia (pieniądze + materiały).
    Ручная покупка улучшения (деньги + материалы).
    """
    result = shop.purchase_upgrade(agent, upgrade_id)
    result["money"] = round(agent.money, 2)
    result["items"] = shop.get_shop_state(agent)
    return result

# =====================================================================
# PROBLEM PLECAKOWY (Knapsack): porównanie GA vs DP na bieżącej mapie
# ЗАДАЧА РЮКЗАКА (Knapsack): сравнение GA vs DP на текущей карте
# =====================================================================
@router.get("/knapsack")
async def knapsack_compare():
    """
    Rozwiązuje problem plecakowy dla aktualnie widocznych minerałów (limit =
    wolne miejsce w plecaku) dwoma metodami i zwraca porównanie GA vs DP.
    Решает задачу рюкзака для текущих видимых минералов (лимит = свободное
    место в рюкзаке) двумя методами и возвращает сравнение GA vs DP.
    """
    active = [m for m in env.objects if m.is_active and m.type in MINERAL_TYPES]
    items = items_from_minerals(active)
    # Kompresor zmniejsza efektywną objętość przenoszonych minerałów.
    # Компрессор уменьшает эффективный объём переносимых минералов.
    for it in items:
        it.volume *= agent.volume_factor
    rem_w = max(0.0, agent.capacity - agent.current_weight())
    rem_v = max(0.0, agent.volume_capacity - agent.current_volume())
    return compare_knapsack(items, rem_w, rem_v)

# =====================================================================
# MISJA: aktywne zadanie dla Unreal Engine + przeładowanie (Alt+R / UE5)
# МИССИЯ: активное задание для Unreal Engine + перезагрузка (Alt+R / UE5)
# =====================================================================
@router.get("/mission")
async def get_mission():
    """Pełne dane aktualnie wybranego zadania (z mission_config.json).
    Полные данные текущего выбранного задания (из mission_config.json).
    """
    return mission.get_active_task()

@router.post("/mission/reload")
async def reload_mission():
    """Przeładowuje wybór z navigate.py (Alt+R w run.py lub przycisk w UE5).
    Перезагружает выбор из navigate.py (Alt+R в run.py или кнопка в UE5).
    """
    data = mission.reload_active_task()
    print(f"[MISSION] Przeładowano zadanie / Перезагружено задание -> {data.get('selected_task')} | {data.get('task_title')}")
    # Stara ścieżka mogła zostać policzona innym algorytmem.
    # Старая ścieżka могла быть рассчитана другим алгоритmem.
    # Następny krok ma od razu użyć aktualnie wybranego zadania.
    # Следующий krok ma od razu użyć aktualnie wybranego zadania.
    agent.current_plan = []
    agent.mining_manifest = []
    agent.status = "IDLE"
    # Zadanie 6 wymaga sieci CNN -> doucz ją leniwie (jeśli jeszcze nie ma).
    # Задanie 6 wymaga sieci CNN -> dograj ją лениво, если jeszcze jej nie ma.
    if data.get("selected_task") == "project-6-neural-networks":
        ensure_cnn_loaded()
    return {"reloaded": True, "mission": mission.active_task_summary()}
