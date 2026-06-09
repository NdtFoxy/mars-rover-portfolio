# 📊 Contribution Report: Assignment 1

This document tracks the individual contributions of team members for the "Autonomous Mars Rover" project.

## 👤 Team Members
- **Mykyta** (Team Lead, Backend Architecture, API)
- **Aliaksandra** (Backend Logic, Domain Entities)
- **Artem** (Frontend, Unreal Engine 5 Visualization)

---

## 📝 Assignment 1: Agent Environment (Execution Environment)
**Status:** Completed ✅

### 🛠 Mykyta's Contributions

*   **Project Infrastructure & DevOps:**
    *   Set up the Git repository with a robust `.gitignore` to prevent repository bloat.
    *   Established a professional **Git Flow** workflow (branching strategy, conventional commits, Pull Request reviews).
    *   **Cloud Asset Pipeline (DVC):** Integrated **DVC (Data Version Control)** linked to Google Drive to manage large Unreal Engine assets, ensuring the Git repository stays lightweight and performant.
    *   **Security & Auth:** Configured secure **Google OAuth 2.0 / Service Account** authentication for DVC, ensuring team access while strictly protecting secrets from being exposed in version control.

*   **Backend Architecture (FastAPI):**
    *   Designed a scalable folder structure following clean architecture principles.
    *   Implemented the **FastAPI server** with RESTful endpoints (`/state`, `/step`) to bridge backend logic and frontend visualization.
    *   Created **Pydantic models** (`GameState`, `Position`) to standardize and validate data exchange between Python and Unreal Engine.
    *   **Stubs & Mocking:** Developed an initial backend skeleton, allowing the frontend team to start integration before the final domain logic was implemented.

*   **Project Management & Documentation:**
    *   Authored comprehensive developer guidelines (`CONTRIBUTING.md`) and project technical documentation.
    *   Maintained project status reports (`REPORTS.md`), ensuring full transparency of team progress for the academic audit.


### 👷 Aliaksandra's Contributions
*   **Domain Entity Modeling:**
    *   Implemented the `Environment` class to represent the 2D grid world (`width`, `height`).
    *   Developed boundary validation logic (`is_within_bounds`) to ensure the agent cannot move outside the defined grid.
*   **Agent Mechanics & Navigation:**
    *   Created the `Agent` class with position tracking (`x`, `y`).
    *   Implemented the core `move` method, enforcing step-by-step movement constraints (preventing teleportation) and validating new coordinates against the `Environment` rules.
    *   Developed the `move_randomly` algorithm for autonomous navigation (choosing Up, Down, Left, Right) while respecting the world's boundaries.
*   **Documentation:**
    *   Documented personal technical contributions and domain logic structures in `REPORTS.md`.

### 🎨 Artem's Contributions
* **UE5 Environment Setup:**
    * Created a 3D Mars-themed environment with a discrete grid visualization (BP_GridManager).
    * Imported and configured the Rover actor (BP_MarsRover) as a Pawn, ensuring correct camera control (3rd person).
* **Backend Integration:**
    * Implemented asynchronous HTTP POST requests using VaRest plugin to fetch agent movement data from the FastAPI server.
    * Developed JSON parsing logic to extract agent coordinates (`x`, `y`) from the API response.
* **Visualization Logic:**
    * Created a coordinate mapping system to translate backend grid indices into UE5 World Space.
    * Implemented smooth movement transitions (MoveComponentTo) for the rover to ensure professional visual experience.
    * Configured procedural obstacle spawning with visibility toggling for the grid tiles.

---


## 📝 Assignment 2: Knowledge Representation & Advanced Simulation Physics
**Status:** Completed ✅

### 🛠 Mykyta's Contributions
*   **REST API Expansion & State Lifecycle:**
    *   Developed the core simulation loop via FastAPI, creating endpoints for semantic data retrieval (`GET /state`), simulation progression (`POST /step`), and world regeneration (`POST /restart`).
    *   Implemented global state management to persist the Environment and Agent objects across stateless HTTP requests.
    *   **Data Aggregation:** Designed the JSON serialization logic in `/state` to package the Agent's telemetry, Environment status (time, weather), the 2D grid, and semantic objects into a unified, frontend-ready "Semantic Network" response.
