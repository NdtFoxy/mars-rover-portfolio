import torch
import torch.nn as nn
import numpy as np
import pickle
import os

# Musi dokładnie odpowiadać architekturze podczas trenowania
class RoverClassifier(nn.Module):
    def __init__(self, input_size=10, num_classes=4):
        super(RoverClassifier, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(input_size, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, num_classes)
        )
        
    def forward(self, x):
        return self.network(x)

class NNAgent:
    def __init__(self):
        self.device = torch.device('cpu') # Do inferencji na FastAPI CPU w zupełności wystarczy i jest szybsze pod względem czasu reakcji
        self.model = RoverClassifier()
        
        # Ładowanie ścieżek względnych do folderu backend
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # app/
        model_path = os.path.join(base_dir, 'core', 'rover_nn_model.pth')
        scaler_path = os.path.join(os.path.dirname(base_dir), 'scaler.pkl')
        
        if os.path.exists(model_path) and os.path.exists(scaler_path):
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
            self.model.eval()
            with open(scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
            self.model_loaded = True
            print("Model sieci neuronowej został pomyślnie załadowany przez agenta.")
        else:
            self.model_loaded = False
            print("Uwaga: Pliki modelu lub skalera nie zostały znalezione. Agent nie będzie mógł generować przewidywań.")

    def get_surroundings(self, env, rx, ry):
        surr = []
        directions = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1)
        ]
        for dx, dy in directions:
            nx, ny = rx + dx, ry + dy
            if env.is_obstacle(nx, ny) or not env.is_within_bounds(nx, ny):
                surr.append(1)
            else:
                surr.append(0)
        return surr

    def decide_action(self, env, rx, ry, tx, ty):
        if not self.model_loaded:
            # Akcja rezerwowa, jeśli model nie został załadowany
            return "STAY"
            
        # Przygotowanie danych wejściowych
        dx = np.sign(tx - rx)
        dy = np.sign(ty - ry)
        surr = self.get_surroundings(env, rx, ry)
        
        features = np.array([[dx, dy] + surr])
        
        # Normalizacja
        features_scaled = self.scaler.transform(features)
        
        # Predykcja sieci neuronowej
        features_t = torch.tensor(features_scaled, dtype=torch.float32).to(self.device)
        with torch.no_grad():
            outputs = self.model(features_t)
            _, predicted = torch.max(outputs, 1)
            action_idx = predicted.item()
            
        action_mapping = {0: "UP", 1: "DOWN", 2: "LEFT", 3: "RIGHT"}
        return action_mapping.get(action_idx, "STAY")