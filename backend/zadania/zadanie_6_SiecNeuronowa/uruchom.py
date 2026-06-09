# -*- coding: utf-8 -*-
"""
Zadanie projektowe 6: Sieci neuronowe (CNN + MLP).
Uruchom:  python3 uruchom.py     (UWAGA: trenuje sieć, ~20-40 s)
Generuje: zbior/rover_training_data.csv (zbiór uczący >=1000/klasę) + zbior/info.txt
          decyzja/nn_raport.txt (decyzje sieci na scenariuszach testowych).
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, BACKEND)
os.chdir(BACKEND)  # potrzebne dla ue5_photos i zapisu artefaktow
ZBIOR = os.path.join(HERE, "zbior")
DECYZJA = os.path.join(HERE, "decyzja")
os.makedirs(ZBIOR, exist_ok=True)
os.makedirs(DECYZJA, exist_ok=True)

from zadania.zadanie_6_SiecNeuronowa.siec import train_cnn

dataset_path = os.path.join(ZBIOR, "rover_training_data.csv")
report_path = os.path.join(DECYZJA, "nn_raport.txt")

print("[Zadanie 6] Trenuje siec CNN+MLP (to potrwa chwile)...")
train_cnn(data_path=dataset_path, report_path=report_path)

# Policz licznosc klas (wymog: >= 1000 na klase)
import pandas as pd
df = pd.read_csv(dataset_path)
counts = df["target_decision"].value_counts().to_dict()
with open(os.path.join(ZBIOR, "info.txt"), "w", encoding="utf-8") as f:
    f.write("ZBIOR UCZACY (Zadanie 6 - siec neuronowa)\n")
    f.write(f"Lacznie przykladow: {len(df)}\n")
    for k, v in counts.items():
        f.write(f"  klasa {k}: {v} przykladow\n")
    f.write("\nWejscie sieci: obraz z kamery UE5 (CNN) + 7 cech telemetrii (MLP).\n")
    f.write("Foldery zdjec UE5: backend/ue5_photos/{sand,rock,crater,station,base}\n")

print("=" * 60)
print(" ZADANIE 6 - SIEC NEURONOWA (CNN + MLP)")
print("=" * 60)
print(f"Zbior uczacy: {len(df)} przykladow -> zbior/rover_training_data.csv")
for k, v in counts.items():
    print(f"  {k}: {v} (wymog >= 1000/klase)")
print("Decyzje sieci -> decyzja/nn_raport.txt")