*   **Security & Network Configuration:**
    *   Configured **CORS (Cross-Origin Resource Sharing)** Middleware to securely allow cross-origin requests. Added specific origins (e.g., `localhost:5173`) to enable seamless integration with web-based dashboards or external frontend clients.
    *   Maintained API documentation accessibility via Swagger UI (`/docs`).

### 👷 Aliaksandra's Contributions
*   **Semantic Object Modeling (Knowledge Representation):**
    *   Implemented an OOP hierarchy for environment entities using a base `GameObject` class (Semantic Node), extending it into interactive `Mineral` and `ChargingStation` frames.
    *   Developed a "Smart Spawning" algorithm (`_get_free_sand_position`) that ensures objects are procedurally generated strictly on navigable Sand terrain without overlapping.
*   **Advanced Agent Physics & Resource Management:**
    *   Implemented complex **Battery Physics**. The agent now consumes energy dynamically based on terrain types (e.g., Sand drains `-2.0`, Mountains drain `-6.0` triggering `HEAVY_DRAIN` status).
    *   Added a State Machine for the Rover (`IDLE`, `MOVING`, `CHARGING`, `DEAD` / Permadeath).
    *   Developed interaction logic: active mining (adding to inventory), docking at charging stations (consuming energy pools), and passive solar charging using sine-wave mathematical models tied to the time of day and weather multipliers.
*   **Dynamic World Systems:**
    *   Engineered a 24-hour Day/Night cycle and a dynamic Weather System with weighted probabilities (e.g., Clear Skies, Sandstorms, Foggy), directly affecting the rover's solar efficiency.

### 🎨 Artem's Contributions
*   **Dynamic Environment Visualization (UE5):**
    *   Implemented a fully functional **Day/Night Cycle** in Unreal Engine 5, dynamically reacting to the `time_of_day` data from the backend API.
    *   Created advanced visual effects for different weather conditions (e.g., Sandstorms, Fog) based on the current simulation state.
*   **3D Asset Integration & World Building:**
    *   Integrated and configured high-quality 3D models for semantic objects: visually distinct Resources (Titanium, Water Ice, Hematite) and Charging Stations.
    *   Upgraded the procedural generation logic to spawn these complex 3D meshes based on backend grid coordinates.
*   **User Interface (HUD):**
    *   Developed a comprehensive On-Screen Interface to display the rover's real-time telemetry (Battery level, Status, Inventory) and environmental data (Weather, Current Hour).




## 📝 Assignment 3: Uninformed State-Space Search (BFS)
**Status:** Completed ✅

### 🛠 Mykyta's Contributions
*   **API Adaptation for Pathfinding:**
    *   Expanded the FastAPI `Pydantic` models (`AgentState` in `models.py`) to support the new agent state, including directional orientation (`N`, `E`, `S`, `W`) and action queues (`current_plan`).
    *   Refactored the `/step` endpoint in `api.py` to trigger the agent's new cognitive function (`follow_plan_or_search`) instead of random movement, bridging the BFS backend logic with the frontend.
    *   Maintained robust JSON serialization, ensuring the UE5 client receives the calculated path step-by-step.
    * **DVC Storage Migration (Google Drive to S3):** 
  Orchestrated a complete migration of the project's heavy data storage from Google Drive to **Backblaze B2 (S3-compatible storage)**. This resolved critical team workflow bottlenecks, including Google Drive's `invalid_grant` OAuth errors and strict personal storage quota limitations.
    * **Git & DVC Tracking Conflict Resolution:** 
    Successfully resolved overlapping tracking issues between Git and DVC for the Unreal Engine assets (`frontend_ue`). Untracked heavy directories from Git cache (`git rm -r --cached`) and completely delegated their version control to DVC, ensuring a clean and lightweight GitHub repository.
    * **Secure S3 Integration:** 
    Configured DVC to work securely via the `dvc-s3` plugin. Implemented proper security practices by storing AWS S3 application keys locally (`--local` flag) to prevent credential leaks into the public Git repository.
    * **Onboarding Automation Script:** 
    Developed a Python utility script (`setup_s3.py`) to automate the DVC setup process for other team members. The script automatically verifies/installs required dependencies (`dvc[s3]`) and injects credentials, allowing teammates to pull gigabytes of data with a single command without manual configuration.

