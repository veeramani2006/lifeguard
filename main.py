from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
import uvicorn
import smtplib
import logging
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google import genai
from dotenv import load_dotenv

load_dotenv()

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

# =============================================
# CONFIG — loaded from environment variables
# =============================================
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
SMTP_SERVER    = "smtp.gmail.com"
SMTP_PORT      = 587
SENDER_EMAIL   = os.environ["SENDER_EMAIL"]
SENDER_PASSWORD = os.environ["SENDER_PASSWORD"]

client = genai.Client(api_key=GEMINI_API_KEY)


class EmailVerificationRequest(BaseModel):
    email: str
    otp: str

    @field_validator("email")
    @classmethod
    def email_valid(cls, v):
        if "@" not in v or len(v) > 200:
            raise ValueError("Invalid email")
        return v.strip().lower()

    @field_validator("otp")
    @classmethod
    def otp_valid(cls, v):
        if not v.isdigit() or len(v) != 4:
            raise ValueError("OTP must be 4 digits")
        return v


class ChatMessage(BaseModel):
    role: str
    content: str

    @field_validator("content")
    @classmethod
    def content_length(cls, v):
        if len(v) > 4000:
            raise ValueError("Message too long")
        return v


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    system: str = ""

    @field_validator("messages")
    @classmethod
    def messages_limit(cls, v):
        if len(v) > 50:
            raise ValueError("Too many messages")
        return v


@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        formatted_history = []
        for msg in request.messages[:-1]:
            formatted_history.append({
                "role": "user" if msg.role == "user" else "model",
                "parts": [{"text": msg.content}]
            })

        chat_session = client.chats.create(
            model="gemini-2.5-flash",
            config={"system_instruction": request.system or "You are a helpful health assistant."},
            history=formatted_history
        )

        last_message = request.messages[-1].content
        response = chat_session.send_message(last_message)

        return {"content": [{"type": "text", "text": response.text}]}

    except Exception as e:
        logger.error(f"Gemini API Error: {str(e)}")
        raise HTTPException(status_code=500, detail="AI service unavailable")


@app.post("/send-verification-email")
async def send_verification_email(request: EmailVerificationRequest):
    try:
        msg = MIMEMultipart()
        msg["From"]    = f"LifeGuard Support <{SENDER_EMAIL}>"
        msg["To"]      = request.email
        msg["Subject"] = "LifeGuard Account Activation Code"

        body = f"""
        <html>
          <body style="font-family:'Segoe UI',sans-serif;background:#0f172a;padding:40px 20px;margin:0;">
            <div style="max-width:480px;margin:auto;background:#1e293b;border-radius:24px;padding:40px;border:1px solid rgba(99,179,237,0.2);">
              <div style="text-align:center;margin-bottom:32px;">
                <h2 style="color:#60a5fa;font-size:22px;font-weight:900;margin:0;">LifeGuard Verification</h2>
                <p style="color:#94a3b8;font-size:13px;margin-top:8px;">Enter this code to activate your account</p>
              </div>
              <div style="background:rgba(59,130,246,0.1);border:2px dashed rgba(59,130,246,0.4);border-radius:16px;padding:32px;text-align:center;margin:24px 0;">
                <div style="font-size:48px;font-weight:900;letter-spacing:16px;color:#93c5fd;font-family:monospace;">{request.otp}</div>
              </div>
              <p style="font-size:11px;color:#64748b;text-align:center;margin-top:20px;">Valid for 10 minutes · Do not share this code</p>
            </div>
          </body>
        </html>
        """
        msg.attach(MIMEText(body, "html"))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=20)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()

        return {"status": "success"}

    except Exception as e:
        logger.error(f"Mail Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Email service unavailable")


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
