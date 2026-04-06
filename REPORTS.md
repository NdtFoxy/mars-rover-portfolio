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