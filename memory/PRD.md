# CAIWAVE Wi-Fi Hotspot Platform - PRD v7.0

## Project Overview
Production-ready Wi-Fi hotspot billing, advertising, and premium live access platform (CAIWAVE). Features ISP-grade MikroTik integration, Package-Based Advertising System, admin-controlled campaigns, CAIWAVE TV streaming service, Subscription & Billing System, and **M-Pesa Daraja STK Push payments**.

**Domain**: www.caiwave.com

## Branding (LOCKED)
- **Brand Name**: CAIWAVE
- **Logo**: Blue (#0032FA) background with white WiFi signal icon + "C" letter at center
- **Mandatory Footer**: "Powered by CAIWAVE WiFi © 2026. All Rights Reserved."

## Tech Stack
- **Backend**: FastAPI + Python
- **Frontend**: React + TailwindCSS + Shadcn UI
- **Database**: MongoDB
- **Auth**: JWT-based multi-role
- **Payments**: M-Pesa Daraja API (LIVE sandbox integration)
- **Router**: MikroTik via FreeRADIUS (structure ready)

---

## What's Been Implemented

### Phase 1: Branding ✅ COMPLETE
- Rebranded from CAITECH to CAIWAVE
- New logo with WiFi icon + "C" letter center

### Phase 2: Admin Features ✅ COMPLETE
- **Campaigns System** (Admin Only)
- **CAIWAVE TV Streams** (Admin Only)
- **Subsidized Uptime** (Admin Only)

### Phase 3: Integrations ✅ COMPLETE
- **M-Pesa Daraja** - LIVE STK Push integration
- **MikroTik / RADIUS** - FreeRADIUS structure ready

### Phase 4: Package-Based Advertising ✅ COMPLETE
| Package | Coverage | Duration | Price (KES) |
|---------|----------|----------|-------------|
| Small Area | Constituency | 3 days | 300 |
| Large Area | County | 7 days | 1,000 |
| Wide Area | National | 14 days | 3,500 |

### Phase 5: Subscription & Billing ✅ COMPLETE
- Monthly subscription: KES 500/hotspot/month
- 14-day free trial
- Invoice statuses: trial → unpaid → paid → overdue
- Access enforcement (suspend overdue hotspots)

### Phase 6: M-Pesa STK Push Integration ✅ COMPLETE (NEW)

**Three Payment Flows:**

| Role | Endpoint | Post-Payment Action |
|------|----------|---------------------|
| Hotspot Owner | `/api/mpesa/owner/pay-subscription` | Activates subscription |
| Advertiser | `/api/mpesa/advertiser/pay-ad` | Ad goes live |
| WiFi Client | `/api/mpesa/client/pay-wifi` | Grants WiFi access |

**Current Configuration (Sandbox):**
```env
MPESA_ENV=sandbox
MPESA_SHORTCODE=174379
MPESA_CONSUMER_KEY=7ONektuabEWBEDGNKM4UgvdBb9le0XdIG3Q0PMfHfqnq3MeM
```

**Production Credentials (Ready to switch):**
```env
MPESA_SHORTCODE=6386009
MPESA_TILL_NUMBER=8573842
```

**Documentation**: `/app/memory/MPESA_INTEGRATION.md`

---

## Key API Endpoints

### M-Pesa Payments (NEW)
| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/mpesa/stk-push` | POST | No | Generic STK Push |
| `/api/mpesa/owner/pay-subscription` | POST | Owner | Pay subscription |
| `/api/mpesa/advertiser/pay-ad` | POST | Advertiser | Pay for ad |
| `/api/mpesa/client/pay-wifi` | POST | No | Pay for WiFi |
| `/api/mpesa/callback` | POST | No | Safaricom callback |
| `/api/mpesa/status/{checkout_id}` | GET | No | Check status |
| `/api/mpesa/wifi-credentials/{checkout_id}` | GET | No | Get WiFi credentials |
| `/api/mpesa/transactions` | GET | Admin | List transactions |
| `/api/mpesa/config-status` | GET | Admin | Config status |

### Subscription & Billing
- `GET /api/subscriptions/status` - Subscription status
- `POST /api/subscriptions/start-trial` - Start trial
- `GET /api/invoices/` - List invoices
- `POST /api/invoices/pay/{id}` - Pay invoice

### Ad Packages
- `GET /api/ad-packages/` - List packages
- `POST /api/ads/upload` - Upload ad
- `POST /api/ads/{id}/approve` - Approve ad
- `POST /api/ads/{id}/activate` - Activate ad

---

## Credentials
- **Admin**: admin@caiwave.com / admin123
- **Hotspot Owner**: owner@caiwave.com / owner123
- **Advertiser**: advertiser@caiwave.com / advertiser123

## Key Files
- **Backend**: `/app/backend/server.py`
- **Backend .env**: `/app/backend/.env`
- **M-Pesa Docs**: `/app/memory/MPESA_INTEGRATION.md`
- **Frontend Admin**: `/app/frontend/src/pages/admin/Dashboard.jsx`
- **Frontend Owner**: `/app/frontend/src/pages/owner/Dashboard.jsx`

## Modular Backend Structure (NEW - v2.1.0)
```
/app/backend/
├── config.py           # Configuration management (env vars, constants)
├── database.py         # MongoDB connection
├── models/             # Pydantic models & enums
│   ├── enums.py       # All enum types
│   ├── user.py        # User models
│   ├── package.py     # WiFi package models
│   ├── hotspot.py     # Hotspot models
│   ├── invoice.py     # Invoice & subscription models
│   ├── session.py     # Session models
│   ├── payment.py     # Payment models
│   ├── ad.py          # Advertisement models
│   ├── voucher.py     # Voucher models
│   ├── campaign.py    # Campaign & stream models
│   └── settings.py    # System settings models
├── services/           # Business logic services
│   ├── mpesa.py       # M-Pesa Daraja integration
│   ├── sms.py         # SMS gateway (Africa's Talking)
│   ├── whatsapp.py    # WhatsApp (Twilio) integration
│   └── notification.py # Unified notification service
├── utils/              # Helper utilities
│   ├── auth.py        # JWT, password hashing, user auth
│   ├── voucher.py     # Voucher code generation
│   ├── revenue.py     # Revenue sharing calculations
│   └── locations.py   # Kenya counties/constituencies
├── routes/             # API route modules (partial)
│   ├── auth.py        # Authentication routes
│   ├── packages.py    # Package routes
│   └── locations.py   # Location routes
└── server.py           # Main FastAPI application
```

---

## Testing Notes
- M-Pesa sandbox is LIVE and working
- Callbacks require ngrok setup for full end-to-end testing
- All API tests passing (100% success rate)

---

## Future Tasks (Backlog)
- **P1**: ngrok setup guide for M-Pesa callback testing
- **P1**: SMS notification integration for payment confirmations
- **P1**: Partner Onboarding Wizard
- **P2**: Voucher Printing System
- **P2**: Invoice PDF/CSV Export
- **P2**: Complete backend route modularization (move remaining routes from server.py to /routes)
- **P2**: Frontend dashboard component modularization
- **P3**: Equipment Marketplace UI
- **P3**: System Audit Logs
- **P3**: Two-Factor Authentication (2FA)

---

## Last Updated: February 2026 - Version 2.1.0
