# CAIWAVE Wi-Fi Hotspot Platform - PRD v8.0

## Project Overview
Production-ready Wi-Fi hotspot billing, advertising, and premium live access platform (CAIWAVE). Features ISP-grade MikroTik integration, Package-Based Advertising System, admin-controlled campaigns, CAIWAVE TV streaming service, Subscription & Billing System, and **Paystack payments (M-Pesa + Card)**.

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
- **Payments**: Paystack (M-Pesa + Card) - LIVE integration
- **Router**: MikroTik via FreeRADIUS + Auto-Configuration

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
- **Paystack Payments** - LIVE M-Pesa + Card integration (replaced M-Pesa Daraja)
- **MikroTik / RADIUS** - Auto-configuration with script generation

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

### Phase 6: Enhanced Ad Management ✅ COMPLETE (Feb 2026)
- **Campaign/Ads Display**: Image-first card layout with dominant thumbnails
- **Quick Stats Dashboard**: Live Now, Pending, Today, Ended counts
- **Ad Time & Date Tracking**: Go-Live and End dates for every ad
- **Status Flow**: Pending → Approved → Paid → Live → Ended
- **Date Filtering**: Today's ads vs Yesterday's ads tabs
- **CAIWAVE TV Contact**: WhatsApp button (https://wa.me/254738570630)

### Phase 7: Paystack Integration ✅ COMPLETE (Feb 11, 2026)

**Replaced M-Pesa Daraja with Paystack for all payments:**

| Role | Endpoint | Post-Payment Action |
|------|----------|---------------------|
| Hotspot Owner | `/api/paystack/owner/pay-subscription` | Activates subscription |
| Advertiser | `/api/paystack/advertiser/pay-ad` | Ad goes live |
| WiFi Client | `/api/paystack/client/pay-wifi` | Grants WiFi access |

**Configuration (LIVE):**
```env
PAYSTACK_SECRET_KEY=sk_live_301cc85e6d03476c35e41ce1f20a2352be75b432
PAYSTACK_PUBLIC_KEY=pk_live_485228adec2487e9d81fe542775f148c9ff43606
PAYSTACK_ENVIRONMENT=live
```

**Features:**
- M-Pesa mobile money payments (STK Push via Paystack)
- Card payments
- Subaccount support for revenue splitting (hotspot owners)
- Webhook handling for payment confirmations

### Phase 8: MikroTik Auto-Configuration ✅ COMPLETE (Feb 11, 2026)

**Centipaid-style MikroTik onboarding workflow:**
- Owner clicks "Add MikroTik" in dashboard
- System generates secure auto-configuration script
- Script configures: Hotspot, RADIUS, Anti-sharing, DNS, Firewall
- Connection confirmation and status tracking

**API Endpoints:**
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/mikrotik-onboard/register` | POST | Register router & generate script |
| `/api/mikrotik-onboard/confirm` | POST | Confirm connection |
| `/api/mikrotik-onboard/routers` | GET | List registered routers |
| `/api/mikrotik-onboard/routers/{id}/script` | GET | Regenerate script |

---

## Key API Endpoints

### Paystack Payments (PRIMARY)
| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/paystack/config` | GET | No | Get Paystack config |
| `/api/paystack/banks` | GET | No | List Kenya banks |
| `/api/paystack/initialize` | POST | No | Initialize payment |
| `/api/paystack/charge-mobile` | POST | No | M-Pesa STK Push |
| `/api/paystack/owner/pay-subscription` | POST | Owner | Pay subscription |
| `/api/paystack/advertiser/pay-ad` | POST | Advertiser | Pay for ad |
| `/api/paystack/client/pay-wifi` | POST | No | Pay for WiFi |
| `/api/paystack/verify/{reference}` | POST | No | Verify payment |
| `/api/paystack/webhook` | POST | No | Paystack webhook |
| `/api/paystack/subaccount/create` | POST | Owner/Admin | Create subaccount |
| `/api/paystack/transactions` | GET | Admin | List transactions |

### M-Pesa (LEGACY - Deprecated)
| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/mpesa/stk-push` | POST | No | Generic STK Push |
| `/api/mpesa/owner/pay-subscription` | POST | Owner | Pay subscription |
| `/api/mpesa/advertiser/pay-ad` | POST | Advertiser | Pay for ad |
| `/api/mpesa/client/pay-wifi` | POST | No | Pay for WiFi |
| `/api/mpesa/callback` | POST | No | Safaricom callback |
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
- **P1**: Partner Onboarding Wizard - guided setup for new hotspot owners
- **P1**: SMS notification integration for payment confirmations
- **P2**: Voucher Printing System
- **P2**: Invoice PDF/CSV Export
- **P2**: Complete backend route modularization (move remaining routes from server.py to /routes)
- **P2**: Frontend dashboard component modularization
- **P3**: Equipment Marketplace UI
- **P3**: System Audit Logs
- **P3**: Two-Factor Authentication (2FA)

---

## Last Updated: February 2026 - Version 2.1.0
