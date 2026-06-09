# -*- coding: utf-8 -*-
"""
Zadanie 6 — sieć neuronowa (CNN + MLP).
Зadanie 6 — нейронная сеть (CNN + MLP).

Wejście stanowi obraz z kamery UE5 (gałąź CNN) oraz 7 cech telemetrii
(gałąź MLP). Zbiór uczący zawiera co najmniej 1000 przykładów na klasę.
На вход идёт изображение с камеры UE5 (ветка CNN) и 7 признаков телеметрии
(ветка MLP). Обучающий набор содержит как минимум 1000 примеров на класс.

Funkcja `train_cnn()` trenuje sieć i zwraca `(model, scaler, reverse_mapping)`.
Функция `train_cnn()` обучает сеть и возвращает `(model, scaler, reverse_mapping)`.

Serwer uruchamia ją tylko wtedy, gdy aktywne jest zadanie 6.
Сервер запускает её только тогда, когда активно задание 6.
"""
import random
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from PIL import Image
import torchvision.transforms as transforms

from zadania.zadanie_5_DrzewoDecyzyjne.drzewo import generate_dataset

BACKEND_DIR = Path(__file__).resolve().parents[2]
UE5_PHOTOS_DIR = BACKEND_DIR / "ue5_photos"

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


def get_ue5_image(category: str, is_training: bool = True) -> torch.Tensor:
    folder_path = UE5_PHOTOS_DIR / category
    fallback_tensor = torch.zeros((3, 32, 32))
    if not folder_path.is_dir():
        return fallback_tensor
    files = [
        path for path in folder_path.iterdir()
        if path.suffix.lower() in {".png", ".jpg", ".jpeg"}
    ]
    if not files:
        return fallback_tensor
    img_path = random.choice(files)
    try:
        img = Image.open(img_path).convert('RGB')
        return train_transforms(img) if is_training else val_transforms(img)
    except Exception as e:
        print(f"[OSTRZEZENIE] Blad wczytywania obrazu {img_path}: {e}")
        return fallback_tensor


class MissionControlCNN(nn.Module):
    def __init__(self, tabular_dim=7, output_dim=2):
        super(MissionControlCNN, self).__init__()
        # GALAZ 1 (WIZJA): splotowa siec na obrazie 3x32x32 z kamery UE5.
        # Conv2d wykrywa cechy przestrzenne (krawedzie, tekstury), MaxPool zmniejsza wymiar.
        self.cnn = nn.Sequential(
            nn.Conv2d(in_channels=3, out_channels=16, kernel_size=3, padding=1),   # 3 kanaly RGB -> 16 map cech
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2),                                           # 32x32 -> 16x16
            nn.Conv2d(in_channels=16, out_channels=32, kernel_size=3, padding=1),  # 16 -> 32 mapy cech
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2),                                           # 16x16 -> 8x8
            nn.Flatten()                                                          # 32*8*8 = 2048 liczb
        )
        # GALAZ 2 (TELEMETRIA): maly MLP na 7 cechach liczbowych (bateria, dystanse, pogoda...).
        self.mlp = nn.Sequential(nn.Linear(tabular_dim, 16), nn.ReLU())
        # FUZJA + KLASYFIKATOR: laczy 2048 (obraz) + 16 (telemetria) -> decyzja (2 klasy).
        self.classifier = nn.Sequential(
            nn.Linear(2048 + 16, 32), nn.ReLU(), nn.Linear(32, output_dim)
        )

    def forward(self, img_x, tab_x):
        img_features = self.cnn(img_x)     # cechy wizualne z kamery (2048)
        tab_features = self.mlp(tab_x)     # cechy z telemetrii (16)
        combined = torch.cat((img_features, tab_features), dim=1)   # FUZJA: sklej oba wektory
        return self.classifier(combined)   # wynik: logity dla GO_TO_CHARGE / CONTINUE_MINING


