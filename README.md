# Personal Assistant (Desktop + iPhone + Android)

This repository creates a responsive assistant you can use in a browser and install like an app on desktop and mobile.

## 1) Setup (easy mode)

If you do not want manual setup steps, run the installer script once and it will handle everything:

```bash
python quick_install.py
```

What it does automatically:
- creates `.venv`
- installs all dependencies
- creates `.env` from `.env.example` (if missing)
- optionally launches the app

> You only need to add `OPENAI_API_KEY` in `.env` if you want OpenAI-backed responses.

### Manual setup (advanced)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# then edit .env and set OPENAI_API_KEY
# optional local free alternative (Ollama): set OPENAI_BASE_URL=http://localhost:11434/v1 and OPENAI_API_KEY=ollama
```


### Use a fully local/free model (Ollama)

If you want to run without paid API usage, you can use a local OpenAI-compatible endpoint:

```bash
ollama pull llama3.1:8b
```

Set in `.env`:

```env
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_API_KEY=ollama
OPENAI_MODEL=llama3.1:8b
```

The backend will route all existing AI endpoints through that local endpoint.

## 2) Run locally

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Open:
- `http://localhost:8000` on your computer.
- `http://<your-computer-local-ip>:8000` on your iPhone/Android (same Wi-Fi).

## 3) API capabilities from `PERSONAL_ASSISTANT_PLAN.md`

The backend now includes foundational modules to match the plan:

- `GET /api/assistant/health` – reports enabled assistant modules.
- `POST /api/items` + `GET /api/items` – normalized task queue plus prioritization buckets (`today_must_do`, `this_week_scheduled`, `backlog`).
- `POST /api/threads` + `GET /api/followups` – follow-up intelligence with draft nudges.
- `POST /api/jobs` + `GET /api/jobs` – lightweight job application tracker.
- `GET /api/brief` – generated morning brief with top outcomes, focus blocks, and due follow-ups.
- `POST /api/learning/feedback` + `GET /api/learning/profile` – adaptive learning loop that tracks high-signal topics from user feedback and tunes assistant behavior.
- `GET/POST /api/profile` – persistent-in-memory user profile for career targeting and retail business context.
- `POST /api/resume/upload` + `GET /api/resume` – upload/store resume text for personalized job assets.
- `POST /api/resume/optimize` – AI resume optimization for a specific job description.
- `POST /api/cover-letter` – generate tailored cover letters by role/company.
- `POST /api/jobs/match` – quick fit scoring + targeting suggestions from resume/profile vs a job description.
- `POST /api/retail/tasks` + `GET /api/retail/tasks` – manage online retail operations tasks (inventory, marketing, support, finance, ops).

These are intentionally in-memory MVP endpoints so you can quickly validate workflow before adding persistent storage and external OAuth integrations.

## 4) Install as a desktop app

- **Chrome / Edge (Windows, macOS, Linux):** open the app URL, then use **Install app** from the address bar (or menu).
- **Safari (macOS):** open the app URL, then choose **File → Add to Dock**.

## 5) Install on iPhone

- Open the app URL in **Safari**.
- Tap **Share** → **Add to Home Screen**.
- Launch it from your Home Screen like a native app.

## 6) Install on Android

- Open the app URL in **Chrome**.
- Tap **Install app** (or **Add to Home screen** from the menu).
- Launch it from your app drawer/home screen.

## 7) Make it available anywhere

Deploy this app on a cloud VM or platform (Render/Fly.io/Railway). Once deployed over HTTPS, you can install it on desktop, iPhone, and Android.


## 8) Run in autonomous mode (no chat required)

Use the Autopilot panel to start background planning loops.

- `POST /api/autopilot/start?interval_seconds=300` – starts autonomous brief generation.
- `POST /api/autopilot/stop` – stops it.
- `GET /api/autopilot/status` – shows latest run and last generated brief snapshot.

The web UI now defaults to this autonomous control panel.


## 9) Build a **real desktop application** (no browser required)

If you do **not** want users to run a localhost command manually, package this project as a native desktop binary.
The included `desktop_app.py` boots the FastAPI backend in-process and opens a native app window with `pywebview`, so users launch it like any normal desktop app.

### Quick build (Windows/macOS/Linux)

```bash
python build_desktop.py
```

This creates a standalone binary in `dist/`:
- Windows: `dist/PersonalAssistant.exe`
- macOS/Linux: `dist/PersonalAssistant`

Users can run that binary directly without opening a terminal or browser.

## 10) One-click Windows download (.exe installer)

If you want users to just click and install, publish a signed Windows installer `.exe` as a GitHub Release asset.

### Build steps (Windows)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python build_desktop.py
```

Build the installer with Inno Setup:

```bash
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

Output:
- `dist/PersonalAssistantInstaller.exe`

### Publish for one-click install

1. Push your changes and create a GitHub Release (for example, `v1.0.0`).
2. Upload `dist/PersonalAssistantInstaller.exe` as a Release asset.
3. Share the direct download URL from that Release.

End-user flow is then:
- Click download link
- Open `PersonalAssistantInstaller.exe`
- Click through the installer wizard
- Launch **Personal Assistant** from Start Menu/Desktop shortcut

> Recommended: code-sign `PersonalAssistantInstaller.exe` so Windows SmartScreen warnings are reduced for users.
