import os
from fastapi import APIRouter
from sklearn.tree import DecisionTreeClassifier

from .models import GameState
from .core.environment import Environment
from .core.agent import Agent
from .core.decision_tree_agent import generate_dataset

router = APIRouter()

# =====================================================================
# ИНИЦИАЛИЗАЦИЯ ИИ 
# =====================================================================
print("[SYSTEM] Initializing Decision Core...")

dataset = generate_dataset(500)
features = [
    "battery_level", "time_of_day", "solar_efficiency", 
    "weather_multiplier", "terrain_type", "dist_to_mineral", 
    "dist_to_station", "inventory_size"
]
X = dataset[features]
y = dataset["target_decision"]

trained_tree = DecisionTreeClassifier(criterion='entropy', max_depth=4, random_state=42)
trained_tree.fit(X, y)

print("[SYSTEM] ML Model synchronized. Operational readiness: 100%.")

# =====================================================================
# ГЛОБАЛЬНЫЕ ОБЪЕКТЫ
# =====================================================================
env = Environment(width=20, height=15)
start_x, start_y = env.reset()
agent = Agent(x=start_x, y=start_y)

# =====================================================================
# ТЕРМИНАЛ УПРАВЛЕНИЯ MARS | SPACE LABORATORY (FIXED ALIGNMENT)
# =====================================================================
def print_pretty_console(environment: Environment, current_agent: Agent):
    """
    Профессиональный дашборд MARS | SPACE LABORATORY.
    Исправлены ошибки выравнивания рамок и изменен визуальный стиль.
    """
    os.system('cls' if os.name == 'nt' else 'clear')

    # Цветовая схема
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    # Определяем цвет батареи
    b_val = current_agent.battery
    b_color = GREEN if b_val > 50 else YELLOW if b_val > 20 else RED
    
    # Расчет ширины (20 клеток по 2 символа + рамки = 44 символа)
    # Ширина контента внутри рамки всегда 40 символов
    UI_WIDTH = 40

    def draw_line(content, color=RESET):
        """Вспомогательная функция для отрисовки строки в рамке"""
        # Очищаем контент от ANSI кодов для корректного замера длины
        clean_content = content.replace(GREEN, "").replace(YELLOW, "").replace(RED, "").replace(CYAN, "").replace(BOLD, "").replace(RESET, "")
        padding = UI_WIDTH - len(clean_content)
        print(f"║ {color}{content}{RESET}{' ' * padding} ║")

    # 1. Заголовок
    print("╔" + "═" * (UI_WIDTH + 2) + "╗")
    draw_line(f"{BOLD}MARS | SPACE LABORATORY{RESET}")
    draw_line("PROJECT ARES: SURFACE EXPLORATION UNIT")
    print("╠" + "═" * (UI_WIDTH + 2) + "╣")

    # 2. Данные телеметрии
    draw_line(f"MISSION TIME : {environment.time_of_day:>5.2f} SOL")
    draw_line(f"WEATHER      : {environment.weather.replace('_', ' ')}")
    
    # Прогресс-бар батареи (10 сегментов)
    filled = int(b_val / 10)
    battery_bar = f"[{'█' * filled}{'░' * (10 - filled)}]"
    draw_line(f"ENERGY LEVEL : {b_color}{battery_bar} {b_val:>5.1f}%{RESET}")
    
    draw_line(f"ROVER STATUS : {current_agent.status}")
    draw_line(f"PAYLOAD      : {len(current_agent.inventory)}/8 SAMPLES")
    print("╠" + "═" * (UI_WIDTH + 2) + "╣")

    # 3. Визуализация поверхности (Карта)
    # Здесь каждая клетка занимает ровно 2 символа ширины
    for y in range(environment.height):
        row = ""
        for x in range(environment.width):
            if current_agent.x == x and current_agent.y == y:
                row += "🤖" # Ровер
            else:
                obj = next((o for o in environment.objects if o.x == x and o.y == y and o.is_active), None)
                if obj:
                    row += "⚡️" if obj.type == "ChargingStation" else "💎"
                else:
                    t = environment.get_terrain_type(x, y)
                    if t == 0: row += "  " # Пустое пространство 
                    elif t == 1: row += "🪨 " # Камни
                    else: row += "⬛"        # Кратер
        print(f"║ {row} ║")

    print("╚" + "═" * (UI_WIDTH + 2) + "╝")
    print(f"[ telemetry.link ] step: {environment.step_counter:04d} | data_sync: OK")

# =====================================================================
# API ENDPOINTS
# =====================================================================

@router.get("/state", response_model=GameState)
async def get_current_state():
    """Сбор текущих данных для внешних систем (Unreal Engine / Web)."""
    env_dict = env.to_dict()
    return GameState(
        agent=agent.to_dict(),
        environment={
            "step_counter": env_dict["step_counter"],
            "time_of_day": env_dict["time_of_day"],
            "weather": env_dict["weather"]
        },
        grid=env_dict["grid"],
        objects=env_dict["objects"]
    )

@router.post("/step", response_model=GameState)
async def make_next_step():
    """Выполнение одиночного командного цикла."""
    agent.follow_plan_or_search(env, trained_tree=trained_tree)
    agent.interact_and_recharge(env)
    env.update_time_and_weather()
    print_pretty_console(env, agent)
    return await get_current_state()

@router.post("/step_multiple/{count}", response_model=GameState)
async def make_multiple_steps(count: int):
    """Пакетное выполнение команд (Fast-Forward)."""
    for _ in range(count):
        if agent.status == "DEAD": break
        agent.follow_plan_or_search(env, trained_tree=trained_tree)
        agent.interact_and_recharge(env)
        env.update_time_and_weather()
        
    print_pretty_console(env, agent)
    return await get_current_state()

@router.post("/restart", response_model=GameState)
async def restart_simulation():
    """Сброс и реинициализация миссии."""
    global env, agent
    start_x, start_y = env.reset()
    agent = Agent(x=start_x, y=start_y)
    print_pretty_console(env, agent)
    return await get_current_state()