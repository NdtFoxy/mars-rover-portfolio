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

## Jak to działa krok po kroku (przepływ tam i z powrotem)
1. **Instancja:** `items_from_minerals` zamienia minerały na mapie w przedmioty plecakowe
   (waga, objętość, wartość); limity = pojemność plecaka łazika (waga ORAZ objętość).
2. **Osobnik:** wektor **bitów** — `1` na pozycji `i` znaczy „zapakuj minerał `i`”.
3. **Pętla GA (`KnapsackGA`)** przez N pokoleń:
   - **selekcja ruletkowa** — szansa wyboru rodzica ∝ jego `fitness`,
   - **krzyżowanie jednopunktowe** — sklejenie genów dwóch rodziców,
   - **mutacja bitowa** — losowe odwrócenie bitów z małym prawdopodobieństwem,
   - **elityzm** — najlepsze osobniki przechodzą bez zmian dalej.
4. **Funkcja celu:** suma wartości spakowanych minerałów; przekroczenie **któregokolwiek** limitu
   (waga lub objętość) jest karane (fitness niższy, ale > 0, by ruletka działała).
5. **Walidacja:** dokładny solver **DP** (`solve_knapsack_dp`) liczy optimum — porównanie pokazuje,
   że GA praktycznie zawsze trafia w optimum (gap ~0.00%).
6. **Na żywo:** `agent._plan_mining_manifest(method="ga")` w każdej turze wybiera, **co kopać**;
   po powrocie do bazy łazik sprzedaje minerały i kupuje ulepszenia (pętla ekonomiczna).

## Pytania prowadzącego (Q&A do obrony)
- **Jak reprezentujecie osobnika?** Jako wektor bitów o długości = liczba minerałów; gen `1` =
  minerał w plecaku. To klasyczne kodowanie problemu plecakowego 0/1.
- **Co to jest selekcja ruletkowa?** Losowanie rodzica z prawdopodobieństwem proporcjonalnym do
  fitness — lepsze rozwiązania częściej się rozmnażają (wymóg 3 z PDF).
- **Jak działają krzyżowanie i mutacja?** Krzyżowanie jednopunktowe wymienia fragmenty genów dwóch
  rodziców; mutacja odwraca pojedyncze bity, dając różnorodność (wymóg 2 z PDF).
- **Czym jest funkcja celu (fitness) i jak karzecie niedopuszczalne rozwiązania?** Sumą wartości;
  przekroczenie limitu wagi LUB objętości obniża fitness (zostaje > 0, żeby ruletka nie dzieliła przez 0).
- **Po co solver DP, skoro macie GA?** DP daje **gwarantowane optimum** `O(n·W·V)` — służy jako
  wzorzec do udowodnienia, że operatory GA są poprawne (GA = DP na testach).
- **Dlaczego w grze używacie GA, a nie DP?** Bo zadanie wymaga algorytmu **genetycznego**; GA łatwo
  skaluje się i rozszerza (np. dodatkowe kryteria), a DP rośnie z iloczynem limitów.
- **Na czym polega „wielowymiarowość”?** Plecak ma **dwa** niezależne ograniczenia (waga i objętość),
  więc pojawiają się realne kompromisy: lód jest lekki, lecz objętościowy; tytan ciężki, lecz kompaktowy.
- **Elityzm — po co?** Chroni najlepsze znalezione rozwiązanie przed utratą w kolejnym pokoleniu.
