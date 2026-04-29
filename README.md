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

## 3) Install as a desktop app

- **Chrome / Edge (Windows, macOS, Linux):** open the app URL, then use **Install app** from the address bar (or menu).
- **Safari (macOS):** open the app URL, then choose **File → Add to Dock**.

## 4) Install on iPhone

- Open the app URL in **Safari**.
- Tap **Share** → **Add to Home Screen**.
- Launch it from your Home Screen like a native app.

## 5) Install on Android

- Open the app URL in **Chrome**.
- Tap **Install app** (or **Add to Home screen** from the menu).
- Launch it from your app drawer/home screen.

## 6) Make it available anywhere

Deploy this app on a cloud VM or platform (Render/Fly.io/Railway). Once deployed over HTTPS, you can install it on desktop, iPhone, and Android.
