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
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .models import GameState
from .core.environment import Environment, MINERAL_TYPES
from .core.agent import Agent
from .core.decision_tree_agent import generate_dataset
from .core import shop
from .core.knapsack import items_from_minerals, compare_knapsack

router = APIRouter()

# =====================================================================
# TRANSFORMACJE OBRAZÓW (W TYM AUGMENTACJA DLA TRENINGU)
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

# =====================================================================
# WIELOWEJŚCIOWA ARCHITEKTURA SIECI NEURONOWEJ (MULTIMODAL CNN + MLP)
# Wejście: obraz z kamery UE5 (CNN) + 7 cech telemetrycznych (MLP).
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
            inventory_fill_ratio = row["inventory_fill_ratio"]

            # 🚨 NAPRAWA BŁĘDU ŚMIERCI
            # Dystans * 2.5 (bo skały kosztują 2.0, a obrót 1.0)
            # Żelazna rezerwa 30.0% na wypadek nocy (brak słońca po 20:00)
            safety_margin = 30.0
            energy_needed_to_return = (dist * 2.5) + safety_margin

            if battery < energy_needed_to_return or inventory_fill_ratio >= 0.95:
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
# RAPORT DIAGNOSTYCZNY MODELU (metryki + scenariusze testowe dla CNN+MLP)
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

    # tab = 7 cech: [bateria%, czas, słońce, pogoda, dyst.minerał, dyst.stacja, zapełnienie plecaka]
    scenarios = [
        {"desc": "Pełna bateria, blisko minerał, daleka baza", "tab": [90.0, 12.0, 1.0, 1.0, 3.0, 20.0, 0.2], "cat": "sand"},
        {"desc": "Słaba bateria (30%), stacja bardzo daleko (18 pól) -> Krytyczny powrót", "tab": [30.0, 12.0, 1.0, 1.0, 5.0, 18.0, 0.1], "cat": "sand"},
        {"desc": "Średnia bateria (40%), stacja blisko (5 pól) -> Bezpieczna regeneracja", "tab": [40.0, 8.0, 0.5, 0.8, 2.0, 5.0, 0.5], "cat": "rock"},
        {"desc": "Bateria 80%, pełny plecak (~100%) -> Nakaz powrotu do bazy i sprzedaży", "tab": [80.0, 14.0, 0.9, 1.0, 4.0, 10.0, 0.97], "cat": "base"}
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
        full_report.append(f"  Wejście: Bat={sc['tab'][0]}%, DystStacja={sc['tab'][5]}, Plecak={sc['tab'][6]*100:.0f}%, Środowisko: {sc['cat'].upper()}")
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

# 7 cech telemetrycznych (tabularne wejście MLP)
tabular_features = [
    "battery_level", "time_of_day", "solar_efficiency",
    "weather_multiplier", "dist_to_mineral",
    "dist_to_station", "inventory_fill_ratio"
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
y_val = y_raw[val_idx]

y_train_tensor = torch.tensor(y_train, dtype=torch.long)
y_val_tensor = torch.tensor(y_val, dtype=torch.long)

# Inicjalizacja sieci wielowejściowej (7 cech tabularnych + obraz)
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

    add_metric(stats, "NN THOUGHT", thought)

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
    selected_act = "MINING" if mining_p > charge_p else "CHARGE"

    decision = Table.grid(expand=True)
    decision.add_column(no_wrap=True)
    decision.add_column(ratio=1)
    add_metric(decision, "TELEMETRIA", f"Bat:{b_val:.0f}% | Czas:{environment.time_of_day:.1f}h | Pogoda:{weather_mult:.1f}")
    add_metric(decision, "SIEĆ", "CNN (obraz UE5 32x32) + MLP (7 cech)")
    add_metric(decision, "PROB", f"MINING {mining_p:.1f}% | CHARGE {charge_p:.1f}%")
    add_metric(decision, "DECYZJA SIECI", f"-> {selected_act} (Aktywny)")

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
            title="MARS | SPACE LABORATORY (NEURAL NET ACTIVE)",
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
            title="SYSTEM DECYZYJNY (CNN + MLP)",
            border_style="magenta",
            box=box.SQUARE,
            width=dashboard_width,
        )
    )
    console.print(Panel(footer, border_style="bright_black", box=box.SIMPLE, width=dashboard_width))
    console.print(Panel(legend, border_style="bright_black", box=box.SIMPLE, width=dashboard_width))

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
        objects=env_dict["objects"],
        shop=shop.get_shop_state(agent)
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

# =====================================================================
# SKLEP Z ULEPSZENIAMI (Shop)
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
    """Ręczny zakup ulepszenia (pieniądze + materiały)."""
    result = shop.purchase_upgrade(agent, upgrade_id)
    result["money"] = round(agent.money, 2)
    result["items"] = shop.get_shop_state(agent)
    return result

# =====================================================================
# PROBLEM PLECAKOWY (Knapsack): porównanie GA vs DP na bieżącej mapie
# =====================================================================
@router.get("/knapsack")
async def knapsack_compare():
    """
    Rozwiązuje problem plecakowy dla aktualnie widocznych minerałów (limit =
    wolne miejsce w plecaku) dwoma metodami i zwraca porównanie GA vs DP.
    """
    active = [m for m in env.objects if m.is_active and m.type in MINERAL_TYPES]
    items = items_from_minerals(active)
    # Kompresor zmniejsza efektywną objętość przenoszonych minerałów
    for it in items:
        it.volume *= agent.volume_factor
    rem_w = max(0.0, agent.capacity - agent.current_weight())
    rem_v = max(0.0, agent.volume_capacity - agent.current_volume())
    return compare_knapsack(items, rem_w, rem_v)
