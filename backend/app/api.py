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
from PIL import Image
import torchvision.transforms as transforms

from .models import GameState
from .core.environment import Environment
from .core.agent import Agent
from .core.decision_tree_agent import generate_dataset

router = APIRouter()

# =====================================================================
# TRANSFORMCJE OBRAZÓW (W TYM AUGMENTACJA DLA TRENINGU)
# =====================================================================
train_transforms = transforms.Compose([
    transforms.Resize((32, 32)),
    transforms.RandomRotation(15),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.ToTensor()
])

val_transforms = transforms.Compose([
    transforms.Resize((32, 32)),
    transforms.ToTensor()
])

# =====================================================================
# FUNKCJA POMOCNICZA: WCZYTYWANIE OBRAZU UE5 Z DYSKU
# =====================================================================
def get_ue5_image(category: str, is_training: bool = True) -> torch.Tensor:
    folder_path = os.path.join("ue5_photos", category)
    fallback_tensor = torch.zeros((3, 32, 32))

    if not os.path.exists(folder_path) or not os.listdir(folder_path):
        return fallback_tensor

    files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if not files:
        return fallback_tensor

    random_file = random.choice(files)
    img_path = os.path.join(folder_path, random_file)

    try:
        img = Image.open(img_path).convert('RGB')
        if is_training:
            return train_transforms(img)
        else:
            return val_transforms(img)
    except Exception as e:
        print(f"[OSTRZEZENIE] Blad wczytywania obrazu {img_path}: {e}")
        return fallback_tensor

# Pozostawione dla zgodności z wyświetlaniem retro-konsoli
def terrain_to_pixels(terrain_type):
    if terrain_type == 0:
        base = [220, 220, 220, 210, 210, 210, 220, 220, 220]
    elif terrain_type == 1:
        base = [80, 180, 80, 180, 80, 180, 80, 180, 80]
    else:
        base = [50, 50, 50, 50, 10, 50, 50, 50, 50]
    
    noisy_pixels = []
    for val in base:
        noise = random.randint(-15, 15)
        noisy_val = max(0, min(255, val + noise))
        noisy_pixels.append(noisy_val)
        
    return noisy_pixels

# =====================================================================
# WIELOWEJŚCIOWA ARCHITEKTURA SIECI NEURONOWEJ (MULTIMODAL CNN)
# =====================================================================
class MissionControlCNN(nn.Module):
    def __init__(self, tabular_dim=7, output_dim=2):
        super(MissionControlCNN, self).__init__()
        
        self.cnn = nn.Sequential(
            nn.Conv2d(in_channels=3, out_channels=16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2),
            nn.Conv2d(in_channels=16, out_channels=32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2),
            nn.Flatten()
        )
        
        self.mlp = nn.Sequential(
            nn.Linear(tabular_dim, 16),
            nn.ReLU()
        )
        
        self.classifier = nn.Sequential(
            nn.Linear(2048 + 16, 32),
            nn.ReLU(),
            nn.Linear(32, output_dim)
        )

    def forward(self, img_x, tab_x):
        img_features = self.cnn(img_x)
        tab_features = self.mlp(tab_x)
        combined = torch.cat((img_features, tab_features), dim=1)
        return self.classifier(combined)

