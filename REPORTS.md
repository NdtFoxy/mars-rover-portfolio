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

### 👷 Aleksandra's Contributions
*(Aleksandra, please add your tasks here)*

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