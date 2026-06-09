# -*- coding: utf-8 -*-
"""
Zadanie 5 — drzewo decyzyjne (ID3 / przyrost informacji).
Задanie 5 — дерево решений (ID3 / прирост информации).

Moduł generuje zbiór uczący telemetrii łazika i trenuje drzewo decyzyjne
(`criterion="entropy"` oznacza wybór atrybutu wg przyrostu informacji).
Модуль генерирует обучающий набор телеметрии ровера и обучает дерево решений
(`criterion="entropy"` означает выбор признака по приросту информации).

To jest model bazowy używany przez serwer, gdy nie działa zadanie 6.
Это базовая модель, которую использует сервер, когда неактивно задание 6.
"""
import math
import random
from typing import Any, Dict, Tuple

import pandas as pd
from sklearn.tree import DecisionTreeClassifier

from app.core.environment import Environment, MINERAL_TYPES

# 8 atrybutów opisujących decyzję (wymóg: >= 8)
# 8 признаков описывающих решение (требование: >= 8)
FEATURES = [
    "battery_level", "time_of_day", "solar_efficiency", "weather_multiplier",
    "terrain_type", "dist_to_mineral", "dist_to_station", "inventory_fill_ratio",
]

WEATHER_MULTIPLIERS = {
    "Clear_Skies": 1.0,
    "Partly_Cloudy": 0.8,
    "Cloudy": 0.5,
    "Foggy": 0.3,
    "Sand_Dust_Calm": 0.2,
    "Sand_Dust_Storm": 0.1,
}


def calculate_solar_efficiency(time_of_day: float) -> float:
    if 6 <= time_of_day <= 20:
        return math.sin((time_of_day - 6) / 14.0 * math.pi)
    return 0.0


def _nearest_distance(agent: Any, objects: list[Any], allowed_types: set[str]) -> float:
    matching = [
        obj for obj in objects
        if getattr(obj, "is_active", False) and getattr(obj, "type", None) in allowed_types
    ]
    if not matching:
        return 100.0
    return float(min(abs(agent.x - obj.x) + abs(agent.y - obj.y) for obj in matching))


def extract_live_features(agent: Any, env: Environment) -> Dict[str, float]:
    """Buduje te same 8 cech dla działającego łazika, które wykorzystano do treningu.
    Строит те же 8 признаков для работающего ровера, что использовались при обучении.
    """
    weight_fill = agent.current_weight() / agent.capacity if agent.capacity > 0 else 1.0
    volume_fill = (
        agent.current_volume() / agent.volume_capacity
        if agent.volume_capacity > 0 else 1.0
    )
    return {
        "battery_level": agent.battery / agent.max_battery * 100.0 if agent.max_battery > 0 else 0.0,
        "time_of_day": float(env.time_of_day),
        "solar_efficiency": calculate_solar_efficiency(env.time_of_day),
        "weather_multiplier": WEATHER_MULTIPLIERS.get(env.weather, 1.0),
        "terrain_type": float(env.get_terrain_type(agent.x, agent.y)),
        "dist_to_mineral": _nearest_distance(agent, env.objects, set(MINERAL_TYPES)),
        "dist_to_station": _nearest_distance(agent, env.objects, {"ChargingStation"}),
        "inventory_fill_ratio": max(weight_fill, volume_fill),
    }


def predict_with_tree(
    clf: DecisionTreeClassifier, agent: Any, env: Environment
) -> Tuple[str, Dict[str, float]]:
    """Zwraca decyzję drzewa i prawdopodobieństwa w formacie używanym przez UI.
    Возвращает решение дерева и вероятности в формате, который использует UI.
    """
    sample = pd.DataFrame([extract_live_features(agent, env)], columns=FEATURES)
    decision = str(clf.predict(sample)[0])
    class_probabilities = {
        str(label): float(probability * 100.0)
        for label, probability in zip(clf.classes_, clf.predict_proba(sample)[0])
    }
    confidence = {
        "MINING": class_probabilities.get("CONTINUE_MINING", 0.0),
        "CHARGE": class_probabilities.get("GO_TO_CHARGE", 0.0),
    }
    return decision, confidence


