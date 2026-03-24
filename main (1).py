from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel
import uvicorn
import smtplib
import logging
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google import genai

# Logging Configuration for Terminal
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="LifeGuard Emergency Network")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# CONFIGURATION — loaded from environment variables
# Set these in Render dashboard or your .env file
# NEVER hardcode secrets in source code
# ==========================================
GEMINI_API_KEY  = os.environ.get("GEMINI_API_KEY", "")
SMTP_SERVER     = "smtp.gmail.com"
SMTP_PORT       = 587
SENDER_EMAIL    = os.environ.get("SENDER_EMAIL", "")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD", "")

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

class EmailVerificationRequest(BaseModel):
    email: str
    otp: str

class ChatRequest(BaseModel):
    messages: list
    system: str = ""

@app.post("/api/chat")
async def chat(request: ChatRequest):
    if not client:
        raise HTTPException(status_code=500, detail="Gemini API key not configured")
    try:
        formatted_history = []
        for msg in request.messages[:-1]:
            formatted_history.append({
                "role": "user" if msg["role"] == "user" else "model",
                "parts": [{"text": msg["content"]}]
            })
        chat_session = client.chats.create(
            model="gemini-2.5-flash",
            config={"system_instruction": request.system if request.system else "You are a helpful health assistant."},
            history=formatted_history
        )
        last_message = request.messages[-1]["content"]
        response = chat_session.send_message(last_message)
        return {"content": [{"type": "text", "text": response.text}]}
    except Exception as e:
        logger.error(f"Gemini API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/send-verification-email")
