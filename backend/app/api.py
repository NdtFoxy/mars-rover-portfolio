import os
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import random 
from fastapi import APIRouter
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

from .models import GameState
from .core.environment import Environment
from .core.agent import Agent
from .core.decision_tree_agent import generate_dataset

router = APIRouter()

# =====================================================================
# KONWERSJA TERENU NA OBRAZ 3x3 Z SZUMEM LOSOWYM (Sensor Noise)
# =====================================================================
def terrain_to_pixels(terrain_type):
    if terrain_type == 0:   # Piasek (Sand)
        base = [220, 220, 220, 210, 210, 210, 220, 220, 220]
    elif terrain_type == 1: # Skała (Rock)
        base = [80, 180, 80, 180, 80, 180, 80, 180, 80]
    else:                   # Krater (Crater)
        base = [50, 50, 50, 50, 10, 50, 50, 50, 50]
    
    noisy_pixels = []
    for val in base:
        noise = random.randint(-15, 15)
        noisy_val = max(0, min(255, val + noise))
        noisy_pixels.append(noisy_val)
        
    return noisy_pixels

# =====================================================================
# DEFINICJA ARCHITEKTURY SIECI NEURONOWEJ (PyTorch MLP)
# =====================================================================
class MissionControlNN(nn.Module):
    def __init__(self, input_dim=16, output_dim=2):
        super(MissionControlNN, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, output_dim)
        )

    def forward(self, x):
        return self.net(x)

# =====================================================================
# BEZPIECZNA GENERACJA I BALANSOWANIE DANYCH (Wymóg: >= 1000 na klasę)
# =====================================================================
def generate_balanced_dataset(required_per_class: int = 1000):
    print(f"[SYSTEM] Generowanie zbalansowanego zbioru danych (min. {required_per_class} próbek na klasę)...")
    accumulated_rows = []
    counts = {"GO_TO_CHARGE": 0, "CONTINUE_MINING": 0}
    
    while counts["GO_TO_CHARGE"] < required_per_class or counts["CONTINUE_MINING"] < required_per_class:
        batch = generate_dataset(500)
        for _, row in batch.iterrows():
            dist = row["dist_to_station"]
            battery = row["battery_level"]
            inventory_size = row["inventory_size"]
            
            # 🚨 NAPRAWA BŁĘDU ŚMIERCI (ZWIĘKSZONY MARGINES BEZPIECZEŃSTWA)
            # Dystans * 2.5 (bo skały kosztują 2.0, a obrót 1.0)
            # Żelazna rezerwa 30.0% na wypadek nocy (brak słońca po 20:00)
            safety_margin = 30.0  
            energy_needed_to_return = (dist * 2.5) + safety_margin
            
            if battery < energy_needed_to_return or inventory_size >= 8:
                corrected_decision = "GO_TO_CHARGE"
            else:
                corrected_decision = row["target_decision"]
                
            if corrected_decision in counts:
                if counts[corrected_decision] < required_per_class:
                    new_row = row.to_dict()
                    new_row["target_decision"] = corrected_decision
                    accumulated_rows.append(new_row)
                    counts[corrected_decision] += 1
                    
    df_balanced = pd.DataFrame(accumulated_rows)
    df_balanced.to_csv("rover_training_data.csv", index=False)
    print(f"[SYSTEM] Dane treningowe zapisano do 'rover_training_data.csv'.")
    return df_balanced

