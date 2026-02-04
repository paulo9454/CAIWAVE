# CAIWAVE Wi-Fi Hotspot Billing Platform - PRD v4.0

## Project Overview
Production-ready Wi-Fi hotspot billing, advertising, and premium live access platform (CAIWAVE). Features ISP-grade MikroTik integration, **Package-Based Advertising System**, admin-controlled campaigns, and CAIWAVE TV streaming service.

## Branding (LOCKED)
- **Brand Name**: CAIWAVE
- **Logo**: Blue (#0032FA) background with white WiFi signal icon + "C" letter at center
- **Mandatory Footer**: "Powered by CAIWAVE WiFi © 2026. All Rights Reserved."

## Tech Stack
- **Backend**: FastAPI + Python
- **Frontend**: React + TailwindCSS + Shadcn UI
- **Database**: MongoDB
- **Auth**: JWT-based multi-role
- **Payments**: M-Pesa Daraja API (structure ready, placeholder credentials)
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
- **M-Pesa Daraja** - STK Push structure ready (MOCKED without credentials)
- **MikroTik / RADIUS** - FreeRADIUS structure ready
- **Integration Settings UI** - Comprehensive admin panel

### Phase 4: Package-Based Advertising ✅ COMPLETE (NEW)
**Advertising Packages (Admin-defined, non-editable by advertisers)**

| Package | Coverage Scope | Duration | Price (KES) |
|---------|----------------|----------|-------------|
| Small Area | Constituency | 3 days | 300 |
| Large Area | County | 7 days | 1,000 |
| Wide Area | National | 14 days | 3,500 |

**Advertiser Flow:**
1. Select package → See pricing upfront
2. Choose coverage (constituencies/counties/national)
3. Upload media (image or video)
4. Submit for admin review

**Admin Flow:**
1. Review pending ads
2. Validate coverage and content quality
3. Approve or reject (no price negotiation)
4. After advertiser payment, activate ad

**Status Flow:**
`PENDING_APPROVAL` → `APPROVED` → `PAID` → `ACTIVE`

**Key APIs:**
- `GET /api/ad-packages` - List all packages
- `GET /api/locations/counties` - Kenya counties
- `GET /api/locations/constituencies` - Kenya constituencies
- `POST /api/ads/upload` - Upload ad with package selection
- `POST /api/ads/{id}/approve` - Admin approve/reject
- `POST /api/ads/{id}/pay` - M-Pesa payment
- `POST /api/ads/{id}/activate` - Go live

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

---

## API Endpoints Summary

### Authentication
- `POST /api/auth/login`
- `POST /api/auth/register`
- `GET /api/auth/me`

### Ad Packages (NEW)
- `GET /api/ad-packages/` - List packages (public)
- `GET /api/ad-packages/{id}` - Get package
- `POST /api/ad-packages/` - Create (admin)
- `PUT /api/ad-packages/{id}` - Update (admin)
- `DELETE /api/ad-packages/{id}` - Delete (admin)
- `POST /api/ad-packages/{id}/toggle` - Enable/disable (admin)

### Locations (NEW)
- `GET /api/locations/counties` - Kenya counties
- `GET /api/locations/constituencies?county=X` - Constituencies

### Ads
- `GET /api/ads/` - List ads (advertiser sees own, admin sees all)
- `GET /api/ads/pending` - Admin only
- `GET /api/ads/active` - Public (captive portal)
- `POST /api/ads/upload` - Upload with package selection
- `POST /api/ads/{id}/approve` - Admin approve/reject
- `POST /api/ads/{id}/pay` - M-Pesa payment
- `POST /api/ads/{id}/activate` - Go live (admin)
- `POST /api/ads/{id}/suspend` - Suspend (admin)
- `POST /api/ads/{id}/reactivate` - Reactivate (admin)

### Wi-Fi Packages
- `GET /api/packages`

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

---

## Credentials
- **Admin**: admin@caiwave.com / admin123
- **Advertiser**: advertiser@caiwave.com / advertiser123

## Key Files
- **Backend**: `/app/backend/server.py` (monolithic - needs refactoring)
- **Frontend Admin**: `/app/frontend/src/pages/admin/Dashboard.jsx`
- **Frontend Advertiser**: `/app/frontend/src/pages/advertiser/Dashboard.jsx`
- **Environment Config**: `/app/backend/.env`

---

## Future Tasks (Backlog)
- **P1**: Partner Onboarding Wizard - Guided setup for hotspot owners
- **P2**: Voucher Printing System - Generate pre-paid vouchers
- **P3**: Equipment Marketplace UI
- **P3**: System Audit Logs
- **P3**: Two-Factor Authentication (2FA)
- **REFACTORING**: Split backend/server.py into modules
- **REFACTORING**: Split admin Dashboard.jsx into separate pages

---

## MOCKED/PLACEHOLDER Features
- **M-Pesa STK Push**: Simulated when credentials not configured (payment succeeds automatically)
- **FreeRADIUS**: Structure ready, requires live server configuration

---

## Last Updated: February 2026
