# 📊 Contribution Report: Assignment 1

This document tracks the individual contributions of team members for the "Autonomous Mars Rover" project.

## 👤 Team Members
- **Mykyta** (Team Lead, Backend Architecture, API)
- **Aleksandra** (Backend Logic, Domain Entities)
- **Artem** (Frontend, Unreal Engine 5 Visualization)

---

## 📝 Assignment 1: Agent Environment (Execution Environment)
**Status:** Completed ✅

### 🛠 Mykyta's Contributions
*   **Project Infrastructure:**
    *   Set up the Git repository, configured `.gitignore` to exclude OS/IDE/Unreal Engine temporary files.
    *   Established a professional **Git Flow** workflow (branching strategy, conventional commits).
*   **Backend Architecture (FastAPI):**
    *   Designed the project folder structure following clean architecture principles.
    *   Implemented the **FastAPI server** with API endpoints (`/state`, `/step`) to bridge backend logic and frontend visualization.
    *   Created **Pydantic models** (`GameState`, `Position`) to standardize data exchange between services.
    *   **Stubs & Mocking:** Implemented temporary stubs for `Agent` and `Environment` classes to ensure early API testing and integration readiness for frontend development.
*   **Documentation:**
    *   Authored `CONTRIBUTING.md` and `REPORTS.md` to streamline team collaboration.

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
*(Artem, please add your tasks here)*

---

## 🚀 How to contribute (Team Workflow)
To maintain code quality, we follow these rules:
1. **Never push to `main` directly.**
2. **Create a feature branch:** `git checkout -b feat/your-feature-name`
3. **Commit your changes:** `git commit -m "feat: description of your change"`
4. **Push to Gitea:** `git push origin feat/your-feature-name`
5. **Open a Pull Request (PR)** in the Gitea interface and request a review.