# Test Credentials — Revo México Leads

## Admin Panel (login at /admin/login)
- Email: admin@revo.mx
- Password: Revo2026
- Role: admin

Configured via backend/.env (ADMIN_EMAIL / ADMIN_PASSWORD). Admin is seeded on backend startup.

## Auth endpoints
- POST /api/auth/login  -> returns { token, user }
- GET  /api/auth/me     (Bearer token)

## Leads endpoints
- POST   /api/leads            (public)
- GET    /api/download/report  (public, serves the PDF)
- GET    /api/leads            (admin)
- GET    /api/leads/stats      (admin)
- DELETE /api/leads/{id}       (admin)
- GET    /api/leads/export?token=JWT  (CSV download)

Auth uses JWT Bearer token stored in localStorage (key: revo_token).