# =====================================================================
# RAPORT DIAGNOSTYCZNY DLA PROFESORA (PLIK + TERMINAL)
# =====================================================================
def run_diagnostic_report(model, scaler, class_mapping, reverse_mapping, val_metrics_text):
    full_report = []
    full_report.append("="*80)
    full_report.append("  SZCZEGÓŁOWY RAPORT DIAGNOSTYCZNY MODELU SIECI NEURONOWEJ (ARES-ML)")
    full_report.append("="*80)
    full_report.append("\n[1. METRYKI KLASYFIKACJI WALIDACYJNEJ]:\n")
    full_report.append(val_metrics_text)
    full_report.append("\n" + "="*80)
    full_report.append("[2. SYMULACJA SCENARIUSZY TESTOWYCH - ANALIZA BEZPIECZEŃSTWA]:\n")

    scenarios = [
        {"desc": "Pełna bateria, blisko minerał, daleka baza", "features": [90.0, 12.0, 1.0, 1.0, 3.0, 20.0, 2.0] + terrain_to_pixels(0)},
        {"desc": "Słaba bateria (30%), stacja bardzo daleko (18 pól) -> Krytyczny powrót", "features": [30.0, 12.0, 1.0, 1.0, 5.0, 18.0, 1.0] + terrain_to_pixels(0)},
        {"desc": "Średnia bateria (40%), stacja blisko (5 pól) -> Bezpieczna regeneracja", "features": [40.0, 8.0, 0.5, 0.8, 2.0, 5.0, 4.0] + terrain_to_pixels(1)},
        {"desc": "Bateria 80%, pełny ekwipunek (8/8) -> Nakaz powrotu do bazy i sprzedaży", "features": [80.0, 14.0, 0.9, 1.0, 4.0, 10.0, 8.0] + terrain_to_pixels(0)}
    ]
    
    model.eval()
    terminal_summary = []
    
    for i, sc in enumerate(scenarios, 1):
        test_input = np.array([sc["features"]])
        test_input_scaled = scaler.transform(test_input)
        test_tensor = torch.tensor(test_input_scaled, dtype=torch.float32)
        
        with torch.no_grad():
            output = model(test_tensor)
            pred_idx = torch.argmax(output, dim=1).item()
            decision = reverse_mapping[pred_idx]
            
        full_report.append(f"Scenariusz {i}: {sc['desc']}")
        full_report.append(f"  Wejście: Bat={sc['features'][0]}%, DystStacja={sc['features'][5]}, Ekwipunek={sc['features'][6]}/8")
        full_report.append(f"  Decyzja Sieci: {decision}")
        full_report.append("-" * 50)
        
        terminal_summary.append(
            f" Scenariusz {i} (Bat: {sc['features'][0]}%, Ekwipunek: {sc['features'][6]}/8) -> Decyzja: \033[92m{decision}\033[0m"
        )
        
    full_report.append("\n[KONIEC RAPORTU]")
    
    with open("nn_model_report.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(full_report))
        
    print("\n" + "="*70)
    print("  SKRÓCONY RAPORT SIECI NEURONOWEJ (Pełny w pliku 'nn_model_report.txt')")
    print("="*70)
    print("[1. METRYKI WALIDACJI (DOKŁADNOŚĆ)]:")
    metric_lines = val_metrics_text.split('\n')
    accuracy_line = next((l for l in metric_lines if "accuracy" in l), "Accuracy: OK")
    print(f"  {accuracy_line.strip()}")
    print("\n[2. PREdykcje SCENARIUSZY SCENICZNYCH]:")
    for s_line in terminal_summary:
        print(s_line)
    print("="*70 + "\n")

# =====================================================================
# INICJALIZACJA I PROCES UCZENIA SIECI NEURONOWEJ
# =====================================================================
print("[SYSTEM] Inicjalizacja rdzenia decyzyjnego opartego o sieć neuronową...")

raw_dataset = generate_balanced_dataset(1000)

pixel_cols = [f"p{i}" for i in range(1, 10)]
pixel_data = []
for idx, row in raw_dataset.iterrows():
    t_type = int(row["terrain_type"])
    pixel_data.append(terrain_to_pixels(t_type))

df_pixels = pd.DataFrame(pixel_data, columns=pixel_cols, index=raw_dataset.index)
raw_dataset = pd.concat([raw_dataset, df_pixels], axis=1)

features = [
    "battery_level", "time_of_day", "solar_efficiency", 
    "weather_multiplier", "dist_to_mineral", 
    "dist_to_station", "inventory_size"
] + pixel_cols

X_raw = raw_dataset[features].values
class_mapping = {"GO_TO_CHARGE": 0, "CONTINUE_MINING": 1}
reverse_mapping = {0: "GO_TO_CHARGE", 1: "CONTINUE_MINING"}
y_raw = raw_dataset["target_decision"].map(class_mapping).values

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_raw)

X_train, X_val, y_train, y_val = train_test_split(X_scaled, y_raw, test_size=0.2, random_state=42)

X_train_tensor = torch.tensor(X_train, dtype=torch.float32)
y_train_tensor = torch.tensor(y_train, dtype=torch.long)
X_val_tensor = torch.tensor(X_val, dtype=torch.float32)
y_val_tensor = torch.tensor(y_val, dtype=torch.long)

trained_nn = MissionControlNN(input_dim=16, output_dim=2)
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(trained_nn.parameters(), lr=0.01)

trained_nn.train()
epochs = 80
for epoch in range(epochs):
    optimizer.zero_grad()
    outputs = trained_nn(X_train_tensor)
    loss = criterion(outputs, y_train_tensor)
    loss.backward()
    optimizer.step()

trained_nn.eval()
with torch.no_grad():
    val_outputs = trained_nn(X_val_tensor)
    _, predicted = torch.max(val_outputs, 1)
    y_pred = predicted.numpy()

