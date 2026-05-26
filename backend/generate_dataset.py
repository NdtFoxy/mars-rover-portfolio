import numpy as np
import pandas as pd
import random
# Zaimportuj swoje klasy z aplikacji (może być konieczne dostosowanie ścieżek)
from app.core.environment import Environment 
from app.core.decision_tree_agent import DecisionTreeAgent # lub search_agent

def get_surroundings(env, rx, ry):
    """Zwraca 8 sąsiednich pól (0 - wolne, 1 - przeszkoda)"""
    surr = []
    directions = [
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)
    ]
    for dx, dy in directions:
        nx, ny = rx + dx, ry + dy
        # Jeśli pole jest poza granicami lub znajduje się tam przeszkoda
        if env.is_obstacle(nx, ny) or not env.is_within_bounds(nx, ny):
            surr.append(1)
        else:
            surr.append(0)
    return surr

def collect_data():
    # Potrzebujemy po 1000 przykładów na klasę
    classes_count = {0: 0, 1: 0, 2: 0, 3: 0}
    required_per_class = 1050 # z małym zapasem
    dataset = []

    action_mapping = {"UP": 0, "DOWN": 1, "LEFT": 2, "RIGHT": 3}

    while any(count < required_per_class for count in classes_count.values()):
        # Inicjalizujemy losowe środowisko
        env = Environment(width=20, height=20, obstacle_density=0.2)
        agent = DecisionTreeAgent() # Twój agent ekspercki
        
        # Umieszczamy łazik i cel na wolnych polach
        rx, ry = env.get_random_free_position()
        tx, ty = env.get_random_free_position()
        
        env.set_rover_position(rx, ry)
        env.set_target_position(tx, ty)

        # Symulujemy ruch łazika
        steps = 0
        while steps < 100:
            if rx == tx and ry == ty:
                break
            
            # Pobieramy decyzję eksperta
            action = agent.decide_action(env, rx, ry, tx, ty) # nazwa metody może się różnić
            if action not in action_mapping:
                break
                
            action_idx = action_mapping[action]
            
            # Zbieramy cechy
            dx = np.sign(tx - rx)
            dy = np.sign(ty - ry)
            surr = get_surroundings(env, rx, ry)
            
            feature_row = [dx, dy] + surr + [action_idx]
            
            # Aby uniknąć dysproporcji w klasach, zapisujemy tylko wtedy, gdy limit nie został przekroczony
            if classes_count[action_idx] < required_per_class:
                dataset.append(feature_row)
                classes_count[action_idx] += 1
            
            # Przesuwamy agenta, aby kontynuować symulację
            rx, ry = env.move_agent(rx, ry, action)
            steps += 1

    # Zapisujemy do CSV
    columns = ['dx', 'dy', 's1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 'action']
    df = pd.DataFrame(dataset, columns=columns)
    df.to_csv('rover_training_data.csv', index=False)
    print("Zbieranie danych zakończone. Rozkład klas:", classes_count)

if __name__ == "__main__":
    collect_data()