### 👷 Aliaksandra's Contributions
*   **State-Space Search Implementation (BFS):**
    *   Developed the `bfs_find_path` algorithm in `search.py` strictly following the "Graph Search Procedure Schema."
    *   Utilized a FIFO queue (`deque` as the **OPEN** list) for Breadth-First Search and a hash set (**CLOSED** list) to prevent cyclic state processing.
    *   Implemented the requested atomic actions as state transitions: `MOVE_FORWARD`, `TURN_LEFT`, and `TURN_RIGHT`.
*   **Agent Brain & Autonomy:**
    *   Upgraded the `Agent` class to autonomously use BFS for targeting active minerals on the map.
    *   Implemented a queue-based execution plan (`current_plan`). The rover now systematically searches for a target, generates a sequence of actions, and executes them step-by-step.
    *   Integrated directional physics, adapting energy consumption for rotating (0.5 energy) and moving forward (2.0 energy).

### 🎨 Artem's Contributions
*   **Path Execution Visualization in UE5:**
    *   Upgraded the Mars Rover actor in Unreal Engine 5 to support the new orientation-based movement (interpolating rotation when turning left/right).
    *   Mapped the discrete API action steps (`MOVE_FORWARD`, `TURN_LEFT`, `TURN_RIGHT`) into smooth 3D animations and timeline-based movement.
    *   Synchronized the UI to display the agent's current directional heading and execution plan queue.

### Sprint Update: Advanced Neural Network Upgrade (Multimodal CNN + MLP)

#### What was done:
1. **Transition to Real Visual Data:**
   - Eliminated the synthetic 3x3 pixel matrix generator.
   - Set up a structured local image database (`ue5_photos/`) containing real screenshots rendered directly in Unreal Engine 5 representing all environment states (`sand`, `rock`, `crater`, `station`, `base`).

2. **Multimodal CNN + MLP Architecture Implementation:**
   - Designed and implemented a multi-input neural network in PyTorch (`MissionControlCNN`).
   - Built a Convolutional Neural Network (CNN) branch using `Conv2d` and `MaxPool2d` layers to extract spatial visual features from 32x32 RGB camera frames.
   - Built a Multilayer Perceptron (MLP) branch to process 7 tabular telemetry features (battery level, time of day, weather multiplier, etc.).
   - Integrated a feature fusion layer to concatenate visual and physical features before final decision classification (`GO_TO_CHARGE` vs. `CONTINUE_MINING`).

3. **Data Augmentation Pipeline:**
   - Implemented real-time image augmentation using `torchvision.transforms` (including random rotations and flips).
   - Successfully expanded a small pool of manual screenshots into a balanced dataset of over 2,000 unique training samples, fulfilling the academic requirement of having $\ge 1000$ training examples per class.

4. **Integration and Real-Time Inference:**
   - Updated the autonomous agent logic to sample and classify visual frames on-the-fly depending on the tile the rover occupies.
   - Maintained full backward compatibility with the existing API communication protocol to ensure seamless integration with the Unreal Engine 5 frontend.
   - Verified training convergence (loss reduced from 0.22 to 0.13).

---

## 📝 Assignment 4: Genetic Algorithms (Problem Plecakowy)
**Status:** Completed ✅

> **Wymagania zadania:** zastosowanie algorytmu genetycznego do problemu pojawiającego się w projekcie; uwzględnienie operacji **krzyżowania** i **mutacji**; wybór rodziców zgodnie z **regułą ruletki**.

### 🛠 Mykyta's Contributions

*   **Wybór problemu — Problem Plecakowy (0/1 Knapsack):**
    *   Każdy minerał otrzymał **wagę (kg)** i **wartość ($)** (`MATERIAL_SPECS` w `environment.py`): Tytan (\$100 / 8 kg), Lód Wodny (\$50 / 3 kg), Hematyt (\$30 / 5 kg).
    *   Łazik ma ograniczoną **pojemność plecaka** (bazowo 20 kg). Spośród rozsianych minerałów musi wybrać podzbiór maksymalizujący wartość bez przekroczenia limitu wagi — to klasyczny problem plecakowy pojawiający się wprost w mechanice gry.

