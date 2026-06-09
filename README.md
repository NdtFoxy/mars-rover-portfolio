<div align="center" style="margin: 0; padding: 0;">
  <a href="#" style="display: block; margin: 0;">
    <img src="assets/banner-2.jpg" alt="Logo" width="2560" height="auto" style="display: block; margin: 0;">
  </a>

<h3 align="center" style="margin: 0;">Autonomous Mars Rover</h3>
  <p>
    <kbd>UNREAL ENGINE 5</kbd> ✛ <kbd>PYTHON ML BACKEND</kbd> ✛ <kbd>REACT FRONTEND</kbd>
  </p>
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


<div align="center">
  <h1>AUTONOMOUS ROVER STRUCTURE</h1>
</div>

<hr>

<details open>
  <summary><kbd>🛰️ ROOT</kbd> <b><code>/AI-COURSE-PROJECT</code></b> ── <i>Ares Core Architecture</i></summary>
  
  <blockquote>
    <details open>
      <summary>🟧 <kbd>📁 backend</kbd> ── <i>Python API & AI Brain 🧠</i></summary>
      <blockquote>
        <details open>
          <summary>🔸 <kbd>📁 app</kbd> ── <i>FastAPI Server Application</i></summary>
          <blockquote>
            <details open>
              <summary>⚙️ <kbd>📁 core</kbd> ── <i>Simulation Engine</i></summary>
              <blockquote>
                🤖 <code>agent.py</code> ── Rover decision-making & movement logic<br>
                🗺️ <code>environment.py</code> ── 2D discrete grid world boundaries
              </blockquote>
            </details>
            🌐 <code>main.py</code> ── Server setup & React CORS configuration<br>
            📡 <code>api.py</code> ── REST endpoints (<code>/state</code>, <code>/step</code>)<br>
            📐 <code>models.py</code> ── Pydantic data schemas (GameState, Position)
          </blockquote>
        </details>
        <details open>
          <summary>🧠 <kbd>📁 zadania</kbd> ── <i>Real Course Algorithm Modules</i></summary>
          <blockquote>
            🔎 <code>zadanie_3_BFS/bfs.py</code> ── Breadth-First Search used by the rover<br>
            🧭 <code>zadanie_4_Astar/astar.py</code> ── A* with terrain costs and Manhattan heuristic<br>
            🌳 <code>zadanie_5_DrzewoDecyzyjne/drzewo.py</code> ── Decision-tree training and live inference<br>
            🧠 <code>zadanie_6_SiecNeuronowa/siec.py</code> ── CNN + MLP training, loaded only for task 6<br>
            🧬 <code>zadanie_7_AlgorytmGenetyczny/genetyczny.py</code> ── Genetic knapsack optimizer
          </blockquote>
        </details>
        🔸 <code>📄 requirements.txt</code> ── Backend dependency matrix<br>
        🔥 <b><kbd>🚀 run.py</kbd></b> ── <i>MAIN SERVER IGNITION (Entry Point)</i>
      </blockquote>
    </details>
    <details open>
      <summary>🟧 <kbd>📁 frontend_ue</kbd> ── <i>3D Mars Surface Simulation (UE5) 🎮</i></summary>
      <blockquote>
        🔸 <code>📁 Config/</code> ── Physics & Environment parameters<br>
        🔸 <code>📁 Content/</code> ── Rover meshes, textures, blueprints<br>
        🔸 <code>📁 DerivedDataCache/</code> & <code>Intermediate/</code> ── Engine cache & compiled data<br>
        🔸 <code>📁 Saved/</code> ── Autosaves & Crash logs<br>
        🔸 <code>📄 Content.dvc</code> ── Large topology assets version control<br>
        🔷 <b><kbd>frontend_ue.uproject</kbd></b> ── <i>Unreal Engine Launcher</i>
      </blockquote>
    </details>
    <details>
      <summary>🖼️ <kbd>📁 assets</kbd> ── <i>Media 📸</i></summary>
      <blockquote>
        🔸 <code>🖼️ banner-2.jpg</code> ── Mission patch / Banner
      </blockquote>
    </details>
    <details open>
      <summary>📜 <kbd>DIRECTIVES</kbd></summary>
      <blockquote>
        📑 <code>CONTRIBUTING.md</code> ── Crew collaboration guidelines<br>
        📊 <code>REPORTS.md</code> ── Tracks team members work<br>
        📖 <code>README.md</code> ── Main documentation
      </blockquote>
    </details>
  </blockquote>
</details>
<hr>



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
> **Cloud Storage Access Required:** The project uses a Backblaze B2 (S3-compatible) remote. To access the heavy assets, you need the application key.

### Accessing Assets:
1. **Request Credentials:** If you are a team member, email the Lead Developer (Mykyta) at **[mykkys@st.amu.edu.pl](mailto:mykkys@st.amu.edu.pl)** to request the Backblaze application key.
2. **Setup:** Run the helper script and paste the key when prompted (it configures the `s3remote` locally):
   ```sh
   python setup_s3.py
   ```
3. **Pull Assets:** Once configured, download all assets with:
   ```sh
   dvc pull
   ```

---

## 🎮 Unreal Engine 5 Setup

The UE5 frontend provides the high-fidelity 3D visualization.

1. Open the project folder `frontend_ue` in **Unreal Engine 5**.
2. Ensure you have run `dvc pull` (see above) so all 3D assets are downloaded.
3. Configure the HTTP requests in the Blueprints to point to `http://localhost:8000/state`.
4. Choose game scene
5. Press **Play** in the UE5 Editor to start the visualization.
