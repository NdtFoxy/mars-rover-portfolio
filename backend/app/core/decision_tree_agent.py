import random
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.tree import DecisionTreeClassifier, export_text, plot_tree

# ИЗМЕНЕНО: Добавлены точки для работы в составе пакета
from .environment import Environment, Mineral, ChargingStation
from .agent import Agent

def generate_dataset(num_samples: int = 500) -> pd.DataFrame:
    data =[]
    
    for _ in range(num_samples):
        env = Environment(width=20, height=15)
        
        # losowa modyfikacja czasu i pogody
        env.step_counter = random.randint(0, 1000)
        env.time_of_day = env.step_counter % 24
        env.weather = random.choice(env.WEATHER_CONDITIONS)
        
        x, y = env._get_free_sand_position()
        agent = Agent(x, y)
        agent.battery = random.uniform(5.0, 100.0)
        agent.inventory = ["Titanium"] * random.randint(0, 8)
        
        # Atrybut 1: Poziom baterii
        battery_level = agent.battery

        # Atrybut 2: Pora dnia
        time_of_day = env.time_of_day

        # Atrybut 3: Efektywność ładowania słonecznego
        solar_efficiency = agent._calculate_solar_efficiency(time_of_day)

        # Atrybut 4: Mnożnik pogody
        weather_multiplier = agent.WEATHER_MULTIPLIERS.get(env.weather, 1.0)

        # Atrybut 5: Typ terenu pod agentem
        terrain_type = env.get_terrain_type(agent.x, agent.y)

        # Atrybut 6: Dystans (Manhattan) do najbliższego minerału
        active_minerals = [m for m in env.objects if m.type in ["Titanium", "Water Ice", "Hematite"] and m.is_active]
        dist_mineral = min([abs(agent.x - m.x) + abs(agent.y - m.y) for m in active_minerals]) if active_minerals else 100

        # Atrybut 7: Dystans (Manhattan) do najbliższej stacji ładującej
        active_stations = [s for s in env.objects if s.type == "ChargingStation" and s.is_active]
        dist_station = min([abs(agent.x - s.x) + abs(agent.y - s.y) for s in active_stations]) if active_stations else 100
        
        # Atrybut 8: Zajętość ekwipunku
        inventory_size = len(agent.inventory)
        
        if battery_level < 45:
            decision = "GO_TO_CHARGE"
        elif battery_level < 40 and weather_multiplier < 0.5: # Zła pogoda, mało prąду
            decision = "GO_TO_CHARGE"
        elif battery_level < 60 and dist_mineral > 10 and dist_station < 5: # Daleko do celu, stacja blisko
            decision = "GO_TO_CHARGE"
        elif inventory_size >= 8: # Pełen ekwipunek
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
            "inventory_size": inventory_size,
            "target_decision": decision
        })
        
    return pd.DataFrame(data)

def run_decision_tree_experiment():
    print("Trwa generowanie zbioru uczącego (500 przykładów)...")
    df = generate_dataset(500)
    
    # Rozdzielenie na zbiór atrybutów opisujących (X) i decyzję (y)
    feature_names = [
        "battery_level", "time_of_day", "solar_efficiency", 
        "weather_multiplier", "terrain_type", "dist_to_mineral", 
        "dist_to_station", "inventory_size"
    ]
    X = df[feature_names]
    y = df["target_decision"]
    
    print("Trwa uczenie drzewa decyzyjnego...")
    # criterion='entropy' wybor atrybutu o

    clf = DecisionTreeClassifier(criterion='entropy', max_depth=4, random_state=42)
    clf.fit(X, y)

    # Reprezentacja w logach
    print("\n" + "-"*50)
    print("Logi:")
    print("-"*50)
    tree_rules = export_text(clf, feature_names=feature_names)
    print(tree_rules)
    
    # Reprezentacja graficzna
    print("\nGenerowanie graficznej reprezentacji drzewa... (Sprawdź nowe okno)")
    plt.figure(figsize=(16, 9))
    plot_tree(
        clf, 
        feature_names=feature_names, 
        class_names=clf.classes_, 
        filled=True, 
        rounded=True, 
        fontsize=10
    )
    plt.title("Drzewo decyzyjne - ID3", fontsize=15)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    run_decision_tree_experiment()