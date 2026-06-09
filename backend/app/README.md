# app/ — kod aplikacji backendu

Pakiet `app/` zawiera serwer FastAPI oraz całą logikę domenową łazika.
Poniżej opis każdego pliku i przepływu danych.

```
app/
├── api.py          # serwer FastAPI: endpointy + dashboard w terminalu
├── models.py       # modele Pydantic = kontrakt danych backend <-> UE5
└── core/
    ├── agent.py        # ŁAZIK: ruch, fizyka energii, decyzje, ekonomia, plecak GA
    ├── environment.py  # ŚWIAT: krata, obiekty semantyczne, czas, pogoda, mapa
    ├── genetic_map.py  # GA generujący mapę (teren)
    ├── shop.py         # sklep z ulepszeniami (z debuffami)
    └── mission.py      # aktywne zadanie (wspólne źródło prawdy dla API i agenta)
```

---

## api.py — warstwa serwera (FastAPI)

Endpointy REST używane przez UE5 i do testów:

| Endpoint | Metoda | Opis |
|---|---|---|
| `/state` | GET | pełny stan świata w JSON (agent, środowisko, krata, obiekty, sklep, misja) |
| `/step` | POST | jeden krok symulacji (myśl → działanie → świat → JSON) |
| `/step_multiple/{n}` | POST | n kroków naraz |
| `/restart` | POST | reset świata i agenta |
| `/shop` | GET | stan sklepu (ulepszenia, koszty) |
| `/shop/buy/{id}` | POST | ręczny zakup ulepszenia |
| `/knapsack` | GET | porównanie GA vs DP na bieżącej mapie (diagnostyka) |
| `/mission` | GET | aktywne zadanie |
| `/mission/reload` | POST | przeładowanie zadania bez restartu (Alt+R / przycisk UE5) |

Przy starcie `api.py`:
1. uczy **drzewo decyzyjne** (zawsze, bazowy mózg),
2. wczytuje **CNN** tylko jeśli aktywne jest zadanie 6 (leniwie),
3. tworzy globalny `Environment` i `Agent`.

---

## models.py — kontrakt danych (Pydantic)

Definiuje struktury JSON wysyłane do UE5: `AgentState`, `EnvironmentState`,
`GameObjectState`, `ShopItemState`, `GameState`. Każde pole jest walidowane i
serializowane — UE5 czyta dokładnie te struktury (m.in. waga/objętość plecaka,
budżet, kierunek, „myśl” AI, typ kamery).

---

## core/agent.py — mózg i fizyka łazika

Najważniejszy plik logiki. Kluczowe metody:

- `move_forward`, `turn_left/right` — ruch i **zużycie energii** zależne od terenu i silnika.
- `follow_plan_or_search` — główna pętla decyzyjna: ładować czy kopać, wyznacz trasę, wykonaj plan.
- `_find_path` — wybiera **BFS** (zad. 3) lub **A\*** (reszta) wg aktywnego zadania.
- `decide_next_macro_action` — decyzja przez **sieć CNN+MLP** (zad. 6).
- `decide_with_tree` — decyzja przez **drzewo ID3** (pozostałe zadania).
- `_plan_mining_manifest` — **problem plecakowy (GA)**: co kopać przy dwóch limitach.
- `interact_and_recharge` — kopanie, ładowanie ze stacji, ekonomia na bazie, ładowanie słoneczne.
- `_do_base_economy` — sprzedaż minerałów + automatyczny zakup ulepszeń (respektuje `SHOP_ENABLED`).
- `_calculate_solar_efficiency` — model sinusoidalny paneli (0 w nocy, max w południe).
- `_check_death` — permadeath przy zerowej baterii.

---

## core/environment.py — świat symulacji

- Hierarchia obiektów semantycznych: `GameObject` → `Mineral`, `ChargingStation`, `ScienceBase`.
- `update_time_and_weather` — „tik” świata: czas (`step_counter * 0.25 h`), pogoda, regeneracja.
- `_get_smooth_weather_transition` — pogoda jako **łańcuch Markowa** (płynne zmiany z wagami).
- `_generate_terrain` — teren generowany **algorytmem genetycznym** (`genetic_map.py`), z cache.
- `_get_free_sand_position` — spawn obiektów tylko na przejezdnym piasku.

---

## core/genetic_map.py — GA generujący mapę

Drugie zastosowanie algorytmu genetycznego: osobnik = cała siatka kafli; fitness premiuje
mapy przejezdne i „ciekawe” (kara za brak ścieżki liczonej pathfindingiem, kara za złe
proporcje terenu, bonus za skupiska skał). Operatory: ruletka, krzyżowanie, mutacja, elityzm.

---

## core/shop.py — sklep z ulepszeniami

Katalog 6 ulepszeń kupowanych za **pieniądze + materiały**. Część ma **debuffy** (kompromisy,
np. silnik: −15% kosztu ruchu, ale −10 baterii). Flaga `SHOP_ENABLED` pozwala włączyć/wyłączyć
sklep (do porównań przeżywalności). Modyfikuje atrybuty agenta: `capacity`, `volume_capacity`,
`max_battery`, `solar_bonus`, `motor_efficiency`, `volume_factor`, `sell_bonus`.

---

## core/mission.py — aktywne zadanie

Wspólne źródło prawdy: czyta `mission_config.json` (zapisywany przez `navigate.py`). API i agent
pytają stąd, JAKIE zadanie jest aktywne. Przeładowanie jest jawne (`reload_active_task`,
Alt+R / `POST /mission/reload`) — serwer nie restartuje się przy zmianie zadania.

---

## Przepływ danych (skrót)

```
navigate.py  ->  mission_config.json  ->  mission.get_active_task()
                                              │
UE5  --POST /step-->  api.py  ->  agent.follow_plan_or_search(...)
                                  ├─ _find_path: BFS / A*
                                  ├─ decyzja: drzewo / CNN
                                  └─ plecak: GA
                              ->  agent.interact_and_recharge(env)
                              ->  env.update_time_and_weather()
                              ->  get_current_state()  --JSON-->  UE5
```
