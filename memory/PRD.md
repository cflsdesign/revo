# PRD — Revo México · Repositorio de Leads (Sayulita 2026)

## Original Problem Statement
Revisar la landing https://cflsdesign.github.io/revo/ y crear el código para un repositorio de los datos de las personas que se registran para descargar el PDF.

## User Choices
- Recrear landing completa + formulario funcional + repositorio + panel admin (todo en uno).
- Capturar: Nombre, Correo, Teléfono + fecha/hora + origen (UTM/campaña).
- Notificación por correo (SendGrid) a cflsdesign@gmail.com por cada nuevo lead.
- Panel admin con login/contraseña (admin@revo.mx / Revo2026).
- Exportación de leads a CSV.

## Architecture
- Backend: FastAPI (/app/backend/server.py), MongoDB (Motor), JWT auth (PyJWT + bcrypt), SendGrid.
- Frontend: React (CRA) + React Router. Landing fiel al original (tema negro/turquesa, fuente Reddit Sans).
- PDF servido por backend en /api/download/report (archivo /app/Sayulita_2026_Revo_Mexico.pdf).

## Implemented (2026-06-25)
- Landing recreada con campo extra Teléfono; captura UTM, referrer, page_url, IP, user-agent.
- POST /api/leads guarda lead y dispara notificación (background) por SendGrid.
- Panel admin: login JWT, stats (total/hoy/7 días/con teléfono), tabla con búsqueda, etiqueta de campaña, eliminar, exportar CSV.
- Verificado end-to-end (API + UI con screenshots).

## Integration status
- SendGrid: código completo y listo. INACTIVO hasta que el usuario agregue SENDGRID_API_KEY y un SENDER_EMAIL verificado en backend/.env. Los leads se guardan siempre; el envío de correo se omite limpiamente si falta la key.

## Backlog / Next
- P1: Activar SendGrid (pegar API Key + remitente verificado) y probar correo real.
- P2: Paginación en panel si crecen los leads (>200).
- P2: Envío automático del PDF por correo al lead (opcional).
- P2: Filtros por campaña / rango de fechas; gráficas.
- P2: Captcha / rate-limit anti-spam en el formulario público.