# =====================================================================
# GENEROWANIE I BALANSOWANIE DANYCH TRENINGOWYCH
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
# GENEROWANIE RAPORTU DIAGNOSTYCZNEGO DLA PROCESU WALIDACJI (CNN)
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
        {"desc": "Pełna bateria, blisko minerał, daleka baza", "tab": [90.0, 12.0, 1.0, 1.0, 3.0, 20.0, 2.0], "cat": "sand"},
        {"desc": "Słaba bateria (30%), stacja bardzo daleko (18 pól) -> Krytyczny powrót", "tab": [30.0, 12.0, 1.0, 1.0, 5.0, 18.0, 1.0], "cat": "sand"},
        {"desc": "Średnia bateria (40%), stacja blisko (5 pól) -> Bezpieczna regeneracja", "tab": [40.0, 8.0, 0.5, 0.8, 2.0, 5.0, 4.0], "cat": "rock"},
        {"desc": "Bateria 80%, pełny ekwipunek (8/8) -> Nakaz powrotu do bazy i sprzedaży", "tab": [80.0, 14.0, 0.9, 1.0, 4.0, 10.0, 8.0], "cat": "base"}
    ]
    
    model.eval()
    terminal_summary = []
    
    for i, sc in enumerate(scenarios, 1):
        test_input = np.array([sc["tab"]])
        test_input_scaled = scaler.transform(test_input)
        tab_tensor = torch.tensor(test_input_scaled, dtype=torch.float32)
        
        img_tensor = get_ue5_image(sc["cat"], is_training=False).unsqueeze(0)
        
        with torch.no_grad():
            output = model(img_tensor, tab_tensor)
            pred_idx = torch.argmax(output, dim=1).item()
            decision = reverse_mapping[pred_idx]
            
        full_report.append(f"Scenariusz {i}: {sc['desc']}")
        full_report.append(f"  Wejście: Bat={sc['tab'][0]}%, DystStacja={sc['tab'][5]}, Ekwipunek={sc['tab'][6]}/8, Środowisko: {sc['cat'].upper()}")
        full_report.append(f"  Decyzja Sieci: {decision}")
        full_report.append("-" * 50)
        
        terminal_summary.append(
            f" Scenariusz {i} (Bat: {sc['tab'][0]}%, Wiz: {sc['cat'].upper()}) -> Decyzja: \033[92m{decision}\033[0m"
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
# INICJALIZACJA I PROCES UCZENIA MULTIMODALNEJ SIECI CNN + MLP
# =====================================================================
print("[SYSTEM] Inicjalizacja rdzenia decyzyjnego opartego o sieci CNN...")

raw_dataset = generate_balanced_dataset(1000)

print("[SYSTEM] Parowanie i wczytywanie obrazów UE5 dla zbioru uczącego...")
images_list = []
for idx, row in raw_dataset.iterrows():
    dist_station = row["dist_to_station"]
    t_type = int(row["terrain_type"])
    
    if dist_station <= 1 and row["target_decision"] == "GO_TO_CHARGE":
        category = random.choice(["station", "base"])
    else:
        if t_type == 1:
            category = "rock"
        elif t_type == 2:
            category = "crater"
        else:
            category = "sand"
            
    images_list.append(get_ue5_image(category, is_training=True))

X_img_tensor = torch.stack(images_list)

tabular_features = [
    "battery_level", "time_of_day", "solar_efficiency", 
    "weather_multiplier", "dist_to_mineral", 
    "dist_to_station", "inventory_size"
]

X_raw = raw_dataset[tabular_features].values
class_mapping = {"GO_TO_CHARGE": 0, "CONTINUE_MINING": 1}
reverse_mapping = {0: "GO_TO_CHARGE", 1: "CONTINUE_MINING"}
y_raw = raw_dataset["target_decision"].map(class_mapping).values

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_raw)

# Spójny podział danych na zbiór treningowy i walidacyjny
indices = np.arange(len(raw_dataset))
train_idx, val_idx = train_test_split(indices, test_size=0.2, random_state=42)

X_train_img = X_img_tensor[train_idx]
X_val_img = X_img_tensor[val_idx]

X_train_tab = torch.tensor(X_scaled[train_idx], dtype=torch.float32)
X_val_tab = torch.tensor(X_scaled[val_idx], dtype=torch.float32)

y_train = y_raw[train_idx]
y_val = y_raw[val_idx] # <--- NAPRAWIONE (Zdefiniowanie tablicy y_val dla scikit-learn)

y_train_tensor = torch.tensor(y_train, dtype=torch.long)
y_val_tensor = torch.tensor(y_val, dtype=torch.long)

# Inicjalizacja sieci wielowejściowej
trained_nn = MissionControlCNN(tabular_dim=7, output_dim=2)
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(trained_nn.parameters(), lr=0.001)

trained_nn.train()
epochs = 30
batch_size = 64

print("[SYSTEM] Trening sieci CNN + MLP w toku...")
for epoch in range(epochs):
    permutation = torch.randperm(X_train_img.size()[0])
    epoch_loss = 0.0
    for i in range(0, X_train_img.size()[0], batch_size):
        batch_indices = permutation[i:i+batch_size]
        batch_img = X_train_img[batch_indices]
        batch_tab = X_train_tab[batch_indices]
        batch_y = y_train_tensor[batch_indices]
        
        optimizer.zero_grad()
        outputs = trained_nn(batch_img, batch_tab)
        loss = criterion(outputs, batch_y)
        loss.backward()
        optimizer.step()
        epoch_loss += loss.item()
        
    if (epoch + 1) % 10 == 0:
        print(f"  Epoka {epoch+1:02d}/{epochs} | Średni błąd loss: {epoch_loss / (X_train_img.size()[0]/batch_size):.4f}")

trained_nn.eval()
with torch.no_grad():
    val_outputs = trained_nn(X_val_img, X_val_tab)
    _, predicted = torch.max(val_outputs, 1)
    y_pred = predicted.numpy()

val_metrics_text = classification_report(y_val, y_pred, target_names=list(class_mapping.keys()))

run_diagnostic_report(trained_nn, scaler, class_mapping, reverse_mapping, val_metrics_text)

print("[SYSTEM] Wielowejściowa sieć neuronowa została pomyślnie wytrenowana i zsynchronizowana.")

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
        agent=agent.to_dict(env),
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