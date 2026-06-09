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

## Jak to działa krok po kroku (przepływ tam i z powrotem)
1. **Zbiór:** `generate_balanced_dataset(1000)` tworzy ≥1000 przykładów na klasę
   (`GO_TO_CHARGE`, `CONTINUE_MINING`) — telemetria + przypisany typ terenu.
2. **Obrazy:** dla każdego przykładu losujemy realny zrzut z `backend/ue5_photos/`
   (sand/rock/crater/station/base) i przepuszczamy przez **augmentację**
   (`RandomRotation(15)`, `RandomHorizontalFlip`) — z 75 zdjęć powstaje 2000+ unikalnych próbek.
3. **Sieć `MissionControlCNN` (multimodalna, 2 wejścia):**
   - gałąź **CNN**: `Conv2d(3→16)` → `MaxPool` → `Conv2d(16→32)` → `MaxPool` na obrazie 3×32×32,
   - gałąź **MLP**: `Linear(7→16)` na 7 cechach telemetrii,
   - **fuzja**: `cat(obraz=2048, telemetria=16)` → `Linear(2064→32)` → `Linear(32→2 klasy)`.
4. **Uczenie:** `CrossEntropyLoss` + optymalizator `Adam(lr=0.001)`, 30 epok (loss spada ~0.22 → 0.13).
5. **Na żywo:** `agent.decide_next_macro_action` bierze kadr terenu pod łazikiem + 7 cech telemetrii
   → sieć zwraca prawdopodobieństwa MINING/CHARGE (widoczne na HUD jako „AI Status”).
6. **Uwaga projektowa:** sieć jest uczona **leniwie** tylko gdy aktywne jest zadanie 6;
   w pozostałych zadaniach decyzję podejmuje drzewo (zad. 5).

## Pytania prowadzącego (Q&A do obrony)
- **Po co sieć, skoro drzewo (zad. 5) już decyduje?** Wymóg zadania: użyć **sieci neuronowej**
  i obrazu. Pokazujemy architekturę **multimodalną** — łączymy wizję (CNN) z telemetrią (MLP).
- **Jak spełniacie wymóg ≥1000 przykładów na klasę?** Przez **augmentację danych** — losowe
  obroty i odbicia 75 bazowych zrzutów dają >2000 unikalnych obrazów treningowych.
- **Czym `Conv2d` różni się od `Linear`?** Konwolucja wykrywa **cechy przestrzenne** obrazu
  (krawędzie, tekstury, cienie) niezależnie od położenia; `Linear` traktuje wejście jako płaski wektor.
- **Funkcja straty i optymalizator?** `CrossEntropyLoss` (klasyfikacja 2-klasowa) + `Adam` (lr=0.001).
- **Czym jest fuzja cech?** Konkatenacja wektora wizualnego (2048) z wektorem telemetrii (16)
  w jeden tensor (2064), który dopiero klasyfikator zamienia na decyzję.
- **Dlaczego wyniki sieci są podobne do drzewa?** Bo decyzja MINING/CHARGE zależy głównie od
  baterii i dystansu — sieć potwierdza tę zależność, a obraz jest dodatkowym kontekstem.
- **Po co `MaxPool`?** Zmniejsza wymiar mapy cech (mniej parametrów, odporność na drobne przesunięcia).