val_metrics_text = classification_report(y_val, y_pred, target_names=list(class_mapping.keys()))

run_diagnostic_report(trained_nn, scaler, class_mapping, reverse_mapping, val_metrics_text)

print("[SYSTEM] Sieć neuronowa została pomyślnie wytrenowana i zsynchronizowana.")

# =====================================================================
# GLOBALNE OBIEKTY
# =====================================================================
env = Environment(width=20, height=15)
start_x, start_y = env.reset()
agent = Agent(x=start_x, y=start_y)

# =====================================================================
# TERMINAL UPRZĘŻY WIZUALIZACYJNEJ (DASHBOARD)
# =====================================================================
def print_pretty_console(environment: Environment, current_agent: Agent):
    os.system('cls' if os.name == 'nt' else 'clear')

    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    b_val = current_agent.battery
    b_color = GREEN if b_val > 50 else YELLOW if b_val > 20 else RED
    UI_WIDTH = 40

    active_minerals_count = sum(1 for obj in environment.objects if obj.type in ["Titanium", "Water Ice", "Hematite"] and obj.is_active)

    def draw_line(content, color=RESET):
        clean_content = content.replace(GREEN, "").replace(YELLOW, "").replace(RED, "").replace(CYAN, "").replace(BOLD, "").replace(RESET, "")
        padding = UI_WIDTH - len(clean_content)
        print(f"║ {color}{content}{RESET}{' ' * padding} ║")

    print("╔" + "═" * (UI_WIDTH + 2) + "╗")
    draw_line(f"{BOLD}MARS | SPACE LABORATORY (NEURAL NET ACTIVE){RESET}")
    draw_line("PROJECT ARES: SURFACE EXPLORATION UNIT")
    print("╠" + "═" * (UI_WIDTH + 2) + "╣")

    draw_line(f"MISSION TIME : {environment.time_of_day:>5.2f} SOL")
    draw_line(f"WEATHER      : {environment.weather.replace('_', ' ')}")
    
    filled = int(b_val / 10)
    battery_bar = f"[{'█' * filled}{'░' * (10 - filled)}]"
    draw_line(f"ENERGY LEVEL : {b_color}{battery_bar} {b_val:>5.1f}%{RESET}")
    
    draw_line(f"ROVER STATUS : {current_agent.status}")
    draw_line(f"PAYLOAD      : {len(current_agent.inventory)}/8 SAMPLES")
    draw_line(f"BUDGET       : {YELLOW}${current_agent.money:>6.1f}{RESET}")
    
    nn_conf = getattr(current_agent, "nn_confidence", {"MINING": 0.0, "CHARGE": 0.0})
    mining_p = nn_conf.get("MINING", 0.0)
    charge_p = nn_conf.get("CHARGE", 0.0)
    draw_line(f"NN THOUGHT   : MINING {CYAN}{mining_p:>5.1f}%{RESET} | CHARGE {CYAN}{charge_p:>5.1f}%{RESET}")
    
    draw_line(f"MINERALS MAP : {active_minerals_count:>2d} ACTIVE")
    print("╠" + "═" * (UI_WIDTH + 2) + "╣")

    for y_idx in range(environment.height):
        row = ""
        for x_idx in range(environment.width):
            if current_agent.x == x_idx and current_agent.y == y_idx:
                row += "🤖 " 
            else:
                obj = next((o for o in environment.objects if o.x == x_idx and o.y == y_idx and o.is_active), None)
                if obj:
                    if obj.type == "ChargingStation":
                        row += "⚡ " 
                    elif obj.type == "ScienceBase":
                        row += "🚀 " 
                    elif obj.type == "Titanium":
                        row += "🔘 " 
                    elif obj.type == "Water Ice":
                        row += "💎 " 
                    elif obj.type == "Hematite":
                        row += "🔴 " 
                    else:
                        row += "💎 " 
                else:
                    t = environment.get_terrain_type(x_idx, y_idx)
                    if t == 0: 
                        row += "  "   
                    elif t == 1: 
                        row += "🪨 "  
                    else: 
                        row += "⚫ "  
        print(f"║ {row} ║")

    print("╠" + "═" * (UI_WIDTH + 2) + "╣")
    
    current_terrain = environment.get_terrain_type(current_agent.x, current_agent.y)
    current_obj = next((o for o in environment.objects if o.x == current_agent.x and o.y == current_agent.y and o.is_active), None)
    
    if current_obj:
        if current_obj.type == "ChargingStation":
            draw_line(" [ OBRAZ Z KAMERY: KUPUŁA ENERGETYCZNA ]")
            draw_line("        .-----------.  ")
            draw_line("       /  [ ⚡ ]     \\ ")
            draw_line("      /   REGENERACJA\\")
            draw_line("     |_______________| ")
        elif current_obj.type == "ScienceBase":
            draw_line(" [ OBRAZ Z KAMERY: PORT ROZŁADUNKOWY ]")
            draw_line("         .---------.   ")
            draw_line("        /   [ 🚀 ]  \\  ")
            draw_line("       / DEPOZYT RUDY\\ ")
            draw_line("      |_______________|")
        else:
            draw_line(f" [ OBRAZ: METEORYT {current_obj.type.upper()} ]")
            draw_line("           _.-*-._     ")
            draw_line(f"         .-  {current_obj.type[:3].upper()}  -.   ")
            draw_line("        /   ZŁOŻE      \\")
            draw_line("       |_______________|")
    else:
        if current_terrain == 0:
            draw_line(" [ OBRAZ Z KAMERY: WYDMY PIASKOWE ]")
            draw_line("      . . . . . . . .  ")
            draw_line("    . . . . . . . . . .")
            draw_line("  . . . . . . . . . . .")
            draw_line(" . . . . . . . . . . . ")
        elif current_terrain == 1:
            draw_line(" [ OBRAZ Z KAMERY: PASMO SKALISTE ]")
            draw_line("         _  _/\\_  _    ")
            draw_line("       _/ \\/    \\/ \\_  ")
            draw_line("      /   OSTRE SKAŁY  \\")
            draw_line("     /_________________\\")
        else:
            draw_line(" [ OBRAZ Z KAMERY: GŁĘBOKI KRATER ]")
            draw_line("        \\             /")
            draw_line("         \\   ABYSS   / ")
            draw_line("          \\_________/  ")
            draw_line("          (NIEPRZEJEZD)")
            
    print("╠" + "═" * (UI_WIDTH + 2) + "╣")
    
    draw_line(" [ SYSTEM ANALIZY DANYCH W TLE (ML) ]")
    
    solar_eff = current_agent._calculate_solar_efficiency(environment.time_of_day)
    weather_mult = current_agent.WEATHER_MULTIPLIERS.get(environment.weather, 1.0)
    
    pixels = terrain_to_pixels(current_terrain)
    p_row1 = f"[{pixels[0]:>3}, {pixels[1]:>3}, {pixels[2]:>3}]"
    p_row2 = f"[{pixels[3]:>3}, {pixels[4]:>3}, {pixels[5]:>3}]"
    p_row3 = f"[{pixels[6]:>3}, {pixels[7]:>3}, {pixels[8]:>3}]"
    
    draw_line(f" TELEMETRIA: Bat:{b_val:.0f}%|Czas:{environment.time_of_day:.1f}h|Pogoda:{weather_mult:.1f}")
    
    draw_line(" MACIERZ PIKSELI KAMERY (3x3 Grayscale):")
    draw_line(f"   {p_row1}")
    draw_line(f"   {p_row2}")
    draw_line(f"   {p_row3}")
    
    draw_line(f" NEURONY: Wejście: 16 | L1: 32 (ReLU) | L2: 16")
    
    mining_p = current_agent.nn_confidence['MINING']
    charge_p = current_agent.nn_confidence['CHARGE']
    selected_act = "MINING" if mining_p > charge_p else "CHARGE"
    
    draw_line(f" PROB: MINING {mining_p:.1f}% | CHARGE {charge_p:.1f}%")
    draw_line(f" DECYZJA SIECI: -> {selected_act} (Aktywny)")

    print("╚" + "═" * (UI_WIDTH + 2) + "╝")
    print(f"[ telemetry.link ] step: {environment.step_counter:04d} | data_sync: OK")
    print("🚀 Baza | ⚡ Ładowarka | 🔘 Tytan ($100) | 💎 Lód ($50) | 🔴 Hematyt ($30) | 🪨 Skała | ⚫ Krater")

# =====================================================================
# API ENDPOINTS
# =====================================================================

@router.get("/state", response_model=GameState)
async def get_current_state():
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
    agent.follow_plan_or_search(env, trained_nn=trained_nn, scaler=scaler, reverse_mapping=reverse_mapping)
    agent.interact_and_recharge(env)
    env.update_time_and_weather()
    print_pretty_console(env, agent)
    return await get_current_state()

@router.post("/step_multiple/{count}", response_model=GameState)
async def make_multiple_steps(count: int):
    for _ in range(count):
        if agent.status == "DEAD": break
        agent.follow_plan_or_search(env, trained_nn=trained_nn, scaler=scaler, reverse_mapping=reverse_mapping)
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