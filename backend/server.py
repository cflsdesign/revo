from dotenv import load_dotenv
load_dotenv()

import os
import csv
import io
import jwt
import bcrypt
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from fastapi import FastAPI, APIRouter, HTTPException, Request, Depends, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# ─── Config ───
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]
JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGORITHM = "HS256"
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@revo.mx")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Revo2026")
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "")
NOTIFY_EMAIL = os.environ.get("NOTIFY_EMAIL", "")
REPORT_PDF_PATH = os.environ.get("REPORT_PDF_PATH", "/app/Sayulita_2026_Revo_Mexico.pdf")

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

app = FastAPI(title="Revo México · Leads API")
api = APIRouter(prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer(auto_error=False)


# ─── Helpers ───
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def create_access_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "type": "access",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_admin(creds: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> dict:
    if creds is None or not creds.credentials:
        raise HTTPException(status_code=401, detail="No autenticado")
    token = creds.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Sesión expirada")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")
    user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return {"id": str(user["_id"]), "email": user["email"], "name": user.get("name", "Admin")}


def send_lead_notification(lead: dict):
    """Send admin notification via SendGrid. Skips silently if not configured."""
    if not SENDGRID_API_KEY or not SENDER_EMAIL or not NOTIFY_EMAIL:
        print("[email] SendGrid no configurado, se omite el envío. Lead guardado igualmente.")
        return
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail

        utm = lead.get("utm", {}) or {}
        rows = "".join(
            f"<tr><td style='padding:6px 14px;color:#888;font-size:13px'>{k}</td>"
            f"<td style='padding:6px 14px;color:#fff;font-size:13px'><strong>{v or '—'}</strong></td></tr>"
            for k, v in [
                ("Nombre", lead.get("name")),
                ("Correo", lead.get("email")),
                ("Teléfono", lead.get("phone")),
                ("Fecha", lead.get("created_at")),
                ("Campaña", utm.get("utm_campaign")),
                ("Fuente", utm.get("utm_source")),
                ("Medio", utm.get("utm_medium")),
                ("Referrer", lead.get("referrer")),
            ]
        )
        html = f"""
        <div style="background:#000;padding:32px;font-family:Arial,sans-serif">
          <h2 style="color:#34D4E7;margin:0 0 4px">Nuevo lead · Revo México</h2>
          <p style="color:#aaa;margin:0 0 20px">Alguien acaba de descargar el análisis Sayulita 2026.</p>
          <table style="border-collapse:collapse;background:#111;border:1px solid #2a2a2a">{rows}</table>
        </div>"""
        message = Mail(
            from_email=SENDER_EMAIL,
            to_emails=NOTIFY_EMAIL,
            subject=f"🔔 Nuevo lead: {lead.get('name')} ({lead.get('email')})",
            html_content=html,
        )
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
        print(f"[email] Notificación enviada a {NOTIFY_EMAIL}")
    except Exception as e:
        print(f"[email] Error enviando notificación: {e}")


# ─── Models ───
class UTM(BaseModel):
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_term: Optional[str] = None
    utm_content: Optional[str] = None


class LeadCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    email: EmailStr
    phone: Optional[str] = Field(default=None, max_length=40)
    utm: Optional[UTM] = None
    referrer: Optional[str] = None
    page_url: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


def lead_to_dict(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "name": doc.get("name"),
        "email": doc.get("email"),
        "phone": doc.get("phone"),
        "utm": doc.get("utm", {}),
        "referrer": doc.get("referrer"),
        "page_url": doc.get("page_url"),
        "ip": doc.get("ip"),
        "user_agent": doc.get("user_agent"),
        "created_at": doc.get("created_at"),
    }


# ─── Public endpoints ───
@api.get("/health")
async def health():
    return {"status": "ok", "email_configured": bool(SENDGRID_API_KEY and SENDER_EMAIL)}


@api.post("/leads")
async def create_lead(payload: LeadCreate, request: Request, background_tasks: BackgroundTasks):
    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "")
    if ip and "," in ip:
        ip = ip.split(",")[0].strip()
    doc = {
        "name": payload.name.strip(),
        "email": payload.email.lower().strip(),
        "phone": (payload.phone or "").strip() or None,
        "utm": payload.utm.model_dump() if payload.utm else {},
        "referrer": payload.referrer,
        "page_url": payload.page_url,
        "ip": ip,
        "user_agent": request.headers.get("user-agent", ""),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    result = await db.leads.insert_one(doc)
    doc["_id"] = result.inserted_id
    background_tasks.add_task(send_lead_notification, lead_to_dict(doc))
    return {"success": True, "download_url": "/api/download/report"}


@api.get("/download/report")
async def download_report():
    if not os.path.exists(REPORT_PDF_PATH):
        raise HTTPException(status_code=404, detail="Reporte no disponible")
    return FileResponse(
        REPORT_PDF_PATH,
        media_type="application/pdf",
        filename="Sayulita_2026_Revo_Mexico.pdf",
    )


# ─── Auth ───
@api.post("/auth/login")
async def login(payload: LoginRequest):
    user = await db.users.find_one({"email": payload.email.lower().strip()})
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    token = create_access_token(str(user["_id"]), user["email"])
    return {"token": token, "user": {"email": user["email"], "name": user.get("name", "Admin")}}


@api.get("/auth/me")
async def me(admin: dict = Depends(get_current_admin)):
    return admin


# ─── Admin: leads ───
@api.get("/leads")
async def list_leads(
    admin: dict = Depends(get_current_admin),
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
):
    query = {}
    if search:
        query = {
            "$or": [
                {"name": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}},
                {"phone": {"$regex": search, "$options": "i"}},
            ]
        }
    total = await db.leads.count_documents(query)
    cursor = db.leads.find(query).sort("created_at", -1).skip(skip).limit(min(limit, 200))
    items = [lead_to_dict(d) async for d in cursor]
    return {"total": total, "items": items}


