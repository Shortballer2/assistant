# Personal Assistant (iPhone + Computer)

This repository creates a responsive web-based assistant you can open on both iPhone and computer.

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
- `http://<your-computer-local-ip>:8000` on your iPhone (same Wi-Fi).

## 3) Make it available anywhere

Deploy this app on a cloud VM or platform (Render/Fly.io/Railway). Once deployed, open the HTTPS URL from any device.
