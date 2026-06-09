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

## Obrona — rozszerzony zestaw

### Co to jest GA i DP (w jednym zdaniu)
- **GA (algorytm genetyczny)** — metoda **przybliżona**, naśladująca ewolucję: trzyma populację
  losowych rozwiązań i ulepsza je przez pokolenia (selekcja → krzyżowanie → mutacja). Szybko
  daje bardzo dobre wyniki, ale **bez gwarancji** trafienia w idealne optimum.
- **DP (programowanie dynamiczne)** — metoda **dokładna**: buduje tablicę najlepszych wartości
  dla kolejnych limitów wagi i objętości i **gwarantuje optimum** `O(n·W·V)`. Wolniejsza przy
  dużych limitach, dlatego w grze używamy GA, a DP traktujemy jako wzorzec.

### Pełna pętla GA (do narysowania na kartce)
```
populacja losowa
   │
   ▼
[ ocena fitness ] ─► [ sortowanie ] ─► [ elityzm: 2 najlepsze ]
   ▲                                          │
   │                                          ▼
   │                          [ ruletka ] ─► [ krzyżowanie ] ─► [ mutacja ]
   │                                          │
   └──────────────  nowe pokolenie  ◄─────────┘
        (powtórz N razy → najlepszy osobnik = wybór minerałów)
```

### Pytania podchwytliwe (z odpowiedziami)
- **Czy GA zawsze znajdzie najlepsze rozwiązanie?** Nie — to heurystyka. W praktyce trafia w
  optimum lub jest o ułamek procenta gorszy; udowadnia to porównanie z DP (u nas 8/8, gap 0.00%).
- **Co, jeśli zwiększysz mutację do 0.5?** Algorytm zacznie błądzić losowo — mutacja zniszczy dobre
  geny, zbieżność się załamie. Dlatego trzymamy małe `0.05`.
- **Co, jeśli usuniesz elityzm?** Najlepsze rozwiązanie może zniknąć w kolejnym pokoleniu —
  zbieżność jest wolniejsza i mniej stabilna.
- **Co, jeśli funkcja celu może być 0 lub ujemna?** Selekcja ruletkowa dzieli przez sumę fitness —
  dlatego trzymamy fitness > 0 (minimum 0.1) i karzemy przekroczenia zamiast zerować.
- **Jak naprawiasz rozwiązanie niedopuszczalne?** Kara w fitness + zachłanna naprawa: usuwam
  minerały o najgorszym stosunku wartość/(waga+objętość), aż zmieszczę się w OBU limitach.
- **Jaka jest złożoność GA vs DP?** GA ≈ `O(pokolenia × populacja × n)` (niezależna od limitów),
  DP `O(n × W × V)` (rośnie z limitami). To kluczowa różnica skalowania.
- **Pokaż operatory w kodzie.** `genetyczny.py`: `roulette_wheel_selection`, `crossover`, `mutate`,
  pętla `run` (tam elityzm i tworzenie nowego pokolenia).

### Skrypt obrony (otwarcie, do zapamiętania)
> „Zastosowałem algorytm genetyczny do **wielowymiarowego problemu plecakowego**: łazik ma plecak
> z limitem wagi i objętości i musi wybrać minerały maksymalizujące wartość. Osobnik to wektor
> bitów, użyłem **selekcji ruletkowej, krzyżowania jednopunktowego, mutacji bitowej i elityzmu**.
> Poprawność sprawdziłem **dokładnym DP** jako wzorcem optymalności — GA trafia w optimum.
> Algorytm działa też na żywo: napędza wybór minerałów i pętlę ekonomiczną (sprzedaż → sklep → większy plecak).”

### Demonstracja krok po kroku
`python3 ../../demo_genetyczny.py` — pokazuje operatory ewolucyjne na żywo (populacja, fitness,
selekcja, krzyżowanie, mutacja) oraz decyzję GA vs DP, idealne gdy prowadzący poprosi „pokaż działanie”.