*   **Algorytm Genetyczny (`core/knapsack.py` → `KnapsackGA`):**
    *   **Reprezentacja:** osobnik = wektor bitów (gen `1` ⇒ minerał spakowany do plecaka).
    *   **Funkcja celu:** suma wartości spakowanych minerałów; przekroczenie pojemności jest karane (rozwiązania niedopuszczalne mają niższy fitness, zawsze > 0, aby ruletka działała).
    *   ✔ **Selekcja ruletkowa** (`roulette_wheel_selection`) — szansa wyboru rodzica proporcjonalna do fitness *(wymóg 3)*.
    *   ✔ **Krzyżowanie jednopunktowe** wektorów genów *(wymóg 2)*.
    *   ✔ **Mutacja** — odwracanie bitów z zadanym prawdopodobieństwem *(wymóg 2)*.
    *   **Elityzm** — najlepsze osobniki przechodzą bez zmian do kolejnego pokolenia. Struktura spójna z istniejącym `genetic_map.py`.

*   **Walidacja jakości GA (porównanie z Programowaniem Dynamicznym):**
    *   Zaimplementowano dokładny solver DP `O(n·W)` (`solve_knapsack_dp`) jako wzorzec optymalności oraz eksperyment porównawczy (`compare_knapsack`, `run_knapsack_experiment`).

    | Benchmark | GA = optimum | Średnia luka (gap) | Czas GA | Czas DP |
    |---|---|---|---|---|
    | Minerały projektu (n=12, W=20) | 30/30 (100%) | 0.00% | ~18 ms | ~0.02 ms |
    | Trudne losowe (n=18, W=30) | 29/30 (97%) | 0.06% | ~20 ms | ~0.04 ms |

    *   **Wniosek:** algorytm genetyczny praktycznie zawsze znajduje rozwiązanie optymalne (lub odległe od optimum o ułamek procenta), co potwierdza poprawność implementacji operatorów ewolucyjnych.

*   **Integracja z agentem oraz sklepem (pętla ekonomiczna):**
    *   Łazik planuje trasy wydobywcze rozwiązując problem plecakowy GA (`_plan_mining_manifest`); pole `last_knapsack` w `/state` pokazuje aktualny plan (liczba sztuk, wartość, waga).
    *   **Sklep z ulepszeniami** (`core/shop.py`): ulepszenia kupowane za **pieniądze + materiały** (np. plecak: `$120 + 2× Hematyt`). Nowe endpointy `/shop` i `/shop/buy/{id}`.
    *   Ulepszenie pojemności plecaka **bezpośrednio zwiększa rozmiar problemu plecakowego** (limit `W`), domykając pętlę: *wydobycie → sprzedaż → ulepszenie → większy plecak → trudniejszy problem plecakowy*.
    *   Materiały potrzebne na ulepszenie dostają premię w funkcji celu GA — łazik dynamicznie zmienia priorytety wydobycia (łączy plecak ze sklepem).
    *   Endpoint diagnostyczny **`/knapsack`** zwraca porównanie GA vs DP na bieżącej mapie.
    *   Dodano twardy bezpiecznik energetyczny (`_needs_emergency_charge` + histereza ładowania), dzięki któremu łazik przeżywa wystarczająco długo, by zademonstrować całą pętlę ekonomiczną.

*   **Rozszerzenie do WIELOWYMIAROWEGO problemu plecakowego (waga + objętość):**
    *   Każdy minerał ma teraz wagę (kg) ORAZ objętość (l), a plecak dwa niezależne limity. Powstają realne kompromisy: Lód jest lekki, lecz objętościowy; Tytan ciężki, lecz kompaktowy.
    *   DP rozszerzono na 2 wymiary `O(n·W·V)`; GA karze przekroczenie KTÓREGOKOLWIEK limitu. Walidacja GA vs DP nadal trzyma optimum (20/20, gap 0.00%).

*   **Rozbudowany sklep (6 ulepszeń, część z DEBUFFAMI / kompromisami):**
    *   Ładownia (+8 kg, +6 l), Panele (+0.6× słońce, **−3 l**), Silnik (−15% ruch, **−10 baterii**), Ogniwo (+30 baterii, **+5% ruch**), Kompresor (−15% objętości minerałów), Wiertło (+15% ceny sprzedaży, **+8% ruch**).
    *   Debuffy tworzą realne decyzje zakupowe (trade-off), a nie wyłącznie wzmocnienia. Nowe atrybuty agenta: `volume_capacity`, `volume_factor`, `sell_bonus`.

