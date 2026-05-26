import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import pickle

# Definicja architektury sieci
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

def train():
    # Wczytywanie danych
    df = pd.read_csv('rover_training_data.csv')
    X = df.drop(columns=['action']).values
    y = df['action'].values
    
    # Podział na zbiór treningowy i testowy
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Normalizacja danych
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)
    
    # Zapisujemy skaler, aby użyć go podczas inferencji agenta
    with open('scaler.pkl', 'wb') as f:
        pickle.dump(scaler, f)
        
    # Konwersja na tensory PyTorch
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Urządzenie używane do treningu: {device}")
    
    X_train_t = torch.tensor(X_train, dtype=torch.float32).to(device)
    y_train_t = torch.tensor(y_train, dtype=torch.long).to(device)
    X_test_t = torch.tensor(X_test, dtype=torch.float32).to(device)
    y_test_t = torch.tensor(y_test, dtype=torch.long).to(device)
    
    train_dataset = TensorDataset(X_train_t, y_train_t)
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    
    # Inicjalizacja modelu
    model = RoverClassifier().to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.005)
    
    # Pętla treningowa
    epochs = 50
    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        for inputs, labels in train_loader:
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()
            
        # Walidacja
        model.eval()
        with torch.no_grad():
            test_outputs = model(X_test_t)
            _, predicted = torch.max(test_outputs, 1)
            accuracy = (predicted == y_test_t).sum().item() / y_test_t.size(0)
            
        if (epoch+1) % 10 == 0:
            print(f"Epoka {epoch+1}/{epochs} | Loss: {running_loss/len(train_loader):.4f} | Accuracy: {accuracy*100:.2f}%")
            
    # Zapisywanie wag modelu
    torch.save(model.state_dict(), 'app/core/rover_nn_model.pth')
    print("Model został pomyślnie zapisany w app/core/rover_nn_model.pth")

if __name__ == "__main__":
    train()