def generate_balanced_dataset(
    required_per_class: int = 1000,
    output_path: str | Path | None = None,
):
    print(f"[SYSTEM] Generowanie zbalansowanego zbioru danych (min. {required_per_class} próbek na klasę)...")
    accumulated_rows = []
    counts = {"GO_TO_CHARGE": 0, "CONTINUE_MINING": 0}
    while counts["GO_TO_CHARGE"] < required_per_class or counts["CONTINUE_MINING"] < required_per_class:
        batch = generate_dataset(500)
        for _, row in batch.iterrows():
            dist = row["dist_to_station"]
            battery = row["battery_level"]
            inventory_fill_ratio = row["inventory_fill_ratio"]
            safety_margin = 30.0
            energy_needed_to_return = (dist * 2.5) + safety_margin
            if battery < energy_needed_to_return or inventory_fill_ratio >= 0.95:
                corrected_decision = "GO_TO_CHARGE"
            else:
                corrected_decision = row["target_decision"]
            if corrected_decision in counts and counts[corrected_decision] < required_per_class:
                new_row = row.to_dict()
                new_row["target_decision"] = corrected_decision
                accumulated_rows.append(new_row)
                counts[corrected_decision] += 1
    df_balanced = pd.DataFrame(accumulated_rows)
    dataset_path = Path(output_path) if output_path else BACKEND_DIR / "rover_training_data.csv"
    dataset_path.parent.mkdir(parents=True, exist_ok=True)
    df_balanced.to_csv(dataset_path, index=False)
    print(f"[SYSTEM] Dane treningowe zapisano do '{dataset_path}'.")
    return df_balanced


def run_diagnostic_report(
    model,
    scaler,
    class_mapping,
    reverse_mapping,
    val_metrics_text,
    output_path: str | Path | None = None,
):
    full_report = ["=" * 80,
                   "  SZCZEGÓŁOWY RAPORT DIAGNOSTYCZNY MODELU SIECI NEURONOWEJ (ARES-ML)",
                   "=" * 80, "\n[1. METRYKI KLASYFIKACJI WALIDACYJNEJ]:\n", val_metrics_text,
                   "\n" + "=" * 80, "[2. SYMULACJA SCENARIUSZY TESTOWYCH - ANALIZA BEZPIECZEŃSTWA]:\n"]
    scenarios = [
        {"desc": "Pełna bateria, blisko minerał, daleka baza", "tab": [90.0, 12.0, 1.0, 1.0, 3.0, 20.0, 0.2], "cat": "sand"},
        {"desc": "Słaba bateria (30%), stacja bardzo daleko -> Krytyczny powrót", "tab": [30.0, 12.0, 1.0, 1.0, 5.0, 18.0, 0.1], "cat": "sand"},
        {"desc": "Średnia bateria (40%), stacja blisko -> Bezpieczna regeneracja", "tab": [40.0, 8.0, 0.5, 0.8, 2.0, 5.0, 0.5], "cat": "rock"},
        {"desc": "Bateria 80%, pełny plecak -> Powrót do bazy i sprzedaż", "tab": [80.0, 14.0, 0.9, 1.0, 4.0, 10.0, 0.97], "cat": "base"},
    ]
    model.eval()
    terminal_summary = []
    for i, sc in enumerate(scenarios, 1):
        test_input_scaled = scaler.transform(np.array([sc["tab"]]))
        tab_tensor = torch.tensor(test_input_scaled, dtype=torch.float32)
        img_tensor = get_ue5_image(sc["cat"], is_training=False).unsqueeze(0)
        with torch.no_grad():
            output = model(img_tensor, tab_tensor)
            decision = reverse_mapping[torch.argmax(output, dim=1).item()]
        full_report.append(f"Scenariusz {i}: {sc['desc']}")
        full_report.append(f"  Wejście: Bat={sc['tab'][0]}%, DystStacja={sc['tab'][5]}, Plecak={sc['tab'][6]*100:.0f}%, Środowisko: {sc['cat'].upper()}")
        full_report.append(f"  Decyzja Sieci: {decision}")
        full_report.append("-" * 50)
        terminal_summary.append(f" Scenariusz {i} (Bat: {sc['tab'][0]}%, Wiz: {sc['cat'].upper()}) -> Decyzja: \033[92m{decision}\033[0m")
    full_report.append("\n[KONIEC RAPORTU]")
    report_path = Path(output_path) if output_path else BACKEND_DIR / "nn_model_report.txt"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(full_report))
    print("\n" + "=" * 70)
    print(f"  SKRÓCONY RAPORT SIECI NEURONOWEJ (Pełny w pliku '{report_path}')")
    print("=" * 70)
    print("[1. METRYKI WALIDACJI (DOKŁADNOŚĆ)]:")
    accuracy_line = next((l for l in val_metrics_text.split('\n') if "accuracy" in l), "Accuracy: OK")
    print(f"  {accuracy_line.strip()}")
    print("\n[2. PREdykcje SCENARIUSZY SCENICZNYCH]:")
    for s_line in terminal_summary:
        print(s_line)
    print("=" * 70 + "\n")