*   **Sieć decyzyjna w wersji zunifikowanej (`main`):**
    *   W `main` decyzje MINING/CHARGE podejmuje multimodalna sieć CNN + MLP (obraz UE5 + 7 cech telemetrii); siódmą cechą tabularną jest stopień zapełnienia plecaka (`inventory_fill_ratio` = max z wagi i objętości), spójny z ekonomią plecaka i sklepu.
    *   Dostępna jest też lekka wersja bez kamery (tylko 7 cech telemetrii) jako tag `wersja-algorytm-genetyczny` — do prezentacji samego algorytmu genetycznego.

*   **Zarządzanie wersjami projektu (Git) oraz prezentacja:**
    *   Wersje utrzymywane jako gałęzie/tagi: `wersja-algorytm-genetyczny` (plecak/sklep) oraz `wersja-siec-cnn` (wariant z kamerą CNN). Umożliwia to oddzielną prezentację każdego zadania prowadzącemu.
    *   Skrypt `demo_genetyczny.py` — prezentacja algorytmu genetycznego (zbiór danych, operatory ewolucyjne, decyzja GA vs DP) krok po kroku.

---

# 🛰️ Wkład indywidualny członków zespołu (zadania 1–7)

**Zespół:** Mykyta Kyslytsia `s498817` (Team Lead — architektura backendu/API, ML, infrastruktura) · Aliaksandra `s498793` (logika domenowa i algorytmy) · Artem `s500690` (Unreal Engine 5 oraz sieć neuronowa CNN + MLP)

## Zadanie 1 — Środowisko działania agenta

**🛠 Mykyta:** Założył strukturę repozytorium, `.gitignore`, `CONTRIBUTING.md` i workflow Git Flow (branże, conventional commits, Pull Requesty). Postawił szkielet serwera **FastAPI** oraz modele **Pydantic** (`GameState`, `Position`) jako kontrakt wymiany danych Python ↔ UE5; przygotował stuby API, by zespół frontendu mógł integrować się przed ukończeniem logiki domenowej.

**🧠 Aliaksandra:** Zaprojektowała i zaimplementowała **rdzeń logiki domenowej** projektu w paradygmacie obiektowym (OOP):
- klasę `Environment` reprezentującą dyskretny świat 2D (krata `width × height`) wraz z metodą `is_within_bounds` walidującą granice planszy oraz przechowywaniem stanu siatki;
- klasę `Agent` ze śledzeniem pozycji (`x`, `y`) i metodą `move`, która **wymusza ruch krok po kroku** (zakaz teleportacji) i sprawdza poprawność współrzędnych względem reguł środowiska;
- algorytm autonomicznej nawigacji `move_randomly` (Up/Down/Left/Right) respektujący granice świata — pierwszy mechanizm samodzielnego poruszania się agenta, na którym później oparto BFS/A\*;
- czytelny podział odpowiedzialności klas (agent vs środowisko), który stał się fundamentem pod wszystkie kolejne zadania (3–7). Udokumentowała własne struktury domenowe w `REPORTS.md`.

**🎮 Artem:** Zbudował środowisko 3D w UE5 z dyskretną wizualizacją kraty (`BP_GridManager`), skonfigurował łazika jako Pawn (`BP_MarsRover`) z kamerą TPP. Zaimplementował asynchroniczne zapytania HTTP (VaRest), parsowanie JSON (współrzędne `x`, `y`), mapowanie indeksów kraty na World Space, płynny ruch (`MoveComponentTo`) i proceduralny spawn przeszkód.

## Zadanie 2 — Reprezentacja wiedzy

**🛠 Mykyta:** Rozbudował REST API o pełny cykl symulacji (`GET /state`, `POST /step`, `POST /restart`) i globalne zarządzanie stanem między bezstanowymi żądaniami HTTP. Zaprojektował serializację JSON pakującą telemetrię agenta, stan środowiska, kratę 2D i obiekty semantyczne w jednolitą „sieć semantyczną”; skonfigurował **CORS** i dokumentację Swagger (`/docs`).

