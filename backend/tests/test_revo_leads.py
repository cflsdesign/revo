"""Pytest regression suite for Revo México leads backend.

Covers:
- Health
- Public POST /api/leads (with UTM, validation)
- Public GET /api/download/report (PDF)
- Auth login (success + wrong creds)
- Admin protected endpoints (401 without token)
- Admin GET /api/leads, /api/leads/stats, DELETE /api/leads/{id}
- CSV export with token query param
"""

import os
import io
import csv
import uuid
import pytest
import requests
from dotenv import load_dotenv

load_dotenv("/app/frontend/.env")
BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "admin@revo.mx"
ADMIN_PASSWORD = "Revo2026"


# ─── Fixtures ───
@pytest.fixture(scope="session")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="session")
def admin_token(session):
    r = session.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    data = r.json()
    assert "token" in data and isinstance(data["token"], str) and len(data["token"]) > 20
    return data["token"]


@pytest.fixture
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


# ─── Health ───
def test_health(session):
    r = session.get(f"{API}/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "email_configured" in body
    # SendGrid not configured by design
    assert body["email_configured"] is False


# ─── Public: create lead ───
def test_create_lead_minimal(session):
    payload = {
        "name": f"TEST Lead {uuid.uuid4().hex[:6]}",
        "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
        "phone": "+52 322 000 0000",
    }
    r = session.post(f"{API}/leads", json=payload)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("success") is True
    assert body.get("download_url") == "/api/download/report"


def test_create_lead_with_utm_persists(session, auth_headers):
    email = f"test_utm_{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "name": "TEST UTM Lead",
        "email": email,
        "phone": "+52 333 111 2222",
        "utm": {
            "utm_source": "facebook",
            "utm_medium": "cpc",
            "utm_campaign": "sayulita2026",
            "utm_term": "real-estate",
            "utm_content": "hero",
        },
        "referrer": "https://t.co/abc",
        "page_url": "https://revo.mx/?utm_source=facebook",
    }
    r = session.post(f"{API}/leads", json=payload)
    assert r.status_code == 200, r.text

    # Verify persistence via admin list (search by email)
    g = requests.get(f"{API}/leads", headers=auth_headers, params={"search": email})
    assert g.status_code == 200
    data = g.json()
    assert data["total"] >= 1
    found = next((it for it in data["items"] if it["email"] == email), None)
    assert found is not None, "Lead not persisted"
    assert found["name"] == "TEST UTM Lead"
    assert found["phone"] == "+52 333 111 2222"
    assert found["utm"]["utm_source"] == "facebook"
    assert found["utm"]["utm_campaign"] == "sayulita2026"
    assert found["referrer"] == "https://t.co/abc"
    assert found["page_url"].startswith("https://revo.mx/")
    assert found["created_at"]


def test_create_lead_invalid_email(session):
    r = session.post(f"{API}/leads", json={"name": "TEST x", "email": "not-an-email"})
    assert r.status_code == 422


def test_create_lead_empty_name(session):
    r = session.post(f"{API}/leads", json={"name": "", "email": "ok@example.com"})
    assert r.status_code == 422


# ─── Public: PDF download ───
def test_download_report_pdf(session):
    r = session.get(f"{API}/download/report")
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("application/pdf")
    assert r.content[:4] == b"%PDF"
    assert len(r.content) > 1000


# ─── Auth ───
def test_login_wrong_password(session):
    r = session.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": "wrong"})
    assert r.status_code == 401


def test_login_unknown_user(session):
    r = session.post(f"{API}/auth/login", json={"email": "nobody@example.com", "password": "x"})
    assert r.status_code == 401


def test_auth_me(admin_token):
    r = requests.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    assert r.json()["email"] == ADMIN_EMAIL


