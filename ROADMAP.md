# 🗺️ Project Roadmap: Assignment 2 (Knowledge Representation)

## 🧠 What is "Knowledge Representation" in our project?
The assignment requires implementing *Frames (Ramy)*, *Semantic Networks (Sieci semantyczne)*, or *Conceptual Graphs*. While this sounds like abstract mathematics, in modern software engineering, it translates directly to **Object-Oriented Programming (OOP) and structured JSON payloads!**

*   **Frames (Ramy):** These are our Python Classes. A frame is a data structure with specific "slots" (properties). 
    *   *Example:* The `Mineral` frame. Its slots are: `Name: Titanium`, `Weight: 5kg`, `Coordinates: X=2, Y=3`.
*   **Semantic Networks (Sieci semantyczne):** These are the relationships between our objects (nodes). 
    *   *Example relationship:* The object `Rover` **[is located at]** `Grid Cell (2,3)`, which **[contains]** `Titanium`. 
    *   *In code:* The rover queries the environment about its current coordinates, and the semantic network resolves this by returning the specific mineral object.

---

## 🏗️ Domain Knowledge Architecture

### 1. Global Environment (Globalny stan środowiska)
*   **Time of Day:** `Day` or `Night`. Changes every *N* steps.
*   **Weather:** `Clear` or `Dust Storm`. 
*   **Impact:** During a Dust Storm, movement costs more energy, and solar panels cannot recharge the rover.

### 2. Mars Materials & Objects (Stan obiektów w interakcji)
*   **Titanium (Tytan):** High-value building material.
*   **Water Ice (Lód Wodny):** Critical resource for survival.
*   **Hematite (Hematyt):** Common iron ore.
*   **Charging Station (Stacja Ładująca):** Fixed points on the map where the rover can recharge its battery to 100%.

### 3. Agent State (Stan agenta)
*   **Battery:** 0-100%. Drains dynamically by moving.
*   **Solar Panels:** Passively regenerates battery IF it is `Day` AND weather is `Clear`.
*   **Inventory:** A list/array of collected materials.
*   **Status:** `Alive`, `Dead` (Battery = 0).

---

## 📋 Task Delegation (Sprint 2)

### 👩‍💻 Aleksandra (Backend Logic / OOP Architecture)
**Goal:** Implement the business logic (Frames and Networks) in Python.
1.  **Create Objects:** Create `Mineral` and `ChargingStation` classes. Populate the `Environment` grid with Titanium, Water Ice, and Hematite at random coordinates.
2.  **Environment Logic:** Add a step counter to `Environment`. Every 20 steps, toggle `is_night`. Every 50 steps, toggle `is_dust_storm`.
3.  **Rover Logic Update:** 
    *   Add `battery = 100` to the `Agent`. `move()` now costs `-2` battery.
    *   At the end of each step, if `env.is_night == False` and `env.weather == 'Clear'`, solar panels add `+1` to battery.
    *   If rover coordinates match a `ChargingStation`, battery becomes `100`.
    *   If rover coordinates match a `Mineral`, remove it from the map and append to `agent.inventory`.

### 🧑‍💻 Mykyta (Team Lead / API / UI Design)
**Goal:** Design the interface and structure the API payload for both frontends.
1.  **UI/UX Design (Figma):** Design a sci-fi HUD (Head-Up Display) for Artem. It must include:
    *   Battery progress bar (Green -> Yellow -> Red).
    *   Environment widget (Sun/Moon icon, Storm warning text).
    *   Inventory list (e.g., "Titanium: 2, Water Ice: 1").
2.  **API Payload (Pydantic):** Update `models.py` so `/state` returns a rich semantic JSON representing the entire knowledge graph.
    ```json
    {
      "environment": {"is_night": false, "weather": "storm"},
      "agent": {"x": 5, "y": 5, "battery": 85, "inventory": ["Titanium", "Ice"]},
      "objects": [
        {"type": "ChargingStation", "x": 2, "y": 2},
        {"type": "Hematite", "x": 8, "y": 9}
      ]
    }
    ```
3.  **React Dashboard:** Update `frontend_backup` to visualize this JSON in real-time as a web control panel.

### 🎮 Artem (Unreal Engine 5 Frontend)
**Goal:** Visualize the Knowledge Representation and build the in-game HUD based on Figma designs.
1.  **Asset Sourcing (Quixel & Marketplace):** 
    *   Download sci-fi crates or small beacons to represent `Minerals` and `Charging Stations`. Use Quixel Megascans for Mars rocks/sand.
2.  **Dynamic Environment (Visuals):**
    *   Parse `is_night` from JSON. If true, dynamically reduce the intensity of the Directional Light and turn on the Rover's Spotlights.
    *   Parse `weather`. If "storm", activate a Niagara particle system (dust/sand) around the camera.
3.  **HUD Implementation (UMG):**
    *   Create a UI Widget based on Mykyta's Figma design. Bind the progress bar to the `battery` value and update the inventory text based on the JSON array.
4.  **Death State:** If `battery == 0`, stop rover movement, trigger a "shutdown" animation (lights turn off), and show a "SYSTEM FAILURE" screen.

---

## 🎯 Summary of Academic Requirements Fulfillment

*   **Aleksandra** fulfills the core **Knowledge Representation** requirement by structuring the Python backend using *Frames* (OOP Classes) and *Semantic Networks* (spatial and logical interactions between the Agent, Objects, and the Environment).
*   **Mykyta** fulfills the **Data Serialization** requirement by mapping these complex semantic relationships into a standardized, machine-readable JSON format, and designs the UX to display this knowledge.
*   **Artem** fulfills the **Visual Representation** requirement by translating the data frames and state changes into a real-time, dynamic 3D simulation in Unreal Engine 5.