**🧠 Aliaksandra:** Zbudowała **całą warstwę reprezentacji wiedzy i fizyki symulacji** — najobszerniejszy moduł logiki backendu:
- **Sieć semantyczna obiektów:** hierarchia OOP z klasą bazową `GameObject` (węzeł semantyczny) rozszerzoną do interaktywnych ram `Mineral`, `ChargingStation` i `ScienceBase`; każdy obiekt zna swój typ, pozycję i stan aktywności oraz potrafi serializować się do JSON (`to_dict`).
- **Inteligentne rozmieszczanie:** algorytm `_get_free_sand_position`, który spawnuje obiekty **wyłącznie na przejezdnym piasku**, bez nakładania się i bez blokowania tras.
- **Fizyka energii:** dynamiczne zużycie baterii zależne od terenu (piasek `−2.0`, góry `−6.0` → status `HEAVY_DRAIN`) oraz **pasywne ładowanie słoneczne** opisane modelem **sinusoidalnym** (sprawność = sinus pory dnia), modulowane mnożnikiem pogody.
- **Maszyna stanów łazika:** `IDLE / MOVING / CHARGING / DEAD` (z mechaniką **permadeath** przy zerowej baterii) oraz logika interakcji: aktywne wydobycie do ekwipunku i dokowanie do stacji ze wspólną pulą energii.
- **Dynamiczne systemy świata:** 24-godzinny cykl dnia/nocy (`time_of_day`) oraz **system pogody jako łańcuch Markowa** z wagami prawdopodobieństwa (czyste niebo, zachmurzenie, mgła, burze piaskowe), płynnie przechodzący między stanami i wpływający na sprawność paneli.

**🎮 Artem:** Zaimplementował w UE5 cykl dnia/nocy reagujący na `time_of_day` z API oraz efekty pogodowe (burze, mgła). Zintegrował modele 3D obiektów semantycznych (Tytan, Lód Wodny, Hematyt, stacje ładowania) i proceduralny spawn meshy wg współrzędnych z backendu. Stworzył pierwszą wersję HUD (bateria, status, ekwipunek, pogoda, godzina).

## Zadanie 3 — Niepoinformowane przeszukiwanie (BFS)

**🛠 Mykyta:** Dostosował API do planowania trasy — rozszerzył modele `Pydantic` (`AgentState`) o orientację kierunkową (`N/E/S/W`) i kolejkę akcji (`current_plan`); przepisał endpoint `/step` na funkcję kognitywną `follow_plan_or_search` zamiast ruchu losowego. Równolegle przeprowadził **migrację DVC z Google Drive na Backblaze S3** i napisał skrypt onboardingowy `setup_s3.py`.

**🧠 Aliaksandra:** Zaimplementowała algorytm **BFS** ściśle według „schematu procedury przeszukiwania grafu stanów”:
- funkcja `bfs_find_path` ze stanem `(x, y, kierunek)`, **kolejką FIFO** jako listą **OPEN** (`deque`) i zbiorem **CLOSED** chroniącym przed cyklami; pierwsze osiągnięcie celu = najkrótsza (najmniej akcji) ścieżka;
- pełny zestaw akcji atomowych jako przejść między stanami: `MOVE_FORWARD`, `TURN_LEFT`, `TURN_RIGHT`, z obsługą przeszkód (krater = ściana) i granic mapy;
- funkcja `reconstruct_path` odtwarzająca sekwencję akcji od celu do startu;
- rozbudowa **„mózgu” agenta**: autonomiczne wybieranie aktywnego minerału jako celu, generowanie i kolejkowe wykonywanie planu (`current_plan`) krok po kroku oraz **fizyka kierunkowa** (obrót `0.5`, ruch `2.0` energii). Dzięki temu BFS przeszedł z teorii w działający, autonomiczny ruch łazika spięty z UE5.

**🎮 Artem:** Rozbudował łazika w UE5 o ruch zależny od orientacji (interpolacja obrotu przy skręcaniu), zmapował dyskretne akcje API na płynne animacje 3D (timeline) i zsynchronizował UI z bieżącym kursem oraz kolejką planu.

## Zadanie 4 — Poinformowane przeszukiwanie (A*)