@api.get("/leads/stats")
async def lead_stats(admin: dict = Depends(get_current_admin)):
    total = await db.leads.count_documents({})
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    week_start = (now - timedelta(days=7)).isoformat()
    today = await db.leads.count_documents({"created_at": {"$gte": today_start}})
    week = await db.leads.count_documents({"created_at": {"$gte": week_start}})
    with_phone = await db.leads.count_documents({"phone": {"$nin": [None, ""]}})
    return {"total": total, "today": today, "week": week, "with_phone": with_phone}


@api.delete("/leads/{lead_id}")
async def delete_lead(lead_id: str, admin: dict = Depends(get_current_admin)):
    try:
        oid = ObjectId(lead_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID inválido")
    res = await db.leads.delete_one({"_id": oid})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Lead no encontrado")
    return {"success": True}


@api.get("/leads/export")
async def export_leads(token: str = Query(...)):
    # token passed as query param so the browser can download directly
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="No autorizado")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "Nombre", "Correo", "Telefono", "Fecha",
        "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
        "referrer", "page_url", "ip",
    ])
    cursor = db.leads.find({}).sort("created_at", -1)
    async for d in cursor:
        utm = d.get("utm", {}) or {}
        writer.writerow([
            d.get("name", ""), d.get("email", ""), d.get("phone", "") or "", d.get("created_at", ""),
            utm.get("utm_source", "") or "", utm.get("utm_medium", "") or "",
            utm.get("utm_campaign", "") or "", utm.get("utm_term", "") or "",
            utm.get("utm_content", "") or "", d.get("referrer", "") or "",
            d.get("page_url", "") or "", d.get("ip", "") or "",
        ])
    buf.seek(0)
    filename = f"revo_leads_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


app.include_router(api)


@app.on_event("startup")
async def startup():
    await db.users.create_index("email", unique=True)
    await db.leads.create_index("created_at")
    await db.leads.create_index("email")
    existing = await db.users.find_one({"email": ADMIN_EMAIL.lower()})
    if existing is None:
        await db.users.insert_one({
            "email": ADMIN_EMAIL.lower(),
            "password_hash": hash_password(ADMIN_PASSWORD),
            "name": "Admin Revo",
            "role": "admin",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        print(f"[seed] Admin creado: {ADMIN_EMAIL}")
    elif not verify_password(ADMIN_PASSWORD, existing["password_hash"]):
        await db.users.update_one(
            {"email": ADMIN_EMAIL.lower()},
            {"$set": {"password_hash": hash_password(ADMIN_PASSWORD)}},
        )
        print("[seed] Contraseña de admin actualizada")
