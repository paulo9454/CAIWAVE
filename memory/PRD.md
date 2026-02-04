# CAIWAVE Wi-Fi Hotspot Platform - PRD v5.0

## Project Overview
Production-ready Wi-Fi hotspot billing, advertising, and premium live access platform (CAIWAVE). Features ISP-grade MikroTik integration, Package-Based Advertising System, admin-controlled campaigns, CAIWAVE TV streaming service, and **Subscription & Billing System** for hotspot owners.

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
- **M-Pesa Daraja** - STK Push structure ready (MOCKED without credentials)
- **MikroTik / RADIUS** - FreeRADIUS structure ready

### Phase 4: Package-Based Advertising ✅ COMPLETE
**Advertising Packages (Admin-defined)**

| Package | Coverage Scope | Duration | Price (KES) |
|---------|----------------|----------|-------------|
| Small Area | Constituency | 3 days | 300 |
| Large Area | County | 7 days | 1,000 |
| Wide Area | National | 14 days | 3,500 |

### Phase 5: Subscription & Billing System ✅ COMPLETE (NEW)

**Pricing & Trial Rules:**
- Monthly subscription: **KES 500 per hotspot per month**
- **14-day free trial** for every new hotspot
- Invoice created on Day 1 with status = TRIAL

**Invoice Statuses:**
- `draft` - Initial state
- `trial` - During 14-day trial period
- `unpaid` - After trial ends
- `paid` - Payment received
- `overdue` - Day 18+ without payment

**Access Enforcement:**
| Status | Access |
|--------|--------|
| Trial (Day 1-14) | Full access |
| Grace Period (Day 15-17) | Limited dashboard access |
| Suspended (Day 18+) | Hotspot disabled, ads paused |

**Owner Dashboard Features:**
- Subscription Status Banner (trial countdown, pay now button)
- Billing page with invoice history
- M-Pesa STK Push payment

**Admin Dashboard Features:**
- Invoice Management page
- Stats: Total, Trial, Unpaid, Overdue, Revenue
- Mark Paid / Suspend Overdue actions
- Invoice filtering by status

---

## Key API Endpoints

### Subscription & Billing (NEW)
- `GET /api/subscriptions/status` - Owner's subscription status
- `POST /api/subscriptions/start-trial` - Start 14-day trial
- `GET /api/invoices/` - List invoices (owner sees own, admin sees all)
- `GET /api/invoices/current` - Owner's current invoice
- `GET /api/invoices/{id}` - Get specific invoice
- `POST /api/invoices/pay/{id}` - Pay via M-Pesa
- `GET /api/invoices/admin/all` - Admin: all invoices with stats
- `POST /api/invoices/admin/mark-paid/{id}` - Admin: mark paid
- `POST /api/invoices/admin/suspend-overdue` - Admin: suspend all overdue

### Ad Packages
- `GET /api/ad-packages/` - List packages (public)
- `POST /api/ad-packages/` - Create (admin)
- `PUT /api/ad-packages/{id}` - Update (admin)

### Locations
- `GET /api/locations/counties` - Kenya counties
- `GET /api/locations/constituencies` - Kenya constituencies

### Ads
- `POST /api/ads/upload` - Upload with package selection
- `POST /api/ads/{id}/approve` - Admin approve/reject
- `POST /api/ads/{id}/pay` - M-Pesa payment
- `POST /api/ads/{id}/activate` - Go live (admin)

---

## Credentials
- **Admin**: admin@caiwave.com / admin123
- **Hotspot Owner**: owner@caiwave.com / owner123
- **Advertiser**: advertiser@caiwave.com / advertiser123

## Key Files
- **Backend**: `/app/backend/server.py`
- **Frontend Admin**: `/app/frontend/src/pages/admin/Dashboard.jsx`
- **Frontend Owner**: `/app/frontend/src/pages/owner/Dashboard.jsx`
- **Frontend Advertiser**: `/app/frontend/src/pages/advertiser/Dashboard.jsx`
- **Landing Page**: `/app/frontend/src/pages/LandingPage.jsx`

---

## MOCKED/PLACEHOLDER Features
- **M-Pesa STK Push**: Simulated when credentials not configured
- **FreeRADIUS**: Structure ready, requires live server configuration

---

## Future Tasks (Backlog)
- **P1**: Partner Onboarding Wizard - Guided setup for hotspot owners
- **P1**: Automated Payment Reminders (SMS/Email before trial ends)
- **P2**: Voucher Printing System - Generate pre-paid vouchers
- **P2**: Invoice PDF Export
- **P3**: Equipment Marketplace UI
- **P3**: System Audit Logs
- **P3**: Two-Factor Authentication (2FA)
- **REFACTORING**: Split backend/server.py into modules
- **REFACTORING**: Split admin Dashboard.jsx into separate pages

---

## Last Updated: February 2026
