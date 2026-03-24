# LifeGuard Emergency Network

Automated crisis response app — Patient vitals, SOS dispatch, blood donor registry, AI health assistant.

## Repo structure

```
lifeguard-apk/
├── www/
│   └── index.html        ← Frontend (loaded by the APK)
├── server/
│   ├── main.py           ← FastAPI backend
│   ├── requirements.txt
│   └── .env.example      ← Copy to .env, fill in secrets
├── capacitor.config.json ← Capacitor / APK settings
├── package.json
├── render.yaml           ← One-click Render deploy config
└── .gitignore
```

---

## Step 1 — Rotate your secrets first

Your old keys were exposed. Do this before anything else:

1. Go to https://aistudio.google.com → API Keys → delete old key → create new one
2. Go to Google Account → Security → App Passwords → delete old password → create new one
3. Copy `server/.env.example` to `server/.env` and fill in the new values

---

## Step 2 — Deploy the backend to Render

1. Push this repo to GitHub (`.env` is gitignored — safe to push)
2. Go to https://render.com → New → Web Service
3. Connect your GitHub repo
4. Render auto-detects `render.yaml` — click **Apply**
5. In the Render dashboard, go to **Environment** and add:
   - `GEMINI_API_KEY` = your new Gemini key
   - `SENDER_EMAIL` = your Gmail address
   - `SENDER_PASSWORD` = your new App Password
6. Click **Deploy** — wait ~2 minutes
7. Copy your live URL, e.g. `https://lifeguard-backend.onrender.com`

---

## Step 3 — Update the frontend URL

Open `www/index.html` and find this line near the bottom:

```js
const BACKEND_URL = "https://YOUR-APP-NAME.onrender.com";
```

Replace it with your actual Render URL, then commit and push.

---

## Step 4 — Build the APK

### Prerequisites (one-time install)
- [Node.js LTS](https://nodejs.org)
- [Android Studio](https://developer.android.com/studio) — install with default SDK settings

### Commands

```bash
# In the repo root:
npm install

npx cap add android

npx cap sync

npx cap open android
```

### Inside Android Studio

1. Wait for Gradle sync to finish (progress bar at bottom)
2. Menu → **Build** → **Build Bundle(s) / APK(s)** → **Build APK(s)**
3. When done, click **locate** in the notification
4. Your APK is at: `android/app/build/outputs/apk/debug/app-debug.apk`

---

## Step 5 — Install on your phone

1. Transfer `app-debug.apk` to your Android phone (USB, Google Drive, etc.)
2. On the phone: Settings → Security → **Install unknown apps** → allow your file manager
3. Tap the APK file to install

---

## Local development (optional)

```bash
cd server
pip install -r requirements.txt
cp .env.example .env   # fill in your secrets
python main.py
# Server runs at http://localhost:8000
```

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| Mobile shell | Capacitor 6 (WebView APK) |
| Frontend | HTML + Tailwind CSS + Firebase JS SDK |
| Backend | FastAPI + Python |
| AI | Google Gemini 2.5 Flash |
| Database | Firebase Firestore |
| Auth | Firebase Authentication |
| Email | Gmail SMTP |
| Hosting | Render (free tier) |
