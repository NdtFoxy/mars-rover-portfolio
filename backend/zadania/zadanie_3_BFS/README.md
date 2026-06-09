# Zadanie projektowe 3 — Niepoinformowane strategie przeszukiwania (BFS)

**PDF:** `route-planning (1).pdf`

## Wymagania (z PDF)
1. Zastosowanie strategii przeszukiwania przestrzeni stanów do planowania ruchu agenta na kracie.
2. Wykorzystanie „Schematu procedury przeszukiwania grafu stanów”.
3. Implementacja strategii **Breadth-First Search**.
4. Agent dysponuje akcjami: ruch do przodu, obrót w lewo, obrót w prawo.

## Realizacja
- Algorytm: `bfs.py` → `bfs_find_path` (kolejka FIFO, stan = `(x, y, kierunek)`, akcje `MOVE_FORWARD / TURN_LEFT / TURN_RIGHT`, bez kosztu i heurystyki).
- `app/core/agent.py` importuje tę funkcję bezpośrednio i używa jej, gdy aktywne jest zadanie 3.
- Mapa generowana przez `Environment` (piasek / skała / krater).

## Pliki
- `zbior/mapa.txt` — dane wejściowe (mapa + start/cel)
- `decyzja/sciezka.txt` — wynik: najkrótsza ścieżka (akcje) + liczba rozwiniętych węzłów

## Uruchomienie
```sh
python3 uruchom.py
```

## Jak to działa krok po kroku (przepływ tam i z powrotem)
1. **Środowisko** (`Environment`) generuje kratę 20×15 z polami: piasek / skała / krater.
2. **Cel:** agent wybiera aktywny minerał na mapie jako punkt docelowy `(gx, gy)`.
3. **Wyszukiwanie:** `agent._find_path` wywołuje `bfs_find_path(x, y, direction, gx, gy, env)`.
   - Stan = `(x, y, kierunek)`; akcje = `MOVE_FORWARD`, `TURN_LEFT`, `TURN_RIGHT`.
   - **OPEN** = kolejka FIFO (`deque`), **CLOSED** = zbiór odwiedzonych stanów (anty-cykl).
   - BFS rozwija stany **wszerz**; pierwsze osiągnięcie celu = najkrótsza (najmniej akcji) ścieżka.
4. **Plan:** zwrócona lista akcji ląduje w `agent.current_plan`.
5. **Wykonanie:** każde `POST /step` zdejmuje jedną akcję z planu → łazik rusza/obraca się →
   stan trafia w JSON do **UE5**, które renderuje ruch.
6. **Powrót:** gdy plecak pełny lub bateria słaba → nowy cel = stacja/baza → **ponowny BFS** →
   łazik wraca, sprzedaje, (opcjonalnie) kupuje ulepszenia i cykl się powtarza.

## Pytania prowadzącego (Q&A do obrony)
- **Dlaczego BFS daje najkrótszą ścieżkę?** Bo przeszukuje wszerz po grafie **bez wag** —
  pierwszy raz, gdy osiągniemy cel, mamy minimalną liczbę akcji.
- **Co to jest „stan” i czemu zawiera kierunek?** Łazik ma orientację; obrót to osobna akcja,
  więc `(x, y, kierunek)` rozróżnia „stoję na (3,4) zwrócony N” od „… zwrócony E”.
- **Czym są listy OPEN i CLOSED?** OPEN = kolejka FIFO stanów do rozwinięcia; CLOSED = zbiór
  już odwiedzonych, żeby nie wpaść w cykl i nie liczyć tego samego dwa razy.
- **Złożoność?** Czasowa i pamięciowa `O(V+E)`, gdzie `V = liczba_komórek × 4 kierunki`.
- **Czy BFS jest zupełny i optymalny?** Zupełny (skończona krata) i optymalny w **liczbie
  kroków** — ale NIE w energii, bo ignoruje koszt wjazdu na skałę. To naprawia A* (zad. 4).
- **Czym różni się od DFS?** DFS idzie w głąb i nie gwarantuje najkrótszej ścieżki; BFS tak.