async def send_verification_email(request: EmailVerificationRequest):
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        raise HTTPException(status_code=500, detail="Email credentials not configured")
    try:
        msg = MIMEMultipart()
        msg['From'] = f"LifeGuard Support <{SENDER_EMAIL}>"
        msg['To'] = request.email
        msg['Subject'] = "LifeGuard Account Activation Code"
        body = f"""
        <html>
            <body style="font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #0f172a, #1e3a5f); padding: 40px 20px; margin: 0;">
                <div style="max-width: 480px; margin: auto; background: linear-gradient(145deg, #1e293b, #0f172a); border-radius: 24px; padding: 40px; border: 1px solid rgba(99,179,237,0.2); box-shadow: 0 25px 50px rgba(0,0,0,0.5);">
                    <div style="text-align:center; margin-bottom: 32px;">
                        <h2 style="color: #60a5fa; font-size: 22px; font-weight: 900; margin: 0;">LifeGuard Verification</h2>
                        <p style="color: #94a3b8; font-size: 13px; margin-top: 8px;">Enter this code to activate your account</p>
                    </div>
                    <div style="background: rgba(59,130,246,0.1); border: 2px dashed rgba(59,130,246,0.4); border-radius: 16px; padding: 32px; text-align: center; margin: 24px 0;">
                        <div style="font-size: 48px; font-weight: 900; letter-spacing: 16px; color: #93c5fd; font-family: monospace;">{request.otp}</div>
                    </div>
                    <p style="font-size: 11px; color: #64748b; text-align: center; margin-top: 20px;">Valid for 10 minutes · Do not share this code</p>
                </div>
            </body>
        </html>
        """
        msg.attach(MIMEText(body, 'html'))
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=20)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Mail Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# FRONTEND UI
# ==========================================
html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="theme-color" content="#080c14">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="LifeGuard">
    <meta name="mobile-web-app-capable" content="yes">
    <title>LifeGuard</title>
    <link rel="manifest" href="/manifest.json">
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@0.344.0/dist/umd/lucide.js"></script>
    <style>
        * { -webkit-tap-highlight-color: transparent; }
        :root {
            --bg-deep: #080c14;
            --bg-card: #0f1623;
            --bg-surface: #141d2e;
            --bg-elevated: #1a2540;
            --blue-glow: #3b82f6;
            --blue-soft: #60a5fa;
            --red-vivid: #ef4444;
            --red-glow: #f87171;
            --green-vivid: #10b981;
            --green-glow: #34d399;
            --amber-vivid: #f59e0b;
            --border: rgba(255,255,255,0.06);
            --border-glow: rgba(59,130,246,0.3);
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --text-muted: #475569;
        }
        body { font-family: 'Inter', sans-serif; background: var(--bg-deep); font-size: 14px; }
        h1, h2, h3, .font-display { font-family: 'Plus Jakarta Sans', sans-serif; }
        ::-webkit-scrollbar { width: 0px; background: transparent; }
        .view-container { display: none; height: 100%; width: 100%; flex-direction: column; position: relative; }
        .view-container.active { display: flex; }
        .view-enter { animation: viewEnter 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
        @keyframes viewEnter { from { opacity: 0; transform: translateY(16px) scale(0.98); } to { opacity: 1; transform: translateY(0) scale(1); } }
        .modal-enter { animation: modalEnter 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
        @keyframes modalEnter { from { opacity: 0; transform: translateY(60px); } to { opacity: 1; transform: translateY(0); } }
        .slide-up { animation: modalEnter 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
        .glass { background: rgba(255,255,255,0.04); backdrop-filter: blur(20px); border: 1px solid var(--border); }
        .glass-blue { background: rgba(59,130,246,0.08); backdrop-filter: blur(20px); border: 1px solid rgba(59,130,246,0.2); }
        .text-gradient-blue { background: linear-gradient(135deg, #60a5fa, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
        .btn-primary { background: linear-gradient(135deg, #3b82f6, #2563eb); color: white; font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; font-size: 14px; border-radius: 14px; padding: 14px; width: 100%; border: none; cursor: pointer; transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1); position: relative; overflow: hidden; }
        .btn-primary:active { transform: scale(0.96); }
        .btn-glow-blue { box-shadow: 0 8px 32px rgba(59,130,246,0.35); }
        .btn-danger { background: linear-gradient(135deg, #ef4444, #dc2626); color: white; font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; font-size: 14px; border-radius: 14px; padding: 14px; width: 100%; border: none; cursor: pointer; transition: all 0.2s; }
        .btn-danger:active { transform: scale(0.96); }
        .btn-glow-red { box-shadow: 0 8px 32px rgba(239,68,68,0.35); }
        .btn-success { background: linear-gradient(135deg, #10b981, #059669); color: white; font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; font-size: 14px; border-radius: 14px; padding: 14px; width: 100%; border: none; cursor: pointer; transition: all 0.2s; }
        .btn-success:active { transform: scale(0.96); }
        .btn-glow-green { box-shadow: 0 8px 32px rgba(16,185,129,0.35); }
        .btn-ghost { background: rgba(255,255,255,0.06); color: var(--text-secondary); font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 600; font-size: 14px; border-radius: 14px; padding: 13px; width: 100%; border: 1px solid var(--border); cursor: pointer; transition: all 0.2s; }
        .btn-ghost:active { transform: scale(0.96); }
        .btn-outline-blue { background: transparent; color: #60a5fa; font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; font-size: 14px; border-radius: 14px; padding: 14px; width: 100%; border: 2px solid rgba(59,130,246,0.4); cursor: pointer; transition: all 0.2s; }
        .btn-outline-blue:active { transform: scale(0.96); }
        .input-dark { background: var(--bg-elevated); border: 1px solid var(--border); color: var(--text-primary); border-radius: 12px; padding: 14px 16px; font-size: 14px; font-family: 'Inter', sans-serif; outline: none; transition: all 0.2s; width: 100%; }
        .input-dark::placeholder { color: var(--text-muted); }
        .input-dark:focus { border-color: rgba(59,130,246,0.5); box-shadow: 0 0 0 3px rgba(59,130,246,0.1); }
        .input-dark option { background: #1a2540; }
        .card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 20px; }
        .card-hover { transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1); cursor: pointer; }
        .card-hover:active { transform: scale(0.97); }
        .back-btn { background: rgba(255,255,255,0.08); border: 1px solid var(--border); border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: all 0.2s; color: var(--text-secondary); }
        .back-btn:active { transform: scale(0.9); }
        .pulse-ring { animation: pulseRing 2s cubic-bezier(0.4, 0, 0.6, 1) infinite; }
        @keyframes pulseRing { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.5; transform: scale(1.05); } }
        .bpm-beat { animation: bpmBeat 0.8s ease-in-out infinite; }
        @keyframes bpmBeat { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.04); } }
        .heartbeat-svg { animation: ecgScroll 3s linear infinite; }
        @keyframes ecgScroll { 0% { stroke-dashoffset: 300; } 100% { stroke-dashoffset: -300; } }
        @keyframes floatUp { 0% { opacity: 0; transform: translateY(30px); } 100% { opacity: 1; transform: translateY(0); } }
        .float-1 { animation: floatUp 0.5s ease forwards; }
        .float-2 { animation: floatUp 0.5s 0.08s ease forwards; opacity: 0; }
        .float-3 { animation: floatUp 0.5s 0.16s ease forwards; opacity: 0; }
        .float-4 { animation: floatUp 0.5s 0.24s ease forwards; opacity: 0; }
        @keyframes sosPulse { 0% { box-shadow: 0 0 0 0 rgba(239,68,68,0.7); } 70% { box-shadow: 0 0 0 30px rgba(239,68,68,0); } 100% { box-shadow: 0 0 0 0 rgba(239,68,68,0); } }
        .sos-pulse { animation: sosPulse 1.5s ease infinite; }
        .badge { display: inline-flex; align-items: center; padding: 3px 10px; border-radius: 100px; font-size: 11px; font-weight: 700; font-family: 'Plus Jakarta Sans', sans-serif; }
        .badge-blue { background: rgba(59,130,246,0.15); color: #60a5fa; border: 1px solid rgba(59,130,246,0.25); }
        .badge-red { background: rgba(239,68,68,0.15); color: #f87171; border: 1px solid rgba(239,68,68,0.25); }
        .badge-green { background: rgba(16,185,129,0.15); color: #34d399; border: 1px solid rgba(16,185,129,0.25); }
        .badge-amber { background: rgba(245,158,11,0.15); color: #fbbf24; border: 1px solid rgba(245,158,11,0.25); }
        .dot-live { width: 8px; height: 8px; border-radius: 50%; background: #34d399; animation: liveDot 2s ease infinite; }
        @keyframes liveDot { 0%, 100% { box-shadow: 0 0 0 0 rgba(52,211,153,0.6); } 50% { box-shadow: 0 0 0 6px rgba(52,211,153,0); } }
        .field-label { font-size: 10px; font-weight: 600; font-family: 'Plus Jakarta Sans', sans-serif; text-transform: uppercase; letter-spacing: 0.8px; color: var(--text-muted); display: block; margin-bottom: 6px; }
        .divider { height: 1px; background: var(--border); }
        .custom-scroll::-webkit-scrollbar { width: 3px; }
        .custom-scroll::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }
        #app-container { background: var(--bg-deep); position: relative; }
        .view-container { z-index: 1; }
    </style>
</head>
<body class="h-screen flex justify-center overflow-hidden" style="background:#04080f;">
<div class="w-full max-w-md h-full relative shadow-2xl overflow-hidden flex flex-col" id="app-container">

    <div id="view-role-selection" class="view-container active overflow-y-auto custom-scroll" style="background: var(--bg-deep);">
        <div class="relative px-6 pt-14 pb-16 text-center overflow-hidden" style="background: linear-gradient(180deg, rgba(59,130,246,0.12) 0%, transparent 100%);">
            <div class="relative">
                <div class="flex justify-center mb-5">
                    <div class="relative">
                        <div class="h-16 w-16 rounded-3xl flex items-center justify-center" style="background:linear-gradient(135deg,#3b82f6,#1d4ed8);box-shadow:0 16px 48px rgba(59,130,246,0.35);">
                            <i data-lucide="activity" class="w-8 h-8 text-white"></i>
                        </div>
                        <div class="dot-live absolute -top-1 -right-1 border-2" style="border-color:var(--bg-deep);"></div>
                    </div>
                </div>
                <h1 class="font-display text-3xl font-bold text-white mb-2 tracking-tight">LifeGuard</h1>
                <p class="text-sm font-medium" style="color:var(--text-secondary);">Automated Crisis Response Network</p>
                <div class="mt-6 flex justify-center opacity-30">
                    <svg width="180" height="30" viewBox="0 0 180 30">
                        <polyline points="0,15 30,15 40,5 50,25 60,10 70,20 80,15 180,15" fill="none" stroke="#60a5fa" stroke-width="2" stroke-dasharray="300" class="heartbeat-svg"/>
                    </svg>
                </div>
            </div>
        </div>
        <div class="px-5 pb-8 space-y-3 -mt-4 float-1">
            <button onclick="switchView('view-patient-portal')" class="w-full card card-hover p-5 flex items-center gap-4 text-left group">
                <div class="h-12 w-12 rounded-2xl flex items-center justify-center shrink-0" style="background:linear-gradient(135deg,rgba(59,130,246,0.2),rgba(37,99,235,0.1));border:1px solid rgba(59,130,246,0.3);">
                    <i data-lucide="user" class="w-5 h-5" style="color:#60a5fa;"></i>
                </div>
                <div class="flex-1">
                    <h3 class="font-display font-bold text-base" style="color:var(--text-primary);">Patient Portal</h3>
                    <p class="text-xs mt-0.5" style="color:var(--text-muted);">Vitals monitoring & SOS dispatch</p>
                </div>
                <i data-lucide="chevron-right" class="w-4 h-4" style="color:var(--text-muted);"></i>
            </button>
            <button onclick="switchView('view-donator-portal')" class="w-full card card-hover p-5 flex items-center gap-4 text-left group">
                <div class="h-12 w-12 rounded-2xl flex items-center justify-center shrink-0" style="background:linear-gradient(135deg,rgba(239,68,68,0.2),rgba(220,38,38,0.1));border:1px solid rgba(239,68,68,0.3);">
                    <i data-lucide="droplets" class="w-5 h-5" style="color:#f87171;"></i>
                </div>
                <div class="flex-1">
                    <h3 class="font-display font-bold text-base" style="color:var(--text-primary);">Blood Donor</h3>
                    <p class="text-xs mt-0.5" style="color:var(--text-muted);">Emergency blood registry</p>
                </div>
                <i data-lucide="chevron-right" class="w-4 h-4" style="color:var(--text-muted);"></i>
            </button>
            <button onclick="switchView('view-hospital-login')" class="w-full card card-hover p-5 flex items-center gap-4 text-left group">
                <div class="h-12 w-12 rounded-2xl flex items-center justify-center shrink-0" style="background:linear-gradient(135deg,rgba(16,185,129,0.2),rgba(5,150,105,0.1));border:1px solid rgba(16,185,129,0.3);">
                    <i data-lucide="building-2" class="w-5 h-5" style="color:#34d399;"></i>
                </div>
                <div class="flex-1">
                    <h3 class="font-display font-bold text-base" style="color:var(--text-primary);">Hospital Login</h3>
                    <p class="text-xs mt-0.5" style="color:var(--text-muted);">Dispatcher command hub</p>
                </div>
                <i data-lucide="chevron-right" class="w-4 h-4" style="color:var(--text-muted);"></i>
            </button>
            <button onclick="switchView('view-admin-login')" class="w-full flex items-center gap-3 px-4 py-3 rounded-2xl text-left" style="background:rgba(255,255,255,0.03);border:1px solid var(--border);">
                <div class="h-8 w-8 rounded-xl flex items-center justify-center" style="background:rgba(255,255,255,0.06);">
                    <i data-lucide="shield-check" class="w-4 h-4" style="color:var(--text-muted);"></i>
                </div>
                <span class="text-xs font-semibold uppercase tracking-widest" style="color:var(--text-muted);">Ambulance Admin</span>
                <i data-lucide="chevron-right" class="w-3 h-3 ml-auto" style="color:var(--text-muted);"></i>
            </button>
        </div>
    </div>

    <div id="view-patient-portal" class="view-container" style="background:var(--bg-deep);">
        <div class="absolute top-0 left-0 right-0 h-64 pointer-events-none" style="background:linear-gradient(180deg,rgba(59,130,246,0.1),transparent);"></div>
        <div class="relative flex-1 flex flex-col items-center justify-center p-8 text-center">
            <div class="absolute top-5 left-5">
                <button onclick="switchView('view-role-selection')" class="back-btn"><i data-lucide="arrow-left" class="w-4 h-4"></i></button>
            </div>
            <div class="h-20 w-20 rounded-3xl flex items-center justify-center mb-6 float-1" style="background:linear-gradient(135deg,#3b82f6,#1d4ed8);box-shadow:0 16px 48px rgba(59,130,246,0.35);">
                <i data-lucide="heart-pulse" class="w-10 h-10 text-white"></i>
            </div>
            <h1 class="font-display text-2xl font-bold text-white mb-2 float-2">Patient Access</h1>
            <p class="text-sm mb-10 float-3" style="color:var(--text-secondary);">Monitor vitals & trigger emergency SOS</p>
            <div class="w-full space-y-3 float-4">
                <button onclick="switchView('view-patient-login')" class="btn-primary btn-glow-blue">Login to Dashboard</button>
                <button onclick="switchView('view-patient-reg')" class="btn-outline-blue">Create New Profile</button>
            </div>
        </div>
    </div>

    <div id="view-donator-portal" class="view-container" style="background:var(--bg-deep);">
        <div class="absolute top-0 left-0 right-0 h-64 pointer-events-none" style="background:linear-gradient(180deg,rgba(239,68,68,0.1),transparent);"></div>
        <div class="relative flex-1 flex flex-col items-center justify-center p-8 text-center">
            <div class="absolute top-5 left-5">
                <button onclick="switchView('view-role-selection')" class="back-btn"><i data-lucide="arrow-left" class="w-4 h-4"></i></button>
            </div>
            <div class="h-20 w-20 rounded-3xl flex items-center justify-center mb-6 float-1" style="background:linear-gradient(135deg,#ef4444,#b91c1c);box-shadow:0 16px 48px rgba(239,68,68,0.35);">
                <i data-lucide="heart" class="w-10 h-10 text-white"></i>
            </div>
            <h1 class="font-display text-2xl font-bold text-white mb-2 float-2">Donor Portal</h1>
            <p class="text-sm mb-10 float-3" style="color:var(--text-secondary);">Register and respond to blood emergencies</p>
            <div class="w-full space-y-3 float-4">
                <button onclick="switchView('view-donator-reg')" class="btn-danger btn-glow-red">Register as Donor</button>
                <button onclick="switchView('view-donator-login')" class="btn-ghost">Already Registered</button>
            </div>
        </div>
    </div>

    <div id="view-patient-login" class="view-container overflow-y-auto" style="background:var(--bg-deep);">
        <div class="absolute top-5 left-5 z-10">
            <button onclick="switchView('view-patient-portal')" class="back-btn"><i data-lucide="arrow-left" class="w-4 h-4"></i></button>
        </div>
        <div class="flex-1 flex flex-col justify-center p-8 pt-20">
            <div class="float-1">
                <span class="badge badge-blue mb-4">Patient Login</span>
                <h1 class="font-display text-2xl font-bold text-white mb-1">Welcome back</h1>
                <p class="text-sm mb-8" style="color:var(--text-secondary);">Sign in to your monitoring dashboard</p>
            </div>
            <div class="space-y-4 float-2">
                <div><span class="field-label">Email Address</span><input type="email" id="login-email" placeholder="your@gmail.com" class="input-dark"></div>
                <div><span class="field-label">Password</span><input type="password" id="login-pass" placeholder="••••••••" class="input-dark"></div>
                <div class="pt-2"><button onclick="loginUser('patient')" class="btn-primary btn-glow-blue">Access Dashboard</button></div>
            </div>
        </div>
    </div>

    <div id="view-donator-login" class="view-container overflow-y-auto" style="background:var(--bg-deep);">
        <div class="absolute top-5 left-5 z-10">
            <button onclick="switchView('view-donator-portal')" class="back-btn"><i data-lucide="arrow-left" class="w-4 h-4"></i></button>
        </div>
        <div class="flex-1 flex flex-col justify-center p-8 pt-20">
            <div class="float-1">
                <span class="badge badge-red mb-4">Donor Login</span>
                <h1 class="font-display text-2xl font-bold text-white mb-1">Donor Access</h1>
                <p class="text-sm mb-8" style="color:var(--text-secondary);">View live emergency blood requests</p>
            </div>
            <div class="space-y-4 float-2">
                <div><span class="field-label">Email Address</span><input type="email" id="don-login-email" placeholder="your@gmail.com" class="input-dark"></div>
                <div><span class="field-label">Password</span><input type="password" id="don-login-pass" placeholder="••••••••" class="input-dark"></div>
                <div class="pt-2"><button onclick="loginUser('donator')" class="btn-danger btn-glow-red">View Live Feed</button></div>
            </div>
        </div>
    </div>

    <div id="view-hospital-login" class="view-container overflow-y-auto" style="background:var(--bg-deep);">
        <div class="absolute top-5 left-5 z-10">
            <button onclick="switchView('view-role-selection')" class="back-btn"><i data-lucide="arrow-left" class="w-4 h-4"></i></button>
        </div>
        <div class="flex-1 flex flex-col justify-center p-8 pt-20">
            <div class="float-1">
                <span class="badge badge-green mb-4">Hospital Staff</span>
                <h1 class="font-display text-2xl font-bold text-white mb-1">Command Hub</h1>
                <p class="text-xs px-3 py-1.5 rounded-xl inline-block mb-8" style="background:rgba(16,185,129,0.1);color:#34d399;border:1px solid rgba(16,185,129,0.2);">Requires @lifeguard.com account</p>
            </div>
            <div class="space-y-4 float-2">
                <div><span class="field-label">Staff Email</span><input type="email" id="hosp-user" placeholder="staff@lifeguard.com" class="input-dark"></div>
                <div><span class="field-label">Password</span><input type="password" id="hosp-pass" placeholder="••••••••" class="input-dark"></div>
                <div class="pt-2"><button onclick="loginUser('hospital')" class="btn-success btn-glow-green">Access Hub</button></div>
            </div>
        </div>
    </div>

    <div id="view-admin-login" class="view-container overflow-y-auto" style="background:var(--bg-deep);">
        <div class="absolute top-5 left-5 z-10">
            <button onclick="switchView('view-role-selection')" class="back-btn"><i data-lucide="arrow-left" class="w-4 h-4"></i></button>
        </div>
        <div class="flex-1 flex flex-col justify-center p-8 pt-20">
            <div class="float-1">
                <span class="badge badge-amber mb-4">Admin Access</span>
                <h1 class="font-display text-2xl font-bold text-white mb-1">Fleet Control</h1>
                <p class="text-sm mb-8" style="color:var(--text-secondary);">Ambulance fleet management system</p>
            </div>
            <div class="space-y-4 float-2">
                <div><span class="field-label">Username</span><input type="text" id="admin-user" placeholder="superadmin" class="input-dark"></div>
                <div><span class="field-label">Password</span><input type="password" id="admin-pass" placeholder="••••••••" class="input-dark"></div>
                <div class="pt-2"><button onclick="adminLogin()" class="btn-primary btn-glow-blue">Fleet Login</button></div>
            </div>
        </div>
    </div>

    <div id="view-patient-reg" class="view-container overflow-y-auto custom-scroll" style="background:var(--bg-deep);">
        <div class="sticky top-0 z-20 px-5 py-4 flex items-center gap-3" style="background:rgba(8,12,20,0.9);backdrop-filter:blur(20px);border-bottom:1px solid var(--border);">
            <button onclick="switchView('view-patient-portal')" class="back-btn"><i data-lucide="arrow-left" class="w-4 h-4"></i></button>
            <div>
                <h1 class="font-display font-bold text-white text-base leading-tight">New Patient Registry</h1>
                <p class="text-xs" style="color:var(--text-muted);">Complete all fields to register</p>
            </div>
        </div>
        <div class="p-5 space-y-4 pb-10">
            <div class="grid grid-cols-2 gap-3">
                <div><span class="field-label">First Name</span><input type="text" id="pat-fname" placeholder="First" class="input-dark"></div>
                <div><span class="field-label">Last Name</span><input type="text" id="pat-lname" placeholder="Last" class="input-dark"></div>
            </div>
            <div class="grid grid-cols-2 gap-3">
                <div><span class="field-label">Age</span><input type="number" id="pat-age" placeholder="25" class="input-dark"></div>
                <div><span class="field-label">Blood Type</span>
                    <select id="pat-blood" class="input-dark"><option>A+</option><option>O+</option><option>B+</option><option>AB+</option><option>A-</option><option>B-</option><option>O-</option><option>AB-</option></select>
                </div>
            </div>
            <div><span class="field-label">Gmail Address</span><input type="email" id="pat-email" placeholder="your@gmail.com" class="input-dark"></div>
            <div><span class="field-label">Password</span><input type="password" id="pat-pass" placeholder="••••••••" class="input-dark"></div>
            <div>
                <span class="field-label">Residential Address</span>
                <div class="relative">
                    <textarea id="pat-address" placeholder="Enter address or use GPS..." class="input-dark resize-none" style="height:72px;padding-right:48px;"></textarea>
                    <button onclick="getRegistrationLocation('pat')" class="absolute right-3 top-3 w-8 h-8 rounded-xl flex items-center justify-center" style="background:rgba(59,130,246,0.15);border:1px solid rgba(59,130,246,0.3);">
                        <i data-lucide="map-pin" class="w-4 h-4" style="color:#60a5fa;"></i>
                    </button>
                </div>
            </div>
            <div><span class="field-label">Medical Conditions</span><textarea id="pat-problem" placeholder="e.g. Stroke History, Diabetes..." class="input-dark resize-none" style="height:72px;"></textarea></div>
            <div>
                <span class="field-label">Emergency Contact</span>
                <div class="flex gap-2">
                    <select id="pat-em-code" class="country-code-select input-dark" style="width:100px;flex-shrink:0;"></select>
                    <input type="tel" id="pat-em-phone" placeholder="Emergency number" class="input-dark">
                </div>
            </div>
            <div class="pt-2"><button onclick="registerUser('patient')" class="btn-primary btn-glow-blue">Complete Registry</button></div>
        </div>
    </div>

    <div id="view-donator-reg" class="view-container overflow-y-auto custom-scroll" style="background:var(--bg-deep);">
        <div class="sticky top-0 z-20 px-5 py-4 flex items-center gap-3" style="background:rgba(8,12,20,0.9);backdrop-filter:blur(20px);border-bottom:1px solid var(--border);">
            <button onclick="switchView('view-donator-portal')" class="back-btn"><i data-lucide="arrow-left" class="w-4 h-4"></i></button>
            <div>
                <h1 class="font-display font-bold text-white text-base leading-tight">Donor Enrollment</h1>
                <p class="text-xs" style="color:var(--text-muted);">Join the emergency blood registry</p>
            </div>
        </div>
        <div class="p-5 space-y-4 pb-10">
            <div><span class="field-label">Full Name</span><input type="text" id="don-name" placeholder="Full Name" class="input-dark"></div>
            <div class="grid grid-cols-2 gap-3">
                <div><span class="field-label">Age</span><input type="number" id="don-age" placeholder="25" class="input-dark"></div>
                <div><span class="field-label">Date of Birth</span><input type="date" id="don-dob" class="input-dark"></div>
            </div>
            <div><span class="field-label">Gmail Address</span><input type="email" id="don-email" placeholder="your@gmail.com" class="input-dark"></div>
            <div><span class="field-label">Password</span><input type="password" id="don-pass" placeholder="••••••••" class="input-dark"></div>
            <div>
                <span class="field-label">Mobile Number</span>
                <div class="flex gap-2">
                    <select id="don-mob-code" class="country-code-select input-dark" style="width:100px;flex-shrink:0;"></select>
                    <input type="tel" id="don-mobile" placeholder="Mobile number" class="input-dark">
                </div>
            </div>
            <div><span class="field-label">Blood Type</span>
                <select id="don-blood" class="input-dark"><option>A+</option><option>O+</option><option>B+</option><option>AB+</option><option>A-</option><option>B-</option><option>O-</option><option>AB-</option></select>
            </div>
            <div>
                <span class="field-label">City / Station</span>
                <div class="relative">
                    <textarea id="don-address" placeholder="Your city or station..." class="input-dark resize-none" style="height:72px;padding-right:48px;"></textarea>
                    <button onclick="getRegistrationLocation('don')" class="absolute right-3 top-3 w-8 h-8 rounded-xl flex items-center justify-center" style="background:rgba(239,68,68,0.15);border:1px solid rgba(239,68,68,0.3);">
                        <i data-lucide="map-pin" class="w-4 h-4" style="color:#f87171;"></i>
                    </button>
                </div>
            </div>
            <div class="pt-2"><button onclick="registerUser('donator')" class="btn-danger btn-glow-red">Verify & Register</button></div>
        </div>
    </div>

    <div id="view-patient-dashboard" class="view-container" style="background:var(--bg-deep);">
        <div class="shrink-0 px-5 py-4 flex items-center justify-between" style="border-bottom:1px solid var(--border);background:rgba(8,12,20,0.95);">
            <button onclick="showPatientFullProfile()" class="flex items-center gap-3 active:opacity-70 transition-opacity">
                <div class="h-10 w-10 rounded-2xl flex items-center justify-center" style="background:linear-gradient(135deg,rgba(59,130,246,0.25),rgba(37,99,235,0.15));border:1px solid rgba(59,130,246,0.3);">
                    <i data-lucide="user" class="w-5 h-5" style="color:#60a5fa;"></i>
                </div>
                <div class="text-left">
                    <p class="font-display font-bold text-white text-base leading-tight" id="dash-pat-name">Patient</p>
                    <p class="text-xs" style="color:var(--text-muted);">Tap to view profile</p>
                </div>
            </button>
            <div class="flex items-center gap-2">
                <div class="dot-live"></div>
                <span class="text-xs font-semibold" style="color:#34d399;">Live</span>
            </div>
        </div>
        <main class="flex-1 overflow-y-auto p-5 space-y-4 custom-scroll">
            <div class="card p-6 text-center relative overflow-hidden">
                <div class="absolute inset-0 pointer-events-none" style="background:radial-gradient(circle at 50% 0%,rgba(59,130,246,0.08),transparent 70%);"></div>
                <p class="text-xs font-semibold uppercase tracking-widest mb-5" style="color:var(--text-muted);">Vitals Monitor</p>
                <div class="relative inline-block mb-2">
                    <div class="h-32 w-32 rounded-full flex items-center justify-center mx-auto" style="background:conic-gradient(#3b82f6 0deg 252deg,rgba(59,130,246,0.1) 252deg 360deg);padding:3px;">
                        <div class="h-full w-full rounded-full flex flex-col items-center justify-center" style="background:var(--bg-card);">
                            <div id="bpm-display" class="font-display text-4xl font-bold text-white bpm-beat">72</div>
                            <span class="text-xs font-semibold uppercase tracking-wider mt-1" style="color:#60a5fa;">BPM</span>
                        </div>
                    </div>
                </div>
                <div class="flex justify-center mb-6 opacity-50">
                    <svg width="160" height="24" viewBox="0 0 160 24">
                        <polyline points="0,12 25,12 33,4 42,20 50,8 58,16 66,12 160,12" fill="none" stroke="#3b82f6" stroke-width="1.5" stroke-dasharray="300" class="heartbeat-svg"/>
                    </svg>
                </div>
                <div class="grid grid-cols-3 gap-3 mb-5">
                    <div class="rounded-xl p-3 text-center" style="background:var(--bg-elevated);"><p class="text-xs" style="color:var(--text-muted);">Status</p><p class="font-display font-bold text-sm mt-1" style="color:#34d399;">Normal</p></div>
                    <div class="rounded-xl p-3 text-center" style="background:var(--bg-elevated);"><p class="text-xs" style="color:var(--text-muted);">SpO2</p><p class="font-display font-bold text-sm mt-1" style="color:#60a5fa;">98%</p></div>
                    <div class="rounded-xl p-3 text-center" style="background:var(--bg-elevated);"><p class="text-xs" style="color:var(--text-muted);">Alerts</p><p class="font-display font-bold text-sm mt-1 text-white">0</p></div>
                </div>
                <button onclick="startSimulation()" class="w-full py-3.5 rounded-2xl text-sm font-bold font-display transition-all active:scale-95" style="background:rgba(239,68,68,0.1);color:#f87171;border:1px solid rgba(239,68,68,0.25);">
                    ⚡ Simulate Anomaly
                </button>
            </div>

            <div class="card p-5 relative overflow-hidden">
                <div class="flex items-center justify-between mb-4">
                    <div class="flex items-center gap-2">
                        <div class="h-8 w-8 rounded-xl flex items-center justify-center" style="background:rgba(245,158,11,0.15);border:1px solid rgba(245,158,11,0.25);">
                            <i data-lucide="zap" class="w-4 h-4" style="color:#fbbf24;"></i>
                        </div>
                        <div>
                            <p class="font-display font-bold text-white text-sm">Impact Detection</p>
                            <p class="text-xs" style="color:var(--text-muted);">Shake / Fall sensor</p>
                        </div>
                    </div>
                    <button id="impact-toggle" onclick="toggleImpactDetection()" class="relative w-12 h-6 rounded-full transition-all duration-300" style="background:rgba(255,255,255,0.1);border:1px solid var(--border);">
                        <span id="impact-toggle-dot" class="absolute top-0.5 left-0.5 w-5 h-5 rounded-full transition-all duration-300" style="background:var(--text-muted);"></span>
                    </button>
                </div>
                <div id="impact-controls" class="hidden">
                    <div class="mb-3">
                        <div class="flex justify-between items-center mb-1">
                            <span class="text-xs font-semibold" style="color:var(--text-muted);">Sensitivity</span>
                            <span id="sensitivity-label" class="text-xs font-bold" style="color:#fbbf24;">Medium</span>
                        </div>
                        <input type="range" id="impact-sensitivity" min="1" max="3" value="2" oninput="updateSensitivity(this.value)" class="w-full h-1.5 rounded-full outline-none cursor-pointer" style="accent-color:#f59e0b;">
                    </div>
                    <div class="rounded-xl p-3" style="background:var(--bg-elevated);">
                        <div class="flex justify-between items-center mb-2">
                            <span class="text-xs font-semibold" style="color:var(--text-muted);">Live Impact</span>
                            <span id="gforce-value" class="text-xs font-bold font-display" style="color:#fbbf24;">0.0 G</span>
                        </div>
                        <div class="h-2 rounded-full overflow-hidden" style="background:rgba(255,255,255,0.06);">
                            <div id="gforce-bar" class="h-full rounded-full transition-all duration-100" style="width:0%;background:linear-gradient(90deg,#10b981,#f59e0b,#ef4444);"></div>
                        </div>
                    </div>
                </div>
                <div class="flex items-center gap-2 mt-3">
                    <div id="impact-status-dot" class="w-2 h-2 rounded-full" style="background:var(--text-muted);"></div>
                    <p id="impact-status-text" class="text-xs" style="color:var(--text-muted);">Tap toggle to activate</p>
                </div>
            </div>

            <div class="card p-5 relative overflow-hidden card-hover" onclick="openHealthBot()">
                <div class="flex items-center gap-3">
                    <div class="h-11 w-11 rounded-2xl flex items-center justify-center shrink-0" style="background:linear-gradient(135deg,rgba(16,185,129,0.2),rgba(5,150,105,0.1));border:1px solid rgba(16,185,129,0.3);">
                        <i data-lucide="bot" class="w-5 h-5" style="color:#34d399;"></i>
                    </div>
                    <div class="flex-1">
                        <p class="font-display font-bold text-white text-sm">LifeGuard Health AI</p>
                        <p class="text-xs mt-0.5" style="color:var(--text-muted);">Ask symptoms · Book appointment</p>
                    </div>
                    <div class="flex flex-col items-end gap-1">
                        <span class="badge badge-green text-xs">AI</span>
                    </div>
                </div>
                <div class="mt-3 flex gap-2 flex-wrap">
                    <span class="text-xs px-2.5 py-1 rounded-xl" style="background:rgba(16,185,129,0.1);color:#34d399;border:1px solid rgba(16,185,129,0.15);">💊 Minor diseases</span>
                    <span class="text-xs px-2.5 py-1 rounded-xl" style="background:rgba(59,130,246,0.1);color:#60a5fa;border:1px solid rgba(59,130,246,0.15);">📅 Book appointment</span>
                    <span class="text-xs px-2.5 py-1 rounded-xl" style="background:rgba(245,158,11,0.1);color:#fbbf24;border:1px solid rgba(245,158,11,0.15);">❓ Health advice</span>
                </div>
            </div>

            <div class="rounded-2xl p-4 flex items-center gap-3" style="background:rgba(59,130,246,0.06);border:1px solid rgba(59,130,246,0.15);">
                <i data-lucide="shield" class="w-5 h-5 shrink-0" style="color:#60a5fa;"></i>
                <p class="text-xs leading-relaxed" style="color:var(--text-secondary);">LifeGuard monitors your vitals and auto-dispatches rescue if an anomaly is detected.</p>
            </div>
        </main>

        <div id="sos-overlay" class="absolute inset-0 z-[200] flex flex-col items-center justify-center hidden p-10 text-center" style="background:linear-gradient(145deg,#7f1d1d,#991b1b,#b91c1c);">
            <div class="relative">
                <div class="h-24 w-24 rounded-full flex items-center justify-center mx-auto mb-6 sos-pulse" style="background:rgba(255,255,255,0.1);border:2px solid rgba(255,255,255,0.2);">
                    <i data-lucide="alert-triangle" class="w-11 h-11 text-white pulse-ring"></i>
                </div>
                <h2 class="font-display text-3xl font-bold text-white mb-3 uppercase tracking-tight">Emergency!</h2>
                <p class="text-red-200 text-sm mb-3">Rescue dispatch in</p>
                <div class="font-display text-6xl font-extrabold text-white mb-10" id="countdown-text">10</div>
                <button onclick="cancelSOS()" class="py-5 px-14 rounded-full font-display font-extrabold text-red-600 uppercase tracking-wider text-sm active:scale-95 transition-all" style="background:white;box-shadow:0 20px 60px rgba(0,0,0,0.4);">CANCEL SOS</button>
            </div>
        </div>

        <div id="sos-contacts-view" class="absolute inset-0 z-[210] flex flex-col items-center justify-start hidden p-6 pt-14 text-center" style="background:linear-gradient(145deg,#7f1d1d,#991b1b);">
            <div class="relative mb-5">
                <div class="absolute inset-0 rounded-full animate-ping" style="background:rgba(255,255,255,0.15);"></div>
                <div class="h-16 w-16 rounded-full flex items-center justify-center relative" style="background:white;box-shadow:0 12px 40px rgba(0,0,0,0.4);">
                    <i data-lucide="phone-incoming" class="w-8 h-8 text-red-600"></i>
                </div>
            </div>
            <h2 class="font-display text-xl font-bold text-white uppercase mb-1">SOS ACTIVE</h2>
            <p class="text-red-200 text-xs mb-6">LifeGuard is broadcasting your GPS coordinates.</p>
            <div class="w-full rounded-2xl p-4 mb-3 text-left" style="background:rgba(255,255,255,0.12);border:1px solid rgba(255,255,255,0.2);">
                <div class="flex items-center gap-2 mb-1">
                    <span class="text-xs font-semibold uppercase tracking-widest text-red-300">Emergency Contact</span>
                </div>
                <p id="sos-display-contact" class="font-display text-xl font-bold text-white mt-1">--</p>
                <a id="sos-call-contact" href="tel:--" class="mt-2 inline-flex items-center gap-1.5 text-xs font-semibold py-1.5 px-3 rounded-lg" style="background:rgba(255,255,255,0.15);color:white;">Call Now</a>
            </div>
            <div class="w-full rounded-2xl p-4 mb-5 text-left" style="background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.15);">
                <span class="text-xs font-semibold uppercase tracking-widest text-red-300">Nearest Ambulance</span>
                <p id="sos-ambulance-driver" class="font-display font-bold text-white text-base mt-1">Searching...</p>
                <p id="sos-ambulance-vehicle" class="text-xs text-red-200 mt-0.5"></p>
                <p id="sos-ambulance-number" class="font-display text-lg font-bold text-white mt-1"></p>
                <a id="sos-call-ambulance" href="tel:--" class="mt-2 inline-flex items-center gap-1.5 text-xs font-semibold py-1.5 px-3 rounded-lg" style="background:rgba(255,255,255,0.15);color:white;">Call Ambulance</a>
            </div>
            <button onclick="stopAlarmAndReset()" class="mt-auto w-full py-3.5 rounded-2xl font-display font-bold text-white transition-all active:scale-95" style="background:rgba(255,255,255,0.15);border:1px solid rgba(255,255,255,0.2);">I'M OKAY NOW</button>
        </div>
    </div>

    <div id="view-donator-dashboard" class="view-container" style="background:var(--bg-deep);">
        <div class="shrink-0 px-5 py-4 flex items-center justify-between" style="background:linear-gradient(90deg,rgba(239,68,68,0.12),rgba(239,68,68,0.06));border-bottom:1px solid rgba(239,68,68,0.15);">
            <div class="flex items-center gap-3">
                <div class="h-9 w-9 rounded-xl flex items-center justify-center" style="background:rgba(239,68,68,0.2);border:1px solid rgba(239,68,68,0.3);">
                    <i data-lucide="droplets" class="w-4 h-4" style="color:#f87171;"></i>
                </div>
                <div>
                    <h1 class="font-display font-bold text-white text-base">Emergency Feed</h1>
                    <div class="flex items-center gap-1.5"><div class="dot-live"></div><span class="text-xs" style="color:#34d399;">Live requests</span></div>
                </div>
            </div>
            <div class="flex gap-2">
                <button onclick="fetchEmergencyRequests()" class="back-btn"><i data-lucide="refresh-cw" class="w-4 h-4"></i></button>
                <button onclick="logout()" class="back-btn"><i data-lucide="log-out" class="w-4 h-4"></i></button>
            </div>
        </div>
        <main class="flex-1 overflow-y-auto p-4 space-y-3 custom-scroll" id="donator-emergency-list">
            <div class="flex items-center justify-center h-full"><p class="text-sm" style="color:var(--text-muted);">Loading requests...</p></div>
        </main>
    </div>

    <div id="view-hospital-dashboard" class="view-container overflow-hidden relative" style="background:var(--bg-deep);">
        <div class="shrink-0 px-5 py-4 flex items-center justify-between" style="background:linear-gradient(90deg,rgba(16,185,129,0.12),rgba(16,185,129,0.06));border-bottom:1px solid rgba(16,185,129,0.15);">
            <div class="flex items-center gap-3">
                <div class="h-9 w-9 rounded-xl flex items-center justify-center" style="background:rgba(16,185,129,0.2);border:1px solid rgba(16,185,129,0.3);">
                    <i data-lucide="building-2" class="w-4 h-4" style="color:#34d399;"></i>
                </div>
                <h1 class="font-display font-bold text-white text-base" id="hosp-admin-name">Hospital Hub</h1>
            </div>
            <button onclick="logout()" class="back-btn"><i data-lucide="log-out" class="w-4 h-4"></i></button>
        </div>
        <div class="shrink-0 p-4" style="background:rgba(16,185,129,0.05);border-bottom:1px solid rgba(16,185,129,0.1);">
            <p class="field-label mb-3" style="color:#34d399;">Post Emergency Alert</p>
            <div class="space-y-2">
                <input type="text" id="req-hosp-name" placeholder="Hospital Name" class="input-dark">
                <div class="grid grid-cols-2 gap-2">
                    <select id="req-blood" class="input-dark"><option>A+</option><option>O+</option><option>B+</option><option>AB+</option><option>A-</option><option>B-</option><option>O-</option><option>AB-</option></select>
                    <input type="number" id="req-units" placeholder="Units needed" class="input-dark">
                </div>
                <input type="text" id="req-reason" placeholder="Incident Type" class="input-dark">
                <button onclick="postBloodRequest()" class="btn-success btn-glow-green" style="padding:12px;">Dispatch Blood Signal</button>
            </div>
        </div>
        <div class="shrink-0 px-4 py-3" style="border-bottom:1px solid var(--border);">
            <p class="field-label mb-2">My Signals</p>
            <div id="hospital-my-requests-list" class="space-y-2 max-h-28 overflow-y-auto custom-scroll"></div>
        </div>
        <div class="shrink-0 p-4 space-y-2" style="border-bottom:1px solid var(--border);">
            <p class="field-label">Find Donors</p>
            <div class="grid grid-cols-2 gap-2">
                <input type="text" id="filter-name" placeholder="Donor Name" class="input-dark">
                <input type="text" id="filter-city" placeholder="City" class="input-dark">
            </div>
            <div class="grid grid-cols-2 gap-2">
                <select id="filter-blood-reg" class="input-dark"><option value="">All Blood</option><option>A+</option><option>O+</option><option>B+</option><option>AB+</option><option>A-</option><option>B-</option><option>O-</option><option>AB-</option></select>
                <input type="date" id="filter-dob-reg" class="input-dark">
            </div>
            <button onclick="applyDonorFilters()" class="btn-success" style="padding:10px;font-size:13px;">Apply Filters</button>
        </div>
        <main class="flex-1 overflow-y-auto p-4 space-y-3 custom-scroll" id="hospital-donor-list"></main>
    </div>

    <div id="view-admin-dashboard" class="view-container overflow-hidden relative" style="background:var(--bg-deep);">
        <div class="shrink-0 px-5 py-4 flex items-center justify-between" style="background:rgba(255,255,255,0.03);border-bottom:1px solid var(--border);">
            <div class="flex items-center gap-3">
                <div class="h-9 w-9 rounded-xl flex items-center justify-center" style="background:rgba(245,158,11,0.15);border:1px solid rgba(245,158,11,0.25);">
                    <i data-lucide="shield" class="w-4 h-4" style="color:#fbbf24;"></i>
                </div>
                <h1 class="font-display font-bold text-white text-base">Fleet Management</h1>
            </div>
            <button onclick="logout()" class="back-btn"><i data-lucide="log-out" class="w-4 h-4"></i></button>
        </div>
        <div class="shrink-0 p-4" style="background:rgba(59,130,246,0.04);border-bottom:1px solid var(--border);">
            <p class="field-label mb-3" style="color:#60a5fa;">Add Ambulance Unit</p>
            <div class="space-y-2">
                <div class="grid grid-cols-2 gap-2">
                    <input type="text" id="amb-driver" placeholder="Driver Name" class="input-dark">
                    <input type="text" id="amb-vehicle" placeholder="Plate No." class="input-dark">
                </div>
                <div class="grid grid-cols-2 gap-2">
                    <input type="tel" id="amb-mobile" placeholder="Phone" class="input-dark">
                    <input type="text" id="amb-licence" placeholder="Licence No." class="input-dark">
                </div>
                <div class="grid grid-cols-2 gap-2">
                    <input type="text" id="amb-location" placeholder="Station" class="input-dark">
                    <input type="text" id="amb-cert" placeholder="Certificate No." class="input-dark">
                </div>
                <button onclick="registerAmbulance()" class="btn-primary btn-glow-blue" style="padding:12px;">Add to Fleet</button>
            </div>
        </div>
        <main class="flex-1 overflow-y-auto p-4 space-y-3 custom-scroll" id="admin-ambulance-list"></main>
    </div>

    <div id="view-patient-otp" class="view-container hidden flex flex-col items-center justify-center text-center p-8" style="background:var(--bg-deep);">
        <div class="h-16 w-16 rounded-2xl flex items-center justify-center mb-5 float-1" style="background:linear-gradient(135deg,rgba(59,130,246,0.2),rgba(37,99,235,0.1));border:1px solid rgba(59,130,246,0.3);">
            <i data-lucide="mail-check" class="w-8 h-8" style="color:#60a5fa;"></i>
        </div>
        <h2 class="font-display text-xl font-bold text-white mb-2 float-2">Verify Account</h2>
        <p class="text-sm mb-2 float-2" style="color:var(--text-secondary);">Code sent to</p>
        <p id="display-pat-email" class="font-bold mb-10 float-2" style="color:#60a5fa;font-size:13px;"></p>
        <div class="flex gap-3 mb-8 float-3">
            <input type="text" id="otp-1" maxlength="1" class="w-12 h-14 border-2 rounded-xl text-center font-display text-2xl font-bold text-white outline-none" style="background:var(--bg-elevated);border-color:var(--border);">
            <input type="text" id="otp-2" maxlength="1" class="w-12 h-14 border-2 rounded-xl text-center font-display text-2xl font-bold text-white outline-none" style="background:var(--bg-elevated);border-color:var(--border);">
            <input type="text" id="otp-3" maxlength="1" class="w-12 h-14 border-2 rounded-xl text-center font-display text-2xl font-bold text-white outline-none" style="background:var(--bg-elevated);border-color:var(--border);">
            <input type="text" id="otp-4" maxlength="1" class="w-12 h-14 border-2 rounded-xl text-center font-display text-2xl font-bold text-white outline-none" style="background:var(--bg-elevated);border-color:var(--border);">
        </div>
        <div class="w-full float-4"><button onclick="verifyOTP()" class="btn-primary btn-glow-blue">Confirm Code</button></div>
    </div>

    <div id="patient-detail-modal" class="absolute inset-0 z-[300] hidden flex flex-col" style="background:var(--bg-deep);">
        <div class="slide-up flex flex-col h-full">
            <div class="shrink-0 px-5 py-5 flex items-center gap-3" style="background:linear-gradient(135deg,rgba(59,130,246,0.2),rgba(37,99,235,0.05));border-bottom:1px solid rgba(59,130,246,0.2);">
                <button onclick="document.getElementById('patient-detail-modal').classList.add('hidden')" class="back-btn"><i data-lucide="arrow-left" class="w-4 h-4"></i></button>
                <div><h2 class="font-display font-bold text-white text-base">My Profile</h2></div>
            </div>
            <div class="flex-1 overflow-y-auto p-5 space-y-4 custom-scroll">
                <div class="text-center py-4">
                    <div class="h-20 w-20 rounded-3xl flex items-center justify-center mx-auto mb-4" style="background:linear-gradient(135deg,rgba(59,130,246,0.2),rgba(37,99,235,0.1));border:1px solid rgba(59,130,246,0.3);">
                        <i data-lucide="user" class="w-9 h-9" style="color:#60a5fa;"></i>
                    </div>
                    <h1 id="prof-pat-name" class="font-display text-xl font-bold text-white mb-3">--</h1>
                    <div class="flex gap-2 justify-center flex-wrap">
                        <span id="prof-pat-blood" class="badge badge-red">--</span>
                        <span class="badge badge-blue">Patient</span>
                    </div>
                </div>
                <div class="divider"></div>
                <div class="grid grid-cols-2 gap-3">
                    <div class="rounded-2xl p-4" style="background:var(--bg-card);border:1px solid var(--border);"><span class="field-label">Age</span><p id="prof-pat-age" class="font-display font-semibold text-white text-base mt-1">--</p></div>
                    <div class="rounded-2xl p-4" style="background:var(--bg-card);border:1px solid var(--border);"><span class="field-label">Blood Type</span><p id="prof-pat-blood-grid" class="font-display font-semibold text-base mt-1" style="color:#f87171;">--</p></div>
                </div>
                <div class="rounded-2xl p-4" style="background:var(--bg-card);border:1px solid var(--border);"><span class="field-label">Email</span><p id="prof-pat-email" class="font-medium text-sm mt-1" style="color:#60a5fa;">--</p></div>
                <div class="rounded-2xl p-4" style="background:var(--bg-card);border:1px solid var(--border);"><span class="field-label">Address</span><p id="prof-pat-address" class="text-sm mt-1" style="color:var(--text-secondary);">--</p></div>
                <div class="rounded-2xl p-4" style="background:rgba(59,130,246,0.06);border:1px solid rgba(59,130,246,0.2);"><span class="field-label" style="color:#60a5fa;">SOS Emergency Contact</span><p id="prof-pat-emergency" class="font-display font-bold text-base mt-1" style="color:#93c5fd;">--</p></div>
                <div class="rounded-2xl p-4" style="background:rgba(245,158,11,0.06);border:1px solid rgba(245,158,11,0.2);"><span class="field-label" style="color:#fbbf24;">Medical History</span><p id="prof-pat-problem-detail" class="text-sm mt-1 italic" style="color:var(--text-secondary);">--</p></div>
            </div>
            <div class="shrink-0 p-5 space-y-3" style="border-top:1px solid var(--border);">
                <button onclick="logout()" class="btn-ghost">Logout</button>
                <button onclick="deletePatientAccount()" class="btn-danger btn-glow-red">Remove Account</button>
            </div>
        </div>
    </div>

    <div id="full-donor-modal" class="absolute inset-0 z-[310] hidden flex flex-col" style="background:var(--bg-deep);">
        <div class="slide-up flex flex-col h-full">
            <div class="shrink-0 px-5 py-5 flex items-center gap-3" style="background:rgba(16,185,129,0.08);border-bottom:1px solid rgba(16,185,129,0.2);">
                <button onclick="document.getElementById('full-donor-modal').classList.add('hidden')" class="back-btn"><i data-lucide="arrow-left" class="w-4 h-4"></i></button>
                <div><h2 class="font-display font-bold text-white text-base">Donor Profile</h2></div>
            </div>
            <div id="full-donor-content" class="flex-1 overflow-y-auto p-5 space-y-4 custom-scroll"></div>
            <div class="shrink-0 p-5" style="border-top:1px solid var(--border);">
                <button onclick="document.getElementById('full-donor-modal').classList.add('hidden')" class="btn-success btn-glow-green">Close Profile</button>
            </div>
        </div>
    </div>

    <div id="ambulance-detail-modal" class="absolute inset-0 z-[320] hidden flex flex-col" style="background:var(--bg-deep);">
        <div class="slide-up flex flex-col h-full">
            <div class="shrink-0 px-5 py-5 flex items-center gap-3" style="background:rgba(59,130,246,0.08);border-bottom:1px solid rgba(59,130,246,0.2);">
                <button onclick="document.getElementById('ambulance-detail-modal').classList.add('hidden')" class="back-btn"><i data-lucide="arrow-left" class="w-4 h-4"></i></button>
                <div><h2 class="font-display font-bold text-white text-base">Fleet Unit</h2></div>
            </div>
            <div id="ambulance-detail-content" class="flex-1 overflow-y-auto p-5 custom-scroll"></div>
            <div class="shrink-0 p-5" style="border-top:1px solid var(--border);">
                <button onclick="document.getElementById('ambulance-detail-modal').classList.add('hidden')" class="btn-primary btn-glow-blue">Close</button>
            </div>
        </div>
    </div>

    <div id="emergency-dispatch-modal" class="absolute inset-x-4 bottom-4 z-[500] hidden rounded-3xl p-5 slide-up" style="background:linear-gradient(135deg,#7f1d1d,#991b1b);border:1px solid rgba(239,68,68,0.3);box-shadow:0 25px 80px rgba(239,68,68,0.4);">
        <div class="flex justify-between items-start mb-4">
            <span class="badge" style="background:rgba(255,255,255,0.15);color:white;border:none;">LIVE ALERT</span>
            <button onclick="this.parentElement.parentElement.classList.add('hidden')" class="h-8 w-8 rounded-full flex items-center justify-center" style="background:rgba(255,255,255,0.1);">
                <i data-lucide="x" class="w-4 h-4 text-white"></i>
            </button>
        </div>
        <h3 class="font-display text-base font-bold text-white uppercase mb-4">Patient SOS Alert!</h3>
        <div class="rounded-2xl p-4 space-y-3 mb-5" style="background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.1);">
            <div class="flex justify-between items-center">
                <span class="text-xs font-bold uppercase tracking-widest text-red-200">Patient</span>
                <span id="modal-sos-name" class="font-display font-bold text-white">--</span>
            </div>
            <div class="divider" style="background:rgba(255,255,255,0.1);"></div>
            <div class="flex justify-between items-center">
                <span class="text-xs font-bold uppercase tracking-widest text-red-200">GPS</span>
                <span id="modal-sos-location" class="font-mono text-xs text-white">--</span>
            </div>
        </div>
        <button onclick="acknowledgeSOS()" class="w-full py-4 rounded-2xl font-display font-extrabold text-red-700 uppercase tracking-wider text-sm active:scale-95 transition-all" style="background:white;">Dispatch Response Unit</button>
    </div>

    <div id="healthbot-modal" class="absolute inset-0 z-[400] hidden flex flex-col" style="background:var(--bg-deep);">
        <div class="slide-up flex flex-col h-full">
            <div class="shrink-0 px-5 py-4 flex items-center gap-3" style="background:linear-gradient(135deg,rgba(16,185,129,0.15),rgba(5,150,105,0.05));border-bottom:1px solid rgba(16,185,129,0.2);">
                <button onclick="closeHealthBot()" class="back-btn"><i data-lucide="arrow-left" class="w-4 h-4"></i></button>
                <div class="h-9 w-9 rounded-xl flex items-center justify-center" style="background:linear-gradient(135deg,#10b981,#059669);box-shadow:0 4px 16px rgba(16,185,129,0.3);">
                    <i data-lucide="bot" class="w-5 h-5 text-white"></i>
                </div>
                <div class="flex-1">
                    <h2 class="font-display font-bold text-white text-sm leading-tight">LifeGuard Health AI</h2>
                    <div class="flex items-center gap-1.5 mt-0.5">
                        <div class="dot-live" style="width:6px;height:6px;"></div>
                        <span class="text-xs" style="color:#34d399;">Powered by Gemini</span>
                    </div>
                </div>
                <button onclick="clearChat()" class="back-btn"><i data-lucide="rotate-ccw" class="w-4 h-4"></i></button>
            </div>
            <div id="bot-quick-chips" class="shrink-0 px-4 py-3 flex gap-2 overflow-x-auto" style="border-bottom:1px solid var(--border);scrollbar-width:none;">
                <button onclick="sendQuickMessage('I have a headache and fever')" class="text-xs px-3 py-1.5 rounded-xl whitespace-nowrap font-medium" style="background:rgba(239,68,68,0.1);color:#f87171;border:1px solid rgba(239,68,68,0.2);">🤒 Headache & fever</button>
                <button onclick="sendQuickMessage('I have a cold and sore throat')" class="text-xs px-3 py-1.5 rounded-xl whitespace-nowrap font-medium" style="background:rgba(59,130,246,0.1);color:#60a5fa;border:1px solid rgba(59,130,246,0.2);">🤧 Cold & throat</button>
                <button onclick="sendQuickMessage('I want to book a doctor appointment')" class="text-xs px-3 py-1.5 rounded-xl whitespace-nowrap font-medium" style="background:rgba(16,185,129,0.1);color:#34d399;border:1px solid rgba(16,185,129,0.2);">📅 Book appointment</button>
                <button onclick="sendQuickMessage('I have stomach pain and nausea')" class="text-xs px-3 py-1.5 rounded-xl whitespace-nowrap font-medium" style="background:rgba(245,158,11,0.1);color:#fbbf24;border:1px solid rgba(245,158,11,0.2);">🤢 Stomach pain</button>
            </div>
            <div id="bot-messages" class="flex-1 overflow-y-auto p-4 space-y-4 custom-scroll"></div>
            <div id="bot-typing" class="hidden px-4 pb-2">
                <div class="flex items-center gap-2">
                    <div class="h-7 w-7 rounded-full flex items-center justify-center shrink-0" style="background:rgba(16,185,129,0.15);border:1px solid rgba(16,185,129,0.2);">
                        <i data-lucide="bot" class="w-3.5 h-3.5" style="color:#34d399;"></i>
                    </div>
                    <div class="flex gap-1 px-3 py-2 rounded-2xl" style="background:var(--bg-card);border:1px solid var(--border);">
                        <span class="w-1.5 h-1.5 rounded-full animate-bounce" style="background:#34d399;animation-delay:0ms;"></span>
                        <span class="w-1.5 h-1.5 rounded-full animate-bounce" style="background:#34d399;animation-delay:150ms;"></span>
                        <span class="w-1.5 h-1.5 rounded-full animate-bounce" style="background:#34d399;animation-delay:300ms;"></span>
                    </div>
                </div>
            </div>
            <div class="shrink-0 p-4 flex gap-3 items-end" style="border-top:1px solid var(--border);background:rgba(8,12,20,0.9);">
                <textarea id="bot-input" placeholder="Ask about symptoms or book appointment..." rows="1"
                    class="flex-1 resize-none rounded-2xl px-4 py-3 text-sm outline-none"
                    style="background:var(--bg-elevated);border:1px solid var(--border);color:var(--text-primary);font-family:'Inter',sans-serif;max-height:100px;"
                    onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();sendBotMessage();}"
                    oninput="this.style.height='auto';this.style.height=Math.min(this.scrollHeight,100)+'px'"></textarea>
                <button onclick="sendBotMessage()" class="h-11 w-11 rounded-2xl flex items-center justify-center shrink-0" style="background:linear-gradient(135deg,#10b981,#059669);box-shadow:0 4px 16px rgba(16,185,129,0.3);">
                    <i data-lucide="send" class="w-4 h-4 text-white"></i>
                </button>
            </div>
        </div>
    </div>

</div>

<script type="module">
    import { initializeApp } from "https://www.gstatic.com/firebasejs/11.6.1/firebase-app.js";
    import { getAuth, createUserWithEmailAndPassword, signInWithEmailAndPassword, signOut, deleteUser } from "https://www.gstatic.com/firebasejs/11.6.1/firebase-auth.js";
    import { getFirestore, doc, setDoc, getDoc, collection, getDocs, addDoc, onSnapshot, deleteDoc } from "https://www.gstatic.com/firebasejs/11.6.1/firebase-firestore.js";

    // ==========================================
    // FIREBASE CONFIG
    // These client-side keys are safe to be public.
    // Restrict them in Firebase Console > App Check
    // and set Firestore Security Rules.
    // ==========================================
    const firebaseConfig = {
        apiKey: "AIzaSyDoeK8KE3LemRo6FOV8H2Q1ugwG4gAQbb8",
        authDomain: "lifeguard-emergency.firebaseapp.com",
        projectId: "lifeguard-emergency",
        storageBucket: "lifeguard-emergency.firebasestorage.app",
        messagingSenderId: "1083414319766",
        appId: "1:1083414319766:web:cd324a1b38234bf5dca8b7"
    };

    const app = initializeApp(firebaseConfig);
    const auth = getAuth(app);
    const db = getFirestore(app);
    const appId = "lifeguard-emergency";

    let allDonors = [];
    let allAmbulances = [];
    let sosUnsubscribe = null;
    window.currentHospitalProfile = null;
    window.currentPatientProfile = null;
    window.pendingVerificationData = null;

    window.switchView = function(viewId) {
        document.querySelectorAll('.view-container').forEach(v => v.classList.remove('active'));
        const target = document.getElementById(viewId);
        if (target) {
            target.classList.add('active');
            target.classList.remove('view-enter');
            void target.offsetWidth;
            target.classList.add('view-enter');
        }
        if (window.lucide) lucide.createIcons();
        if (viewId === 'view-hospital-dashboard' || viewId === 'view-admin-dashboard') {
            fetchDonors(); fetchHospitalMyRequests();
            if (viewId === 'view-admin-dashboard') fetchAmbulanceFleet();
            startGlobalSOSListener();
        } else if (sosUnsubscribe) { sosUnsubscribe(); sosUnsubscribe = null; }
        if (viewId === 'view-donator-dashboard') fetchEmergencyRequests();
    }

    window.getRegistrationLocation = function(type) {
        const el = document.getElementById(type === 'pat' ? 'pat-address' : 'don-address');
        if (navigator.geolocation) {
            el.value = "Acquiring GPS...";
            navigator.geolocation.getCurrentPosition(
                (pos) => { el.value = `Lat: ${pos.coords.latitude.toFixed(4)}, Lng: ${pos.coords.longitude.toFixed(4)}`; },
                () => { el.value = "GPS Access Denied."; }
            );
        }
    }

    window.loginUser = async function(role) {
        const email = (role === 'hospital' ? document.getElementById('hosp-user').value :
            (role === 'donator' ? document.getElementById('don-login-email').value :
                document.getElementById('login-email').value)).toLowerCase().trim();
        const pass = role === 'hospital' ? document.getElementById('hosp-pass').value :
            (role === 'donator' ? document.getElementById('don-login-pass').value :
                document.getElementById('login-pass').value);
        if (role === 'hospital' && !email.endsWith("@lifeguard.com")) { alert("Staff accounts require @lifeguard.com"); return; }
        try {
            const userCred = await signInWithEmailAndPassword(auth, email, pass);
            const snap = await getDoc(doc(db, "artifacts", appId, "users", userCred.user.uid, "profile", "details"));
            const profile = snap.exists() ? snap.data() : null;
            if (role === 'hospital') {
                window.currentHospitalProfile = profile;
                document.getElementById('hosp-admin-name').innerText = profile?.hospital_name || "Hospital Hub";
                document.getElementById('req-hosp-name').value = profile?.hospital_name || "";
                switchView('view-hospital-dashboard');
            } else if (role === 'patient' && profile?.role === 'patient') {
                window.currentPatientProfile = profile;
                document.getElementById('dash-pat-name').innerText = profile.fname;
                switchView('view-patient-dashboard');
            } else if (role === 'donator' && profile?.role === 'donator') {
                window.currentPatientProfile = profile;
                switchView('view-donator-dashboard');
            }
        } catch (e) { alert("Login failed. Check your credentials."); }
    }

    window.registerUser = async function(role) {
        try {
            await signOut(auth);
            let data, email, pass;
            if (role === 'patient') {
                email = document.getElementById('pat-email').value.trim();
                pass = document.getElementById('pat-pass').value;
                data = { role: "patient", fname: document.getElementById('pat-fname').value, lname: document.getElementById('pat-lname').value, age: document.getElementById('pat-age').value, email: email, blood: document.getElementById('pat-blood').value, address: document.getElementById('pat-address').value, emergency: document.getElementById('pat-em-code').value + document.getElementById('pat-em-phone').value, problem: document.getElementById('pat-problem').value };
            } else {
                email = document.getElementById('don-email').value.trim();
                pass = document.getElementById('don-pass').value;
                data = { role: "donator", name: document.getElementById('don-name').value, age: document.getElementById('don-age').value, dob: document.getElementById('don-dob').value, email: email, mobile: document.getElementById('don-mob-code').value + document.getElementById('don-mobile').value, blood: document.getElementById('don-blood').value, address: document.getElementById('don-address').value };
            }
            const userCred = await createUserWithEmailAndPassword(auth, email, pass);
            await setDoc(doc(db, "artifacts", appId, "users", userCred.user.uid, "profile", "details"), { ...data, createdAt: new Date().toISOString() });
            window.pendingVerificationData = { role, uid: userCred.user.uid, data, email };
            generateOTP();
        } catch (e) { alert("Registry error: " + e.message); }
    }

    window.showPatientFullProfile = function() {
        const p = window.currentPatientProfile; if (!p) return;
        document.getElementById('prof-pat-name').innerText = `${p.fname} ${p.lname}`;
        document.getElementById('prof-pat-blood').innerText = p.blood || '--';
        document.getElementById('prof-pat-blood-grid').innerText = p.blood || '--';
        document.getElementById('prof-pat-age').innerText = p.age || '--';
        document.getElementById('prof-pat-email').innerText = p.email || '--';
        document.getElementById('prof-pat-address').innerText = p.address || 'Not provided.';
        document.getElementById('prof-pat-emergency').innerText = p.emergency || '--';
        document.getElementById('prof-pat-problem-detail').innerText = p.problem || "None registered.";
        document.getElementById('patient-detail-modal').classList.remove('hidden');
        if (window.lucide) lucide.createIcons();
    }

    window.deletePatientAccount = async function() {
        if (!confirm("This will permanently delete your account.")) return;
        try {
            await deleteDoc(doc(db, "artifacts", appId, "users", auth.currentUser.uid, "profile", "details"));
            await deleteUser(auth.currentUser);
            window.location.reload();
        } catch (e) { alert("Please logout and login again before deletion."); }
    }

    function startGlobalSOSListener() {
        if (sosUnsubscribe) return;
        sosUnsubscribe = onSnapshot(collection(db, "artifacts", appId, "public", "data", "sos_signals"), (snapshot) => {
            snapshot.docChanges().forEach((change) => {
                if (change.type === "added") {
                    const data = change.doc.data();
                    if ((new Date() - new Date(data.timestamp)) < 600000) {
                        document.getElementById('modal-sos-name').innerText = data.patientName;
                        document.getElementById('modal-sos-location').innerText = data.location;
                        document.getElementById('emergency-dispatch-modal').classList.remove('hidden');
                        if (window.lucide) lucide.createIcons();
                    }
                }
            });
        });
    }

    window.acknowledgeSOS = () => { alert("Rescue Unit assigned."); document.getElementById('emergency-dispatch-modal').classList.add('hidden'); }

    window.registerAmbulance = async function() {
        const dr = document.getElementById('amb-driver').value, v = document.getElementById('amb-vehicle').value, m = document.getElementById('amb-mobile').value, l = document.getElementById('amb-licence').value, loc = document.getElementById('amb-location').value, c = document.getElementById('amb-cert').value;
        if (!dr || !v || !m || !l || !loc || !c) { alert("Missing data points."); return; }
        try { await addDoc(collection(db, "artifacts", appId, "public", "data", "ambulances"), { dr, v, m, l, loc, c, timestamp: new Date().toISOString() }); alert("Added to Fleet Hub."); fetchAmbulanceFleet(); } catch (e) {}
    }

    async function fetchAmbulanceFleet() {
        try {
            const snap = await getDocs(collection(db, "artifacts", appId, "public", "data", "ambulances"));
            allAmbulances = snap.docs.map(d => ({ id: d.id, ...d.data() }));
            document.getElementById('admin-ambulance-list').innerHTML = allAmbulances.map((d, idx) => `
                <div onclick="showAmbulanceDetail(${idx})" class="card card-hover p-4 flex justify-between items-center">
                    <div><h4 class="font-display font-bold text-white text-sm">${d.v}</h4><p class="text-xs mt-0.5" style="color:#60a5fa;">${d.loc}</p></div>
                    <button onclick="event.stopPropagation(); deleteAmbulance('${d.id}')" class="h-8 w-8 rounded-xl flex items-center justify-center" style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.2);">
                        <i data-lucide="trash-2" class="w-4 h-4" style="color:#f87171;"></i>
                    </button>
                </div>`).join('');
            if (window.lucide) lucide.createIcons();
        } catch (e) {}
    }

    window.showAmbulanceDetail = function(idx) {
        const d = allAmbulances[idx]; if (!d) return;
        document.getElementById('ambulance-detail-content').innerHTML = `
            <div class="space-y-4 p-1">
                <div class="card p-5"><span class="field-label">Driver</span><p class="font-display font-bold text-white text-lg mt-1">${d.dr}</p></div>
                <div class="grid grid-cols-2 gap-3">
                    <div class="card p-4"><span class="field-label">Vehicle No</span><p class="font-display font-bold text-white mt-1">${d.v}</p></div>
                    <div class="card p-4"><span class="field-label">Cert No</span><p class="font-display font-bold text-white mt-1">${d.c}</p></div>
                </div>
                <div class="card p-4" style="background:rgba(59,130,246,0.06);border-color:rgba(59,130,246,0.2);"><span class="field-label" style="color:#60a5fa;">Mobile</span><p class="font-display font-semibold text-base mt-1" style="color:#93c5fd;">${d.m}</p></div>
                <div class="card p-4"><span class="field-label">Licence</span><p class="font-bold text-white mt-1">${d.l}</p></div>
                <div class="card p-4"><span class="field-label">Station</span><p class="font-bold text-white mt-1">${d.loc}</p></div>
            </div>`;
        document.getElementById('ambulance-detail-modal').classList.remove('hidden');
        if (window.lucide) lucide.createIcons();
    }

    window.deleteAmbulance = async (id) => { if (confirm("Remove from fleet?")) { await deleteDoc(doc(db, "artifacts", appId, "public", "data", "ambulances", id)); fetchAmbulanceFleet(); } }

    // ALARM
    let alarmAudioCtx = null, alarmNodes = [], vibrateInterval = null;
    function startAlarm() {
        try {
            alarmAudioCtx = new (window.AudioContext || window.webkitAudioContext)();
            function playAlarmCycle() {
                if (!alarmAudioCtx) return;
                const osc1 = alarmAudioCtx.createOscillator(), gainNode = alarmAudioCtx.createGain();
                osc1.type = 'sawtooth';
                osc1.frequency.setValueAtTime(880, alarmAudioCtx.currentTime);
                osc1.frequency.linearRampToValueAtTime(1760, alarmAudioCtx.currentTime + 0.4);
                gainNode.gain.setValueAtTime(0.6, alarmAudioCtx.currentTime);
                osc1.connect(gainNode); gainNode.connect(alarmAudioCtx.destination);
                osc1.start(); osc1.stop(alarmAudioCtx.currentTime + 0.85);
                alarmNodes.push(osc1, gainNode);
            }
            playAlarmCycle();
            window.alarmLoop = setInterval(playAlarmCycle, 900);
        } catch(e) {}
        if (navigator.vibrate) { navigator.vibrate([500,100,500,100,800,200]); vibrateInterval = setInterval(() => navigator.vibrate([500,100,500]), 2500); }
    }
    function stopAlarm() {
        if (window.alarmLoop) { clearInterval(window.alarmLoop); window.alarmLoop = null; }
        alarmNodes.forEach(n => { try { n.disconnect(); } catch(e){} });
        alarmNodes = [];
        if (alarmAudioCtx) { try { alarmAudioCtx.close(); } catch(e){} alarmAudioCtx = null; }
        if (vibrateInterval) { clearInterval(vibrateInterval); vibrateInterval = null; }
        if (navigator.vibrate) navigator.vibrate(0);
    }
    window.stopAlarmAndReset = () => { stopAlarm(); window.location.reload(); }

    async function fetchNearestAmbulance() {
        try {
            const snap = await getDocs(collection(db, "artifacts", appId, "public", "data", "ambulances"));
            const units = snap.docs.map(d => d.data());
            if (units.length === 0) { document.getElementById('sos-ambulance-driver').innerText = 'No units registered'; return; }
            const unit = units[0];
            document.getElementById('sos-ambulance-driver').innerText = unit.dr || 'Ambulance Unit';
            document.getElementById('sos-ambulance-vehicle').innerText = `Vehicle: ${unit.v || '--'} · ${unit.loc || ''}`;
            document.getElementById('sos-ambulance-number').innerText = unit.m || '--';
            const callBtn = document.getElementById('sos-call-ambulance');
            if (callBtn && unit.m) callBtn.href = `tel:${unit.m}`;
        } catch(e) {}
    }

    window.executeEmergencyProtocol = async () => {
        const p = window.currentPatientProfile;
        document.getElementById('sos-overlay').classList.add('hidden');
        document.getElementById('sos-contacts-view').classList.remove('hidden');
        document.getElementById('sos-display-contact').innerText = p.emergency || '--';
        const callContact = document.getElementById('sos-call-contact');
        if (callContact && p.emergency) callContact.href = `tel:${p.emergency}`;
        fetchNearestAmbulance();
        if (window.lucide) lucide.createIcons();
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(async (pos) => {
                const loc = `Lat: ${pos.coords.latitude.toFixed(5)}, Lng: ${pos.coords.longitude.toFixed(5)}`;
                await addDoc(collection(db, "artifacts", appId, "public", "data", "sos_signals"), { patientName: `${p.fname} ${p.lname}`, location: loc, timestamp: new Date().toISOString() });
            });
        }
    }

    window.startSimulation = () => {
        let bpm = 72;
        const intv = setInterval(() => {
            bpm += 20;
            const el = document.getElementById('bpm-display');
            el.innerText = bpm;
            el.style.color = bpm > 120 ? '#f87171' : bpm > 100 ? '#fbbf24' : 'white';
            if (bpm > 140) { clearInterval(intv); window.triggerSOSUI(); }
        }, 600);
    }

    window.triggerSOSUI = () => {
        document.getElementById('sos-overlay').classList.remove('hidden');
        startAlarm();
        let c = 10;
        const sInt = setInterval(() => {
            c--; document.getElementById('countdown-text').innerText = c;
            if (c <= 0) { clearInterval(sInt); executeEmergencyProtocol(); }
        }, 1000);
        window.sosCounter = sInt;
    }

    window.cancelSOS = () => {
        clearInterval(window.sosCounter);
        stopAlarm();
        document.getElementById('sos-overlay').classList.add('hidden');
        const el = document.getElementById('bpm-display');
        el.innerText = "72"; el.style.color = 'white';
    }

    // IMPACT DETECTION
    let impactActive = false, impactThreshold = 25, lastImpactTime = 0, impactSOSPending = false, impactCountdownTimer = null;
    const SENSITIVITY_MAP = { 1: { threshold: 40, label: 'Low', color: '#34d399' }, 2: { threshold: 25, label: 'Medium', color: '#fbbf24' }, 3: { threshold: 16, label: 'High', color: '#f87171' } };

    window.toggleImpactDetection = function() {
        if (!impactActive) {
            if (typeof DeviceMotionEvent !== 'undefined' && typeof DeviceMotionEvent.requestPermission === 'function') {
                DeviceMotionEvent.requestPermission().then(state => { if (state === 'granted') activateImpactDetection(); }).catch(() => {});
            } else { activateImpactDetection(); }
        } else { deactivateImpactDetection(); }
    }

    function activateImpactDetection() {
        impactActive = true;
        window.addEventListener('devicemotion', onDeviceMotion);
        const toggle = document.getElementById('impact-toggle'), dot = document.getElementById('impact-toggle-dot'), controls = document.getElementById('impact-controls');
        if (toggle) { toggle.style.background = 'rgba(245,158,11,0.3)'; toggle.style.borderColor = 'rgba(245,158,11,0.5)'; }
        if (dot) { dot.style.background = '#f59e0b'; dot.style.transform = 'translateX(24px)'; }
        if (controls) controls.classList.remove('hidden');
        showImpactStatus('Monitoring for impacts...', '#fbbf24', true);
    }

    function deactivateImpactDetection() {
        impactActive = false;
        window.removeEventListener('devicemotion', onDeviceMotion);
        const toggle = document.getElementById('impact-toggle'), dot = document.getElementById('impact-toggle-dot'), controls = document.getElementById('impact-controls');
        if (toggle) { toggle.style.background = 'rgba(255,255,255,0.1)'; toggle.style.borderColor = 'var(--border)'; }
        if (dot) { dot.style.background = 'var(--text-muted)'; dot.style.transform = 'translateX(0)'; }
        if (controls) controls.classList.add('hidden');
        showImpactStatus('Tap toggle to activate', 'var(--text-muted)', false);
    }

    function onDeviceMotion(event) {
        const acc = event.accelerationIncludingGravity; if (!acc) return;
        const magnitude = Math.sqrt((acc.x||0)**2 + (acc.y||0)**2 + (acc.z||0)**2);
        const gForce = (magnitude / 9.81).toFixed(1);
        const barEl = document.getElementById('gforce-bar'), gvalEl = document.getElementById('gforce-value');
        if (barEl) barEl.style.width = Math.min(100, (magnitude / 50) * 100) + '%';
        if (gvalEl) gvalEl.innerText = gForce + ' G';
        const now = Date.now();
        if (magnitude > impactThreshold && !impactSOSPending && (now - lastImpactTime) > 8000) { lastImpactTime = now; triggerImpactSOS(magnitude); }
    }

    function triggerImpactSOS(magnitude) {
        impactSOSPending = true;
        showImpactStatus(`Impact detected! ${(magnitude/9.81).toFixed(1)}G`, '#f87171', true);
        let countdown = 5;
        document.getElementById('sos-overlay').classList.remove('hidden');
        document.getElementById('countdown-text').innerText = countdown;
        startAlarm();
        impactCountdownTimer = setInterval(() => {
            countdown--;
            const el = document.getElementById('countdown-text');
            if (el) el.innerText = countdown;
            if (countdown <= 0) { clearInterval(impactCountdownTimer); impactSOSPending = false; executeEmergencyProtocol(); }
        }, 1000);
        window.sosCounter = impactCountdownTimer;
    }

    window.updateSensitivity = function(val) {
        const cfg = SENSITIVITY_MAP[val]; impactThreshold = cfg.threshold;
        const label = document.getElementById('sensitivity-label');
        if (label) { label.innerText = cfg.label; label.style.color = cfg.color; }
    }

    function showImpactStatus(text, color, active) {
        const dot = document.getElementById('impact-status-dot'), txt = document.getElementById('impact-status-text');
        if (dot) { dot.style.background = color; dot.style.boxShadow = active ? `0 0 6px ${color}` : 'none'; }
        if (txt) { txt.innerText = text; txt.style.color = color; }
    }

    // HEALTHBOT - GEMINI
    let botHistory = [];
    const BOT_SYSTEM = `You are LifeGuard Health AI, a compassionate medical assistant. Help users with:
1. Minor disease symptoms (cold, flu, headache, fever, stomach ache, rashes, etc.)
2. General health questions
3. Doctor appointment booking - collect: name, preferred date, reason, doctor type
Keep responses concise for mobile. For emergencies (chest pain, stroke, severe bleeding) say: Use the SOS button immediately. You are an AI assistant, not a licensed doctor.`;

    window.openHealthBot = function() {
        document.getElementById('healthbot-modal').classList.remove('hidden');
        if (window.lucide) lucide.createIcons();
        if (botHistory.length === 0) {
            const name = window.currentPatientProfile ? window.currentPatientProfile.fname : 'there';
            addBotMessage(`Hi ${name}! I am your LifeGuard Health AI powered by Gemini.\\n\\nI can help with:\\n- Minor symptoms and advice\\n- General health questions\\n- Booking appointments\\n\\nHow can I help you?`, 'bot');
        }
        setTimeout(() => { const m = document.getElementById('bot-messages'); if (m) m.scrollTop = m.scrollHeight; }, 100);
    }

    window.closeHealthBot = () => document.getElementById('healthbot-modal').classList.add('hidden');

    window.clearChat = function() {
        botHistory = [];
        document.getElementById('bot-messages').innerHTML = '';
        window.openHealthBot();
    }

    window.sendQuickMessage = function(text) {
        document.getElementById('bot-input').value = text;
        sendBotMessage();
    }

    window.sendBotMessage = async function() {
        const input = document.getElementById('bot-input');
        const text = input.value.trim();
        if (!text) return;
        input.value = ''; input.style.height = 'auto';
        addBotMessage(text, 'user');
        botHistory.push({ role: 'user', content: text });
        document.getElementById('bot-typing').classList.remove('hidden');
        scrollBotToBottom();
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ system: BOT_SYSTEM, messages: botHistory })
            });
            const data = await response.json();
            const reply = data.content?.[0]?.text || "Sorry, I could not process that. Please try again.";
            botHistory.push({ role: 'model', content: reply });
            document.getElementById('bot-typing').classList.add('hidden');
            addBotMessage(reply, 'bot');
        } catch(e) {
            document.getElementById('bot-typing').classList.add('hidden');
            addBotMessage("Unable to connect. Please check your internet and try again.", 'bot');
        }
        scrollBotToBottom();
    }

    function addBotMessage(text, role) {
        const container = document.getElementById('bot-messages');
        const isBot = role === 'bot';
        const div = document.createElement('div');
        div.className = 'flex gap-2 ' + (isBot ? 'items-start' : 'items-start justify-end');
        const formatted = text
            .replace(/[*][*](.*?)[*][*]/g, '<strong>$1</strong>')
            .replace(/[*](.*?)[*]/g, '<em>$1</em>')
            .replace(/\\n/g, '<br>');
        if (isBot) {
            div.innerHTML = `
                <div class="h-7 w-7 rounded-full flex items-center justify-center shrink-0 mt-1" style="background:rgba(16,185,129,0.15);border:1px solid rgba(16,185,129,0.25);">
                    <i data-lucide="bot" class="w-3.5 h-3.5" style="color:#34d399;"></i>
                </div>
                <div class="max-w-xs rounded-2xl rounded-tl-sm px-4 py-3 text-sm leading-relaxed" style="background:var(--bg-card);border:1px solid var(--border);color:var(--text-primary);">${formatted}</div>`;
        } else {
            div.innerHTML = `<div class="max-w-xs rounded-2xl rounded-tr-sm px-4 py-3 text-sm leading-relaxed text-white" style="background:linear-gradient(135deg,#10b981,#059669);">${formatted}</div>`;
        }
        container.appendChild(div);
        if (window.lucide) lucide.createIcons();
        scrollBotToBottom();
    }

    function scrollBotToBottom() {
        const msgs = document.getElementById('bot-messages');
        if (msgs) setTimeout(() => msgs.scrollTop = msgs.scrollHeight, 50);
    }

    window.postBloodRequest = async function() {
        const h = document.getElementById('req-hosp-name').value, b = document.getElementById('req-blood').value, u = document.getElementById('req-units').value, r = document.getElementById('req-reason').value;
        if (!h || !u || !r) return;
        try { await addDoc(collection(db, "artifacts", appId, "public", "data", "blood_requests"), { hospital: h, hospitalUid: auth.currentUser?.uid, blood: b, units: u, reason: r, timestamp: new Date().toISOString() }); alert("Signal dispatched."); fetchHospitalMyRequests(); } catch (e) {}
    }

    async function fetchHospitalMyRequests() {
        if (!auth.currentUser) return;
        try {
            const snap = await getDocs(collection(db, "artifacts", appId, "public", "data", "blood_requests"));
            const myReqs = snap.docs.map(d => ({ id: d.id, ...d.data() })).filter(req => req.hospitalUid === auth.currentUser.uid);
            document.getElementById('hospital-my-requests-list').innerHTML = myReqs.length === 0 ?
                `<p class="text-xs italic" style="color:var(--text-muted);">No active signals.</p>` :
                myReqs.map(req => `<div class="flex justify-between items-center py-2 px-3 rounded-xl" style="background:var(--bg-elevated);border:1px solid var(--border);">
                    <div class="flex items-center gap-2"><span class="badge badge-red text-xs">${req.blood}</span><span class="text-xs" style="color:var(--text-secondary);">${req.reason.substring(0,18)}...</span></div>
                    <button onclick="deleteBloodRequest('${req.id}')" class="h-7 w-7 rounded-lg flex items-center justify-center" style="background:rgba(239,68,68,0.1);"><i data-lucide="trash-2" class="w-3 h-3" style="color:#f87171;"></i></button>
                </div>`).join('');
            if (window.lucide) lucide.createIcons();
        } catch (e) {}
    }

    window.deleteBloodRequest = async (id) => { if (confirm("End signal?")) { await deleteDoc(doc(db, "artifacts", appId, "public", "data", "blood_requests", id)); fetchHospitalMyRequests(); } }

    window.fetchEmergencyRequests = async function() {
        try {
            const snap = await getDocs(collection(db, "artifacts", appId, "public", "data", "blood_requests"));
            const reqs = snap.docs.map(d => d.data()).sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
            document.getElementById('donator-emergency-list').innerHTML = reqs.length === 0 ?
                `<div class="flex flex-col items-center justify-center h-full py-20"><p class="text-sm" style="color:var(--text-muted);">No active signals</p></div>` :
                reqs.map(req => `<div class="card p-4" style="border-left:3px solid #ef4444;">
                    <div class="flex justify-between items-start mb-3">
                        <div><h3 class="font-display font-bold text-white text-sm">${req.hospital}</h3><p class="text-xs mt-1 font-semibold uppercase" style="color:#f87171;">${req.reason}</p></div>
                        <span class="badge badge-red text-base font-extrabold">${req.blood}</span>
                    </div>
                    <button onclick="alert('Response sent to ${req.hospital}')" class="btn-danger" style="padding:10px;font-size:13px;">I Can Donate Now</button>
                </div>`).join('');
            if (window.lucide) lucide.createIcons();
        } catch (e) {}
    }

    async function fetchDonors() {
        try { const snap = await getDocs(collection(db, "artifacts", appId, "public", "data", "donators")); allDonors = snap.docs.map(d => d.data()); renderDonorList(allDonors); } catch (e) {}
    }

    function renderDonorList(data) {
        const list = document.getElementById('hospital-donor-list');
        if (data.length === 0) { list.innerHTML = `<p class="text-center py-10 text-sm" style="color:var(--text-muted);">No matches found.</p>`; return; }
        list.innerHTML = data.map((donor, idx) => `
            <div onclick="showDonorFullProfile(${idx})" class="card card-hover p-4 flex items-center gap-3">
                <div class="h-10 w-10 rounded-2xl flex items-center justify-center shrink-0" style="background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.2);">
                    <i data-lucide="user" class="w-5 h-5" style="color:#34d399;"></i>
                </div>
                <div class="flex-1 min-w-0"><h3 class="font-display font-bold text-white text-sm">${donor.name || 'Donor'}</h3><p class="text-xs mt-0.5 truncate" style="color:var(--text-muted);">${donor.address || 'N/A'}</p></div>
                <span class="badge badge-red">${donor.blood || '--'}</span>
            </div>`).join('');
        if (window.lucide) lucide.createIcons();
    }

    window.showDonorFullProfile = function(idx) {
        const d = allDonors[idx]; if (!d) return;
        document.getElementById('full-donor-content').innerHTML = `
            <div class="text-center py-4">
                <div class="h-16 w-16 rounded-2xl flex items-center justify-center mx-auto mb-4" style="background:rgba(16,185,129,0.15);border:1px solid rgba(16,185,129,0.3);">
                    <i data-lucide="user" class="w-8 h-8" style="color:#34d399;"></i>
                </div>
                <h1 class="font-display text-xl font-bold text-white mb-3">${d.name || 'Donor'}</h1>
                <span class="badge badge-red text-sm">${d.blood || '--'}</span>
            </div>
            <div class="divider"></div>
            <div class="grid grid-cols-2 gap-3">
                <div class="card p-4 text-center"><span class="field-label">Age</span><p class="font-display font-bold text-white mt-1">${d.age || '--'}</p></div>
                <div class="card p-4 text-center"><span class="field-label">D.O.B</span><p class="font-bold text-white text-sm mt-1">${d.dob || '--'}</p></div>
            </div>
            <div class="card p-4" style="background:rgba(59,130,246,0.06);border-color:rgba(59,130,246,0.2);">
                <span class="field-label" style="color:#60a5fa;">Contact</span>
                <p class="font-display font-semibold text-base mt-1" style="color:#93c5fd;">${d.mobile || '--'}</p>
            </div>
            <div class="card p-4"><span class="field-label">Location</span><p class="text-sm mt-1" style="color:var(--text-secondary);">${d.address || '--'}</p></div>`;
        document.getElementById('full-donor-modal').classList.remove('hidden');
        if (window.lucide) lucide.createIcons();
    }

    window.applyDonorFilters = function() {
        const nS = document.getElementById('filter-name').value.toLowerCase().trim();
        const cS = document.getElementById('filter-city').value.toLowerCase().trim();
        const bS = document.getElementById('filter-blood-reg').value;
        const dS = document.getElementById('filter-dob-reg').value;
        renderDonorList(allDonors.filter(d => (!nS || (d.name||"").toLowerCase().includes(nS)) && (!cS || (d.address||"").toLowerCase().includes(cS)) && (!bS || d.blood === bS) && (!dS || d.dob === dS)));
    }

    window.logout = () => signOut(auth).then(() => window.location.reload());
    window.adminLogin = () => { const u = document.getElementById('admin-user').value, p = document.getElementById('admin-pass').value; if (u === 'superadmin' && p === 'lifeguard2026') switchView('view-admin-dashboard'); else alert("Invalid credentials."); }

    window.generateOTP = async function() {
        const email = window.pendingVerificationData?.email || document.getElementById('pat-email').value;
        const otp = Math.floor(1000 + Math.random() * 9000).toString();
        window.genOTP = otp;
        document.getElementById('display-pat-email').innerText = email;
        switchView('view-patient-otp');
        try { await fetch('/send-verification-email', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email, otp }) }); } catch (e) {}
        alert("Your verification code: " + otp);
    }

    window.verifyOTP = async () => {
        const entered = document.getElementById('otp-1').value + document.getElementById('otp-2').value + document.getElementById('otp-3').value + document.getElementById('otp-4').value;
        if (entered === window.genOTP) {
            const { role, uid, data } = window.pendingVerificationData;
            if (role === 'donator') await setDoc(doc(db, "artifacts", appId, "public", "data", "donators", uid), data);
            window.currentPatientProfile = data;
            switchView(role === 'donator' ? 'view-donator-dashboard' : 'view-patient-dashboard');
        } else alert("Incorrect code. Please try again.");
    }

    document.addEventListener("DOMContentLoaded", () => {
        const codes = [{ c: "+91", f: "IN" }, { c: "+1", f: "US" }, { c: "+44", f: "UK" }];
        document.querySelectorAll('.country-code-select').forEach(s => codes.forEach(ct => {
            const o = document.createElement('option'); o.value = ct.c; o.textContent = `${ct.f} ${ct.c}`; s.appendChild(o);
        }));
        [1,2,3,4].forEach(n => {
            const input = document.getElementById('otp-' + n);
            if (input) {
                input.oninput = function() {
                    if (this.value.length == 1 && n < 4) document.getElementById('otp-' + (n+1)).focus();
                    this.style.borderColor = this.value ? '#3b82f6' : 'var(--border)';
                };
            }
        });
        if (window.lucide) lucide.createIcons();
    });

    setTimeout(() => { if (window.lucide) lucide.createIcons(); }, 500);
</script>

<script>
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => navigator.serviceWorker.register('/sw.js').catch(() => {}));
    }