# ─── Admin endpoints reject unauthenticated ───
@pytest.mark.parametrize("method,path", [
    ("GET", "/leads"),
    ("GET", "/leads/stats"),
    ("DELETE", "/leads/000000000000000000000000"),
])
def test_admin_endpoints_require_auth(method, path):
    r = requests.request(method, f"{API}{path}")
    assert r.status_code == 401, f"{method} {path} -> {r.status_code}"


def test_admin_endpoints_reject_bad_token():
    r = requests.get(f"{API}/leads", headers={"Authorization": "Bearer not.a.real.jwt"})
    assert r.status_code == 401


# ─── Admin: stats & list ───
def test_stats(auth_headers):
    r = requests.get(f"{API}/leads/stats", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    for k in ("total", "today", "week", "with_phone"):
        assert k in data
        assert isinstance(data[k], int)


def test_list_leads(auth_headers):
    r = requests.get(f"{API}/leads", headers=auth_headers, params={"limit": 50})
    assert r.status_code == 200
    data = r.json()
    assert "items" in data and "total" in data
    assert isinstance(data["items"], list)
    if data["items"]:
        first = data["items"][0]
        for k in ("id", "name", "email", "created_at"):
            assert k in first
        assert "_id" not in first


def test_search_leads(auth_headers, session):
    email = f"test_search_{uuid.uuid4().hex[:8]}@example.com"
    session.post(f"{API}/leads", json={"name": "TEST Search User", "email": email})
    r = requests.get(f"{API}/leads", headers=auth_headers, params={"search": "TEST Search User"})
    assert r.status_code == 200
    assert any(it["email"] == email for it in r.json()["items"])


# ─── Admin: delete ───
def test_delete_lead_flow(auth_headers, session):
    email = f"test_del_{uuid.uuid4().hex[:8]}@example.com"
    session.post(f"{API}/leads", json={"name": "TEST Delete", "email": email})
    listing = requests.get(f"{API}/leads", headers=auth_headers, params={"search": email}).json()
    lead = next(it for it in listing["items"] if it["email"] == email)

    d = requests.delete(f"{API}/leads/{lead['id']}", headers=auth_headers)
    assert d.status_code == 200
    assert d.json().get("success") is True

    # Verify gone
    listing2 = requests.get(f"{API}/leads", headers=auth_headers, params={"search": email}).json()
    assert not any(it["email"] == email for it in listing2["items"])


def test_delete_invalid_id(auth_headers):
    r = requests.delete(f"{API}/leads/not-an-objectid", headers=auth_headers)
    assert r.status_code == 400


def test_delete_missing_lead(auth_headers):
    r = requests.delete(f"{API}/leads/000000000000000000000000", headers=auth_headers)
    assert r.status_code == 404


# ─── CSV export ───
def test_csv_export(admin_token, session):
    # Create a known lead first
    email = f"test_csv_{uuid.uuid4().hex[:8]}@example.com"
    session.post(f"{API}/leads", json={
        "name": "TEST CSV Lead",
        "email": email,
        "phone": "+52 999 888 7777",
        "utm": {"utm_source": "google", "utm_campaign": "csv-test"},
    })

    r = requests.get(f"{API}/leads/export", params={"token": admin_token})
    assert r.status_code == 200
    assert "text/csv" in r.headers.get("content-type", "")
    assert "attachment" in r.headers.get("content-disposition", "")

    reader = csv.reader(io.StringIO(r.text))
    rows = list(reader)
    header = rows[0]
    for col in ("Nombre", "Correo", "Telefono", "Fecha",
                "utm_source", "utm_medium", "utm_campaign"):
        assert col in header

    # Verify our lead is present with utm values
    matching = [row for row in rows[1:] if email in row]
    assert matching, "CSV missing our test lead"
    row = matching[0]
    src_idx = header.index("utm_source")
    camp_idx = header.index("utm_campaign")
    assert row[src_idx] == "google"
    assert row[camp_idx] == "csv-test"


def test_csv_export_bad_token():
    r = requests.get(f"{API}/leads/export", params={"token": "bad"})
    assert r.status_code == 401
