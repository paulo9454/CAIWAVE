# CAIWAVE Wi-Fi Hotspot Billing Platform - PRD v3.1

## Project Overview
Production-ready Wi-Fi hotspot billing, advertising, and premium live access platform (CAIWAVE). Features ISP-grade MikroTik integration, integrated advertising engine, admin-controlled campaigns, and CAIWAVE TV streaming service.

## Branding (LOCKED)
- **Brand Name**: CAIWAVE
- **Logo**: Blue (#0032FA) background with white WiFi signal icon + "C" letter at center
- **Mandatory Footer**: "Powered by CAIWAVE WiFi © 2026. All Rights Reserved."

## Tech Stack
- **Backend**: FastAPI + Python
- **Frontend**: React + TailwindCSS + Shadcn UI
- **Database**: MongoDB
- **Auth**: JWT-based multi-role
- **Payments**: M-Pesa Daraja API (structure ready)
- **Router**: MikroTik via FreeRADIUS (structure ready)
- **SMS**: Flexible gateway (Africa's Talking / Centipid)
- **WhatsApp**: Twilio

---

## What's Been Implemented

### Phase 1: Branding ✅ COMPLETE
- Rebranded from CAITECH to CAIWAVE
- New logo with WiFi icon + "C" letter center
- Updated all UI components and footer

### Phase 2: Admin Features ✅ COMPLETE
- **Campaigns System** (Admin Only) - Full CRUD
- **CAIWAVE TV Streams** (Admin Only) - Full CRUD with live status
- **Subsidized Uptime** (Admin Only) - Discounted pricing offers
- Landing page CAIWAVE TV section

### Phase 3: Integrations ✅ COMPLETE
- **M-Pesa Daraja** - STK Push structure ready
  - `/api/mpesa/stk-push` - Initiate payment
  - `/api/mpesa/callback` - Handle M-Pesa callbacks
  - `/api/mpesa/status/{id}` - Check payment status
  - `/api/mpesa/config-status` - Configuration status
  
- **MikroTik / RADIUS** - FreeRADIUS structure ready
  - `/api/radius/config` - RADIUS server config
  - `/api/radius/nas-clients` - Manage NAS clients (MikroTik routers)
  - `/api/radius/generate-config/{id}` - Generate MikroTik RouterOS commands
  - `/api/radius/test-connection` - Test RADIUS connectivity
  
- **Integration Settings UI** - Comprehensive admin panel with:
  - Tabbed interface (M-Pesa, MikroTik/RADIUS, SMS)
  - Setup instructions and environment variable documentation
  - NAS client management (add, edit, delete, toggle)
  - MikroTik config generation with copy-to-clipboard

---

## Configuration Required (in backend/.env)

### M-Pesa Daraja
```env
MPESA_ENV=sandbox
MPESA_CONSUMER_KEY=your_key
MPESA_CONSUMER_SECRET=your_secret
MPESA_SHORTCODE=174379
MPESA_PASSKEY=your_passkey
MPESA_CALLBACK_URL=https://your-domain/api/mpesa/callback
```

### FreeRADIUS
```env
RADIUS_ENABLED=true
RADIUS_HOST=your_freeradius_server_ip
RADIUS_SECRET=your_shared_secret
RADIUS_AUTH_PORT=1812
RADIUS_ACCT_PORT=1813
```

### SMS (Africa's Talking)
```env
SMS_PROVIDER=africas_talking
AT_API_KEY=your_api_key
AT_USERNAME=your_username
AT_SENDER_ID=CAIWAVE
```

---

## API Endpoints Summary

### Authentication
- `POST /api/auth/login`
- `POST /api/auth/register`
- `GET /api/auth/me`

### Packages
- `GET /api/packages`

### Hotspots
- `GET /api/hotspots`
- `POST /api/hotspots`

### Payments
- `POST /api/payments/initiate`
- `GET /api/portal/{hotspot_id}`

### M-Pesa
- `POST /api/mpesa/stk-push`
- `POST /api/mpesa/callback`
- `GET /api/mpesa/config-status`

### RADIUS / MikroTik
- `GET /api/radius/config`
- `GET /api/radius/nas-clients`
- `POST /api/radius/nas-clients`
- `PUT /api/radius/nas-clients/{id}`
- `DELETE /api/radius/nas-clients/{id}`
- `POST /api/radius/nas-clients/{id}/toggle`
- `GET /api/radius/generate-config/{id}`

### Campaigns (Admin Only)
- `GET /api/campaigns/`
- `POST /api/campaigns/`
- `PUT /api/campaigns/{id}`
- `POST /api/campaigns/{id}/status`
- `DELETE /api/campaigns/{id}`

### CAIWAVE TV Streams (Admin Only)
- `GET /api/streams/`
- `GET /api/streams/live`
- `POST /api/streams/`
- `PUT /api/streams/{id}`
- `POST /api/streams/{id}/toggle`
- `DELETE /api/streams/{id}`

### Subsidized Uptime (Admin Only)
- `GET /api/subsidized-uptime/`
- `GET /api/subsidized-uptime/active`
- `POST /api/subsidized-uptime/`
- `PUT /api/subsidized-uptime/{id}`
- `POST /api/subsidized-uptime/{id}/status`
- `DELETE /api/subsidized-uptime/{id}`

### Ads
- `GET /api/ads/pending`
- `POST /api/ads/{id}/approve`
- `POST /api/ads/{id}/reject`

### Settings
- `GET /api/settings/revenue-config`
- `PUT /api/settings/revenue-config`

---

## Credentials
- **Admin**: admin@caiwave.com / admin123

## Key Files
- **Integration Settings**: `/app/frontend/src/pages/admin/Dashboard.jsx` (IntegrationSettingsPage component)
- **Backend Server**: `/app/backend/server.py`
- **Environment Config**: `/app/backend/.env`

---

## Future Tasks (Backlog)
- Partner Onboarding Wizard
- Voucher Printing System
- Equipment Marketplace UI
- System Audit Logs
- Two-Factor Authentication (2FA)
- Actual FreeRADIUS server integration testing
- Production M-Pesa credentials setup
