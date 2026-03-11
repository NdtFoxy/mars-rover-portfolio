<div align="center" style="margin: 0; padding: 0;">
  <a href="#" style="display: block; margin: 0;">
    <img src="assets/banner-2.jpg" alt="Logo" width="2560" height="auto" style="display: block; margin: 0;">
  </a>

<h3 align="center" style="margin: 0;">Autonomous Mars Rover</h3>
<h4 align="center" style="margin: 0;">UNREAL ENGINE 5 + PYTHON ML BACKEND + REACT FRONTEND</h4>
</div>

Project Description: An autonomous agent exploring the surface of Mars based on a discrete, two-dimensional representation of the environment. The project combines visualization in Unreal Engine 5 with advanced decision-making logic on a Python server and a web-based control panel built with React.

### Built With

-   ![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
-   ![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
-   ![Unreal Engine](https://img.shields.io/badge/Unreal_Engine-313131?style=for-the-badge&logo=unrealengine&logoColor=white)
-   ![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
-   ![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white)
-   ![Git](https://img.shields.io/badge/Git-F05032?style=for-the-badge&logo=git&logoColor=white)

Technology Stack:
Backend: Python, FastAPI, Uvicorn, Pydantic (Logic and API).
Frontend: Unreal Engine 5 (3D Visualization), React 18 + TypeScript, Lucide React (Web UI / Control Panel).
Communication Protocol: HTTP/REST (JSON).
Version Control: Git (Gitea).

<h2>🧭 Карта Проекта (Интерактивная)</h2>

<details open>
  <summary><b>🌍 AI-COURSE-PROJECT</b> <i>(Root)</i></summary>
  
  <blockquote>
    <details>
      <summary>📁 <b>backend</b> ── <i>Сердце проекта на Python 🐍</i></summary>
      <blockquote>
        📁 <code>app/</code> - логика и API<br>
        📁 <code>venv/</code> - окружение<br>
        📄 <code>requirements.txt</code> - зависимости<br>
        🚀 <code>run.py</code> - точка входа AI
      </blockquote>
    </details>
    <details>
      <summary>📁 <b>frontend_ue</b> ── <i>Визуализация на Unreal Engine 🎮</i></summary>
      <blockquote>
        📁 <code>Config/</code> - настройки UE<br>
        📁 <code>Content/</code> - ассеты, блюпринты, модели<br>
        📁 <code>Saved/</code> & <code>Intermediate/</code> - кэш и логи<br>
        📄 <code>Content.dvc</code> - трекинг тяжелых файлов<br>
        🔷 <code>frontend_ue.uproject</code> - файл запуска движка
      </blockquote>
    </details>
    <details>
      <summary>📁 <b>assets & .dvc</b> ── <i>Данные и ресурсы 📊</i></summary>
      <blockquote>
        📁 <code>assets/</code> - картинки, медиа<br>
        📁 <code>.dvc/</code> - конфиги версионирования данных
      </blockquote>
    </details>
    📄 <code>CONTRIBUTING.md</code> - гайдлайны для команды<br>
    📄 <code>REPORTS.md</code> - отчетность и метрики<br>
    📄 <code>README.md</code> - главная документация
  </blockquote>
</details>

# 🚀 Getting Started: Building and Running

This guide will help you set up the Mars Rover project environment. Please ensure you have **Git**, **Python**, **Node.js (for React UI)**, and **Unreal Engine 5** installed.

## 1. Clone the Repository

```sh
git clone https://git.wmi.amu.edu.pl/s498817/ai-course-project.git
cd ai-course-project
```

---

## 2. Backend Setup (FastAPI)

The core simulation logic runs on a FastAPI server.

1. Navigate to the backend directory:
   ```sh
   cd backend
   ```

2. Create and activate a virtual environment:
   ```sh
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   
   # Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

4. Launch the development server:
   ```sh
   python run.py
   ```

> [!IMPORTANT]
> The Backend API is available at **[http://localhost:8000/docs](http://localhost:8000/docs)**. Use this interface to test API endpoints and verify the simulation logic.

---

## 🗄️ Working with Assets (DVC)

We use **DVC (Data Version Control)** to manage heavy 3D assets (textures, models) without bloating the Git repository.

> [!CAUTION]
> **Cloud Storage Access Required:** The project uses an encrypted Google Drive remote. To access the heavy assets, you need the service account credentials.

### Accessing Assets:
1. **Request Credentials:** If you are a team member, email the Lead Developer (Nikita) at **[nikita.kyslytsia@example.com](mailto:nikita.kyslytsia@example.com)** to request the necessary JSON keys.
2. **Setup:** Place the key file in the root folder, then configure DVC locally:
   ```sh
   dvc remote modify --local myremote gdrive_client_id <CLIENT_ID>
   dvc remote modify --local myremote gdrive_client_secret <CLIENT_SECRET>
   ```
3. **Pull Assets:** Once configured, download all assets with:
   ```sh
   dvc pull
   ```

---

## 🌐 Frontend Control Panel (React)

For real-time agent monitoring, we use a React-based dashboard. Ensure you have **[Node.js](https://nodejs.org/en)** installed.

1. Navigate to the React directory:
   ```sh
   cd frontend_backup
   ```

2. Install dependencies:
   ```sh
   npm install
   ```

3. Run the development server:
   ```sh
   npm run dev
   ```

> [!TIP]
> The Web UI will be available at **[http://localhost:5173](http://localhost:5173)**, providing a dashboard to monitor the agent's real-time state.

---

## 🎮 Unreal Engine 5 Setup

The UE5 frontend provides the high-fidelity 3D visualization.

1. Open the project folder `frontend_ue` in **Unreal Engine 5**.
2. Ensure you have run `dvc pull` (see above) so all 3D assets are downloaded.
3. Configure the HTTP requests in the Blueprints to point to `http://localhost:8000/state`.
4. Choose game scene
5. Press **Play** in the UE5 Editor to start the visualization.
