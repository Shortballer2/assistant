# Personal Assistant (Desktop + iPhone + Android)

This repository creates a responsive assistant you can use in a browser and install like an app on desktop and mobile.

## 1) Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# then edit .env and set OPENAI_API_KEY
```

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