**🧠 Aliaksandra:** Zaimplementowała poinformowane przeszukiwanie **A\***, rozszerzając schemat z zadania 3 o koszt:
- funkcja `astar_find_path` z **kopcem priorytetowym** (`heapq`) i funkcją priorytetu `f(n) = g(n) + h(n)`, gdzie `g` to realny dotychczasowy koszt, a `h` to **heurystyka Manhattan** (dopuszczalna → A\* pozostaje optymalny);
- model **zróżnicowanego kosztu terenu** (`TERRAIN_COSTS`: piasek `2.0`, skała `6.0`, obrót `0.5`), dzięki któremu łazik **omija drogie skały** i planuje trasy tańsze energetycznie;
- mechanizm pomijania „przeterminowanych” wpisów w kopcu (gdy znaleziono tańszą drogę do stanu) oraz **zliczanie rozwiniętych węzłów**, co pozwoliło ilościowo wykazać, że A\* rozwija ich mniej niż BFS;
- integracja: ten sam moduł obsługuje trasy w zadaniach 4–7, więc A\* stał się domyślnym planerem ruchu w żywej symulacji.

**🛠 Mykyta:** Zintegrował A\* z agentem (używany we wszystkich trybach poza zadaniem 3), dodał porównanie efektywności A\* vs BFS (liczba rozwiniętych węzłów, koszt energetyczny) i obsłużył wynik w API/serializacji.

**🎮 Artem:** Zwizualizował w UE5 najtańszą ścieżkę wyznaczoną przez A\* i prezentację kosztu energetycznego trasy w HUD (spójnie z systemem ruchu z zadania 3).

## Zadanie 5 — Drzewa decyzyjne (ID3)

**🧠 Aliaksandra:** Zaimplementowała pełny pipeline **uczenia drzewa decyzyjnego (ID3)**:
- generator zbioru uczącego `generate_dataset` tworzący **300 przykładów** telemetrii (powyżej wymaganych 200), opisanych **8 atrybutami** (bateria, pora dnia, nasłonecznienie, pogoda, teren, dystans do minerału, dystans do stacji, zapełnienie plecaka) i automatycznie etykietowanych decyzją `GO_TO_CHARGE` / `CONTINUE_MINING`;
- trening `train_tree` na `DecisionTreeClassifier(criterion="entropy")` — kryterium entropii realizuje **wybór atrybutu wg przyrostu informacji** (istota ID3), z ograniczoną głębokością przeciw przeuczeniu;
- funkcja `predict_with_tree` zwracająca decyzję i pewności klas, używana przez agenta na żywo;
- **wizualizacja wyuczonego drzewa** do `drzewo.png` (grafika) oraz eksport reguł IF-THEN do `reguly.txt` — czytelny dowód działania modelu na obronie.

**🛠 Mykyta:** Zintegrował drzewo decyzyjne z działającym agentem jako bazowy „mózg” (decyzja `GO_TO_CHARGE` / `CONTINUE_MINING`), rozbudował telemetrię i skalibrował progi/poziomy drzewa (m.in. dostrojenie z 45% → 25%); zapewnił uczenie drzewa przy każdym starcie serwera.

**🎮 Artem:** Wyprowadził decyzję sieci/drzewa na HUD (pole „AI Status” / `nn_thought`) oraz interaktywny skaner kamery wizualizujący typ terenu pod łazikiem.

## Zadanie 6 — Sieci neuronowe (CNN + MLP)

**🎮 Artem:** Przeprowadził kluczowy upgrade — z perceptronu na **multimodalną sieć `MissionControlCNN`**: gałąź **CNN** (`Conv2d` + `MaxPool2d`) dla obrazu z kamery UE5 + gałąź **MLP** dla 7 cech telemetrii, z **fuzją cech**. Zbudował bazę realnych zrzutów `ue5_photos/` i zastosował **augmentację** (`torchvision.transforms`) spełniającą wymóg **≥1000/klasę** (>2000 próbek z 75 kadrów); wdrożył **inference na żywo** (próbkowanie kadru pod łazikiem) oraz moduł AI-nawigatora z hot-reload.

**🛠 Mykyta:** Zaimplementował pierwszą wersję klasyfikatora neuronowego i skrypt treningowy (generacja i **balansowanie zbioru** `rover_training_data.csv`), dostroił inference serią poprawek i zoptymalizował generację map (cache). Zintegrował leniwe trenowanie sieci tylko przy aktywnym zadaniu 6.