</script>
</body>
</html>
"""

@app.get("/")
async def get_app():
    return HTMLResponse(content=html_content)

@app.get("/manifest.json")
async def get_manifest():
    manifest = {
        "name": "LifeGuard Emergency Network",
        "short_name": "LifeGuard",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#080c14",
        "theme_color": "#080c14",
        "icons": [
            {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"}
        ]
    }
    return JSONResponse(content=manifest)

SW_CONTENT = """
const CACHE_NAME = 'lifeguard-v2';
self.addEventListener('install', e => { self.skipWaiting(); });
self.addEventListener('activate', e => { self.clients.claim(); });
self.addEventListener('fetch', e => {
    if (e.request.url.includes('firebase') || e.request.url.includes('googleapis') || e.request.url.includes('/api/') || e.request.url.includes('/send-verification')) return;
    e.respondWith(fetch(e.request).catch(() => caches.match('/')));
});
"""

@app.get("/sw.js")
async def get_service_worker():
    return Response(content=SW_CONTENT, media_type="application/javascript", headers={"Cache-Control": "no-cache", "Service-Worker-Allowed": "/"})

def generate_icon_svg(size):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}"><rect width="{size}" height="{size}" rx="{int(size*0.22)}" fill="#1d4ed8"/><polyline points="{size*0.28},{size*0.52} {size*0.36},{size*0.52} {size*0.40},{size*0.38} {size*0.44},{size*0.66} {size*0.48},{size*0.44} {size*0.52},{size*0.58} {size*0.56},{size*0.52} {size*0.72},{size*0.52}" fill="none" stroke="white" stroke-width="{max(1.5,size*0.025)}" stroke-linecap="round" stroke-linejoin="round"/></svg>'

@app.get("/icon-192.png")
async def icon192():
    return Response(content=generate_icon_svg(192), media_type="image/svg+xml")

@app.get("/icon-512.png")
async def icon512():
    return Response(content=generate_icon_svg(512), media_type="image/svg+xml")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
