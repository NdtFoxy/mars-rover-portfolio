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