**🧠 Aliaksandra:** Dostarczyła **generator zróżnicowanych map** (oparty na ewolucji z oceną przejezdności przez pathfinding), który zapewnia **różnorodne scenariusze terenu** używane przy budowie i balansowaniu zbioru uczącego sieci. Dzięki temu dane treningowe pokrywają realne układy piasku/skał/kraterów (a nie jeden statyczny przypadek), co poprawia uogólnianie modelu. Jej warstwa środowiska (telemetria, pogoda, dystanse) dostarcza też 7 cech tabularnych wejścia sieci.

## Zadanie 7 — Algorytmy genetyczne (problem plecakowy)

**🛠 Mykyta:** Zaprojektował i zaimplementował **`KnapsackGA`**: selekcja ruletkowa, krzyżowanie jednopunktowe, mutacja bitowa, elityzm; rozszerzył problem do **wielowymiarowego** (waga + objętość). Dodał walidację przez dokładny solver **DP** (GA = optimum, gap 0.00%), **sklep z 6 ulepszeniami (z debuffami)** i domknął pętlę ekonomiczną *wydobycie → sprzedaż → ulepszenie → większy plecak*. Przygotował `demo_genetyczny.py` (operatory krok po kroku).

**🧠 Aliaksandra:** Zaimplementowała **drugie zastosowanie algorytmu genetycznego** w projekcie — **GA generujący mapę** (`genetic_map.py`), historycznie **pierwsze użycie operatorów ewolucyjnych** w całym kodzie, które utorowało drogę pod GA plecakowy:
- osobnik = cała siatka kafli; **funkcja przystosowania** premiuje mapy przejezdne i „ciekawe” (kara za brak ścieżki start–cel liczonej pathfindingiem, kara za złe proporcje piasku/skał/kraterów, bonus za **klasteryzację skał** w pasma gór zamiast losowego szumu);
- pełny komplet operatorów: **selekcja ruletkowa**, **krzyżowanie** (wymiana wierszy mapy), **mutacja** kafli i **elityzm**;
- **cache** wyniku, by nie uruchamiać kosztownej ewolucji przy każdym restarcie środowiska.
To jej moduł generuje teren, po którym faktycznie jeździ łazik we wszystkich zadaniach.

**🎮 Artem:** Wyprowadził na HUD bieżący plan plecakowy (`last_knapsack`: liczba sztuk, wartość, waga) i interfejs sklepu z ulepszeniami; usunął zakleszczenie (deadlock) w logice wyznaczania trasy łazika.

Dodatkowo przeprowadził **migrację klienta UE5 na architekturę hybrydową C++ + Blueprints**: warstwa Blueprintów pełni odtąd wyłącznie rolę dekoratora widoku (spawn i wizualizacja), a całość obliczeń, matematyki i parsowania danych sieciowych przeniósł do wydajnej warstwy **C++** (z pomocniczym mostem GPU). Zaimplementował bibliotekę `UAresTimeLibrary` (`UBlueprintFunctionLibrary`):
- **`ProcessTelemetryWithCuda`** — pełne parsowanie surowego JSON z backendu po stronie CPU/C++ do czystych struktur `USTRUCT` (`FAresAgentState`, `FAresEnvironmentState`, `FAresObjectState`): agent, środowisko, obiekty dynamiczne, sklep, aktywne zadanie (`mission`) i krata.
- **Składanie danych dla HUD w C++** — łączenie tablic `inventory` i `current_plan` w gotowe stringi, automatyczne budowanie opisu sklepu (`UPGRADE SHOP`) oraz opisu aktywnego zadania (`ACTIVE TASK`), z bezpieczną obsługą pól `null` (np. `energy_pool`).
- **Most GPU/CUDA** — przeniesienie ciężkiego wyliczania transformacji ~300 kafli kraty na GPU (`RunCudaGridCalculation`) z czystym fallbackiem C++; pomocnicze funkcje `ProcessTimeOfDay`/`ConvertTimeInternal` (czas nieba UDS), `CalculateTileTransform` i `GetTileVisuals` (skala/offset kafla wg typu terenu).