def generate_dataset(num_samples: int = 500) -> pd.DataFrame:
    data = []
    for _ in range(num_samples):
        env = Environment(width=20, height=15)
        env.step_counter = random.randint(0, 1000)
        env.time_of_day = env.step_counter % 24
        env.weather = random.choice(env.WEATHER_CONDITIONS)

        traversable = [
            (x, y)
            for y in range(env.height)
            for x in range(env.width)
            if env.get_terrain_type(x, y) != 2
        ]
        x, y = random.choice(traversable)
        battery_level = random.uniform(5.0, 100.0)
        inventory_fill_ratio = round(random.uniform(0.0, 1.0), 3)

        time_of_day = env.time_of_day
        solar_efficiency = calculate_solar_efficiency(time_of_day)
        weather_multiplier = WEATHER_MULTIPLIERS.get(env.weather, 1.0)
        terrain_type = env.get_terrain_type(x, y)

        active_minerals = [m for m in env.objects if m.type in MINERAL_TYPES and m.is_active]
        dist_mineral = min([abs(x - m.x) + abs(y - m.y) for m in active_minerals]) if active_minerals else 100

        active_stations = [s for s in env.objects if s.type == "ChargingStation" and s.is_active]
        dist_station = min([abs(x - s.x) + abs(y - s.y) for s in active_stations]) if active_stations else 100

        if battery_level < 20:
            decision = "GO_TO_CHARGE"
        elif battery_level < 60 and weather_multiplier <= 0.5:
            decision = "GO_TO_CHARGE"
        elif battery_level < 50 and solar_efficiency < 0.3:
            decision = "GO_TO_CHARGE"
        elif inventory_fill_ratio >= 0.95:
            decision = "GO_TO_CHARGE"
        elif dist_mineral > 15 and battery_level < 70 and solar_efficiency < 0.5:
            decision = "GO_TO_CHARGE"
        else:
            decision = "CONTINUE_MINING"

        data.append({
            "battery_level": battery_level,
            "time_of_day": time_of_day,
            "solar_efficiency": solar_efficiency,
            "weather_multiplier": weather_multiplier,
            "terrain_type": terrain_type,
            "dist_to_mineral": dist_mineral,
            "dist_to_station": dist_station,
            "inventory_fill_ratio": inventory_fill_ratio,
            "target_decision": decision,
        })
    return pd.DataFrame(data)


def train_tree(num_samples: int = 400, random_state: int = 42):
    """Trenuje drzewo decyzyjne (ID3/entropia). Zwraca `(model, lista_cech)`.
    Обучает дерево решений (ID3/энтропия). Возвращает `(model, lista_cech)`.
    """
    previous_random_state = random.getstate()
    random.seed(random_state)
    try:
        df = generate_dataset(num_samples)
    finally:
        random.setstate(previous_random_state)
    # criterion="entropy" -> podzial wg PRZYROSTU INFORMACJI (to jest istota ID3).
    # max_depth=4 -> plytkie, czytelne drzewo (ogranicza przeuczenie, latwe do pokazania).
    clf = DecisionTreeClassifier(criterion="entropy", max_depth=4, random_state=42)
    clf.fit(df[FEATURES], df["target_decision"])   # uczenie na 8 cechach -> etykieta decyzji
    return clf, FEATURES


def run_decision_tree_experiment():
    import matplotlib.pyplot as plt
    from sklearn.tree import export_text, plot_tree

    print("Trwa generowanie zbioru uczącego (500 przykładów)...")
    df = generate_dataset(500)
    print(df.head(500))

    X = df[FEATURES]
    y = df["target_decision"]
    clf = DecisionTreeClassifier(criterion="entropy", max_depth=4, random_state=42)
    clf.fit(X, y)

    print("\n" + "-" * 50 + "\nLogi:\n" + "-" * 50)
    print(export_text(clf, feature_names=FEATURES))

    plt.figure(figsize=(16, 9))
    plot_tree(clf, feature_names=FEATURES, class_names=list(clf.classes_),
              filled=True, rounded=True, fontsize=10)
    plt.title("Drzewo decyzyjne (ID3 / entropia)")
    plt.tight_layout()
    plt.savefig("decision_tree.png", dpi=300)
    print("Grafika zapisana jako 'decision_tree.png'.")
    plt.show()


if __name__ == "__main__":
    run_decision_tree_experiment()
