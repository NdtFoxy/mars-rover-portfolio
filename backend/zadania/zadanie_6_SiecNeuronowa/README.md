# Zadanie projektowe 6 — Sieci neuronowe (CNN + MLP)

**PDF:** `neural-networks (1).pdf`

## Wymagania (z PDF)
1. Zastosowanie uczenia sieci neuronowych do wybranego problemu.
2. Zbiór uczący zawierający **co najmniej 1000 przykładów dla każdej klasy**.
3. Agent **wykorzystuje wyuczoną sieć** w procesie podejmowania decyzji.

## Realizacja
- Sieć: `siec.py` → `MissionControlCNN` i `train_cnn` (multimodalna: gałąź **CNN** dla obrazu z kamery UE5 + gałąź **MLP** dla 7 cech telemetrii, fuzja cech → decyzja).
- Zbiór uczący: `generate_balanced_dataset(1000)` (≥1000 na klasę: `GO_TO_CHARGE`, `CONTINUE_MINING`) + zdjęcia UE5 z `backend/ue5_photos/`.
- Decyzja: agent (`agent.decide_next_macro_action`) używa wyuczonej sieci na żywo.
- API wywołuje `train_cnn()` leniwie tylko wtedy, gdy aktywne jest zadanie 6.

## Pliki
- `zbior/rover_training_data.csv` — zbiór uczący
- `zbior/info.txt` — liczność klas (potwierdza ≥1000/klasę)
- `decyzja/nn_raport.txt` — metryki + decyzje sieci na scenariuszach testowych

## Uruchomienie
```sh
python3 uruchom.py     # trenuje sieć i zapisuje artefakty (~20-40 s)
```
> Wersja „na żywo” (agent + UE5): wybierz to zadanie w `navigate.py` i uruchom `run.py`.
