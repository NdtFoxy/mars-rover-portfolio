import numpy as np
import pandas as pd
import random
# Импортируйте ваши классы из приложения (может потребоваться настроить пути)
from app.core.environment import Environment 
from app.core.decision_tree_agent import DecisionTreeAgent # или search_agent

def get_surroundings(env, rx, ry):
    """Возвращает 8 соседних клеток (0 - свободно, 1 - препятствие)"""
    surr = []
    directions = [
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)
    ]
    for dx, dy in directions:
        nx, ny = rx + dx, ry + dy
        # Если клетка за пределами или там препятствие
        if env.is_obstacle(nx, ny) or not env.is_within_bounds(nx, ny):
            surr.append(1)
        else:
            surr.append(0)
    return surr

def collect_data():
    # Нам нужно по 1000 примеров на класс
    classes_count = {0: 0, 1: 0, 2: 0, 3: 0}
    required_per_class = 1050 # с небольшим запасом
    dataset = []

    action_mapping = {"UP": 0, "DOWN": 1, "LEFT": 2, "RIGHT": 3}

    while any(count < required_per_class for count in classes_count.values()):
        # Инициализируем случайную среду
        env = Environment(width=20, height=20, obstacle_density=0.2)
        agent = DecisionTreeAgent() # Ваш экспертный агент
        
        # Размещаем ровер и цель в свободные клетки
        rx, ry = env.get_random_free_position()
        tx, ty = env.get_random_free_position()
        
        env.set_rover_position(rx, ry)
        env.set_target_position(tx, ty)

        # Симулируем поездку ровера
        steps = 0
        while steps < 100:
            if rx == tx and ry == ty:
                break
            
            # Получаем решение эксперта
            action = agent.decide_action(env, rx, ry, tx, ty) # название метода может отличаться
            if action not in action_mapping:
                break
                
            action_idx = action_mapping[action]
            
            # Собираем фичи
            dx = np.sign(tx - rx)
            dy = np.sign(ty - ry)
            surr = get_surroundings(env, rx, ry)
            
            feature_row = [dx, dy] + surr + [action_idx]
            
            # Чтобы не было перекоса в классах, сохраняем только если лимит не превышен
            if classes_count[action_idx] < required_per_class:
                dataset.append(feature_row)
                classes_count[action_idx] += 1
            
            # Перемещаем агента для продолжения симуляции
            rx, ry = env.move_agent(rx, ry, action)
            steps += 1

    # Сохраняем в CSV
    columns = ['dx', 'dy', 's1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 'action']
    df = pd.DataFrame(dataset, columns=columns)
    df.to_csv('rover_training_data.csv', index=False)
    print("Сбор данных завершен. Распределение по классам:", classes_count)

if __name__ == "__main__":
    collect_data()