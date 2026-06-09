# Zadanie projektowe 7 — Algorytmy genetyczne (problem plecakowy)

**PDF:** `genetic-algorithms.pdf`

## Wymagania (z PDF)
1. Zastosowanie algorytmu genetycznego do wybranego problemu w projekcie.
2. Uwzględnienie operacji **krzyżowania** i **mutacji**.
3. Wybór rodziców zgodnie z **regułą ruletki**.

## Realizacja
- Problem: **wielowymiarowy problem plecakowy** (waga + objętość) — łazik wybiera minerały do plecaka.
- GA: `genetyczny.py` → `KnapsackGA` (selekcja ruletkowa + krzyżowanie jednopunktowe + mutacja bitowa + elityzm).
- Walidacja: dokładny solver **DP** (`solve_knapsack_dp`) jako wzorzec optymalności (GA = DP).
- `app/core/agent.py` importuje ten moduł i używa GA do wyboru minerałów w działającej symulacji.

## Pliki
- `zbior/instancja.txt` — dane wejściowe (minerały: waga / objętość / wartość + limity)
- `decyzja/ga_vs_dp.txt` — wybór GA + porównanie z optimum (DP)

## Uruchomienie
```sh
python3 uruchom.py
# pełna prezentacja operatorów krok po kroku:
python3 ../../demo_genetyczny.py
```
