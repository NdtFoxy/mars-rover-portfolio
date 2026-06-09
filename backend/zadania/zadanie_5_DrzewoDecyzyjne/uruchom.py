# -*- coding: utf-8 -*-
"""
Zadanie projektowe 5: Drzewa decyzyjne (ID3 / przyrost informacji).
Uruchom:  python3 uruchom.py
Generuje: zbior/rover_training_data.csv (zbiór uczący >=200, 8 atrybutów)
          decyzja/drzewo.png + decyzja/reguly.txt (wyuczone drzewo).
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, BACKEND)
os.chdir(BACKEND)
ZBIOR = os.path.join(HERE, "zbior")
DECYZJA = os.path.join(HERE, "decyzja")
os.makedirs(ZBIOR, exist_ok=True)
os.makedirs(DECYZJA, exist_ok=True)

import matplotlib
matplotlib.use("Agg")  # bez okna -- zapis do pliku
import matplotlib.pyplot as plt
import random
from sklearn.tree import DecisionTreeClassifier, export_text, plot_tree

from zadania.zadanie_5_DrzewoDecyzyjne.drzewo import FEATURES, generate_dataset

random.seed(42)

print("[Zadanie 5] Generuje zbior uczacy (>= 200 przykladow)...")
df = generate_dataset(300)                       # >= 200
df.to_csv(os.path.join(ZBIOR, "rover_training_data.csv"), index=False)

X = df[FEATURES]
y = df["target_decision"]

# criterion="entropy" => wybor atrybutu wg PRZYROSTU INFORMACJI (zgodnie z ID3)
clf = DecisionTreeClassifier(criterion="entropy", max_depth=4, random_state=42)
clf.fit(X, y)

rules = export_text(clf, feature_names=FEATURES)
with open(os.path.join(DECYZJA, "reguly.txt"), "w", encoding="utf-8") as f:
    f.write("DECYZJA: wyuczone drzewo decyzyjne (ID3 / przyrost informacji)\n")
    f.write(f"Zbior uczacy: {len(df)} przykladow, {len(FEATURES)} atrybutow\n")
    f.write(f"Klasy decyzji: {list(clf.classes_)}\n\n")
    f.write(rules)

plt.figure(figsize=(16, 9))
plot_tree(clf, feature_names=FEATURES, class_names=list(clf.classes_),
          filled=True, rounded=True, fontsize=9)
plt.title("Drzewo decyzyjne (ID3 / entropia)")
plt.tight_layout()
plt.savefig(os.path.join(DECYZJA, "drzewo.png"), dpi=200)
plt.close()

print("=" * 60)
print(" ZADANIE 5 - DRZEWO DECYZYJNE (ID3)")
print("=" * 60)
print(f"Zbior uczacy: {len(df)} przykladow x {len(FEATURES)} atrybutow -> zbior/rover_training_data.csv")
print(f"Decyzja: drzewo -> decyzja/drzewo.png + decyzja/reguly.txt")
print("\nFragment regul:")
print("\n".join(rules.splitlines()[:18]))
