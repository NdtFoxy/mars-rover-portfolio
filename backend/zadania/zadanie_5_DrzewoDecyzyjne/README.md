# Zadanie projektowe 5 — Drzewa decyzyjne (ID3)

**PDF:** `decision-trees.pdf`

## Wymagania (z PDF)
1. Zastosowanie schematu uczenia drzew decyzyjnych do wybranego problemu.
2. Algorytm **ID3** — wybór atrybutu o **największym przyroście informacji** (lub uogólnienie).
3. Zbiór uczący złożony z **co najmniej 200 przykładów**.
4. Decyzja opisana **co najmniej 8 atrybutami**.
5. Opcja **podglądu wyuczonego drzewa** (logi lub plik z grafiką).

## Realizacja
- Implementacja: `drzewo.py` → `generate_dataset`, `train_tree`, `predict_with_tree`.
- Zbiór uczący: telemetria łazika → decyzja `GO_TO_CHARGE` / `CONTINUE_MINING`.
- Drzewo: `DecisionTreeClassifier(criterion="entropy")` → wybór atrybutu wg przyrostu informacji (ID3).
- 8 atrybutów: bateria, pora dnia, słońce, pogoda, teren, dystans do minerału, dystans do stacji, zapełnienie plecaka.
- Serwer zawsze uczy to drzewo przy starcie i używa go jako bazowego mózgu, gdy zadanie 6 nie jest aktywne.

## Pliki
- `zbior/rover_training_data.csv` — zbiór uczący (300 przykładów, 8 atrybutów)
- `decyzja/drzewo.png` — graficzny podgląd wyuczonego drzewa
- `decyzja/reguly.txt` — drzewo jako reguły tekstowe

## Uruchomienie
```sh
python3 uruchom.py
```
