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

## Jak to działa krok po kroku (przepływ tam i z powrotem)
1. **Zbiór uczący:** `generate_dataset` tworzy 300 przykładów telemetrii łazika, każdy z
   etykietą `GO_TO_CHARGE` / `CONTINUE_MINING` (reguły fizyki: mało baterii + daleko do bazy → ładuj).
2. **Uczenie:** `train_tree` buduje `DecisionTreeClassifier(criterion="entropy")` — kryterium
   entropii = **przyrost informacji** (ID3). Drzewo wybiera w każdym węźle atrybut, który
   najmocniej „rozdziela” klasy.
3. **Serwer:** uczy drzewo **raz przy starcie** i trzyma je w pamięci jako bazowy „mózg”.
4. **Na żywo:** w każdym `POST /step` `agent.decide_with_tree` buduje wektor **8 cech** z aktualnego
   stanu → `predict_with_tree` zwraca decyzję → łazik kopie dalej albo wraca na ładowanie.
5. **Podgląd:** `decyzja/drzewo.png` (grafika) + `decyzja/reguly.txt` (drzewo jako reguły IF-THEN).

## Pytania prowadzącego (Q&A do obrony)
- **Co to jest przyrost informacji (information gain)?** Spadek **entropii** zbioru po podziale
  według danego atrybutu. ID3 wybiera atrybut o **największym** przyroście.
- **Wzór entropii?** `H(S) = −Σ pᵢ·log₂(pᵢ)`, gdzie `pᵢ` to udział klasy `i` w zbiorze.
- **Jakie 8 atrybutów?** bateria, pora dnia, nasłonecznienie, pogoda, teren, dystans do minerału,
  dystans do stacji, zapełnienie plecaka.
- **Dlaczego `criterion="entropy"` to ID3?** Bo wybór podziału maksymalizuje przyrost informacji
  (jak w ID3); różnica wobec klasycznego ID3 to obsługa cech ciągłych (progi liczbowe).
- **Jak unikacie przeuczenia (overfitting)?** Zbiór 300 przykładów + płytkie, czytelne drzewo;
  można ograniczyć `max_depth`.
- **Drzewo vs sieć neuronowa (zad. 6)?** Drzewo jest **interpretowalne** (reguły IF-THEN) i tanie;
  sieć radzi sobie z danymi nieliniowymi/obrazem, ale jest „czarną skrzynką”.