def train_cnn(
    data_path: str | Path | None = None,
    report_path: str | Path | None = None,
    required_per_class: int = 1000,
    epochs: int = 30,
):
    """Trenuje multimodalną sieć CNN+MLP. Zwraca (model, scaler, reverse_mapping).
    Обучает мультимодальную сеть CNN+MLP. Возвращает (model, scaler, reverse_mapping).
    """
    print("[SYSTEM] Inicjalizacja rdzenia decyzyjnego opartego o sieci CNN...")
    raw_dataset = generate_balanced_dataset(required_per_class, output_path=data_path)

    print("[SYSTEM] Parowanie i wczytywanie obrazów UE5 dla zbioru uczącego...")
    images_list = []
    for _, row in raw_dataset.iterrows():
        dist_station = row["dist_to_station"]
        t_type = int(row["terrain_type"])
        if dist_station <= 1 and row["target_decision"] == "GO_TO_CHARGE":
            category = random.choice(["station", "base"])
        elif t_type == 1:
            category = "rock"
        elif t_type == 2:
            category = "crater"
        else:
            category = "sand"
        images_list.append(get_ue5_image(category, is_training=True))
    X_img_tensor = torch.stack(images_list)

    tabular_features = ["battery_level", "time_of_day", "solar_efficiency",
                        "weather_multiplier", "dist_to_mineral", "dist_to_station",
                        "inventory_fill_ratio"]
    X_raw = raw_dataset[tabular_features].values
    class_mapping = {"GO_TO_CHARGE": 0, "CONTINUE_MINING": 1}
    reverse_mapping = {0: "GO_TO_CHARGE", 1: "CONTINUE_MINING"}
    y_raw = raw_dataset["target_decision"].map(class_mapping).values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_raw)

    indices = np.arange(len(raw_dataset))
    train_idx, val_idx = train_test_split(
        indices,
        test_size=0.2,
        random_state=42,
        stratify=y_raw,
    )
    X_train_img, X_val_img = X_img_tensor[train_idx], X_img_tensor[val_idx]
    X_train_tab = torch.tensor(X_scaled[train_idx], dtype=torch.float32)
    X_val_tab = torch.tensor(X_scaled[val_idx], dtype=torch.float32)
    y_train, y_val = y_raw[train_idx], y_raw[val_idx]
    y_train_tensor = torch.tensor(y_train, dtype=torch.long)

    trained_nn = MissionControlCNN(tabular_dim=7, output_dim=2)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(trained_nn.parameters(), lr=0.001)

    trained_nn.train()
    batch_size = 64
    print("[SYSTEM] Trening sieci CNN + MLP w toku...")
    for epoch in range(epochs):
        permutation = torch.randperm(X_train_img.size()[0])
        epoch_loss = 0.0
        for i in range(0, X_train_img.size()[0], batch_size):
            bi = permutation[i:i + batch_size]
            optimizer.zero_grad()
            outputs = trained_nn(X_train_img[bi], X_train_tab[bi])
            loss = criterion(outputs, y_train_tensor[bi])
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
        if (epoch + 1) % 10 == 0:
            print(f"  Epoka {epoch+1:02d}/{epochs} | Średni błąd loss: {epoch_loss / (X_train_img.size()[0]/batch_size):.4f}")

    trained_nn.eval()
    with torch.no_grad():
        val_outputs = trained_nn(X_val_img, X_val_tab)
        y_pred = torch.max(val_outputs, 1)[1].numpy()
    val_metrics_text = classification_report(y_val, y_pred, target_names=list(class_mapping.keys()))
    run_diagnostic_report(
        trained_nn,
        scaler,
        class_mapping,
        reverse_mapping,
        val_metrics_text,
        output_path=report_path,
    )
    print("[SYSTEM] Sieć neuronowa wytrenowana i zsynchronizowana.")
    return trained_nn, scaler, reverse_mapping
