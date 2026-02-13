# CAIWAVE Wi-Fi Hotspot Platform - PRD v9.2

## Project Overview
Production-ready Wi-Fi hotspot billing, advertising, and premium live access platform (CAIWAVE). Features ISP-grade MikroTik integration, Package-Based Advertising System, admin-controlled campaigns, CAIWAVE TV streaming service, Subscription & Billing System, and **Paystack payments (M-Pesa + Card + Bank)**.

**Domain**: www.caiwave.com

## Tech Stack
- **Backend**: FastAPI + Python
- **Frontend**: React + TailwindCSS + Shadcn UI
- **Database**: MongoDB
- **Auth**: JWT-based multi-role
- **Payments**: Paystack (M-Pesa STK Push + Cards + Bank)
- **Router**: MikroTik via FreeRADIUS

---

## Recent Changes (Feb 13, 2026)

### 1. Replaced M-Pesa Daraja with Paystack
- Admin Integration Settings now shows **Paystack Payment Gateway**
- Displays: Live Mode, M-Pesa STK Push, Cards (Visa/Mastercard), Bank Transfer
- Removed M-Pesa Daraja tab completely

### 2. Clarified MikroTik Management Roles
- **Hotspot Owners**: Register their MikroTik routers from Owner Dashboard → MikroTik Setup
- **Admins**: View and manage ALL registered routers from Admin → Integrations → RADIUS Server
- Added note: "Hotspot owners register their MikroTik routers from their dashboard. As admin, you can view and manage all registered routers here."

### 3. Updated MikroTik Script
- Added Paystack domains to walled garden (*.paystack.com, *.paystack.co)
- Added remote management (API enabled, management user created)
- Fixed redirect_slashes issue for API endpoints

### 4. Fixed Deployment Issues
- Added `redirect_slashes=False` to FastAPI to prevent 307 redirects
- Fixed API endpoints to use consistent trailing slashes

---

## MikroTik Integration Flow

### For Hotspot Owners:
1. Go to **Owner Dashboard → MikroTik Setup**
2. Click **Add MikroTik**
3. Select your hotspot from dropdown
4. Enter router name
5. Click **Generate Configuration Script**
6. Copy script and paste into MikroTik terminal
7. Click **Confirm Connection** after setup

### For Admins:
1. Go to **Admin Dashboard → Integrations → RADIUS Server**
2. View all registered routers from all owners
3. Click **Generate Config** to regenerate scripts
4. **Disable/Enable** routers as needed

---

## Paystack Configuration (LIVE)
```env
PAYSTACK_SECRET_KEY=sk_live_301cc85e6d03476c35e41ce1f20a2352be75b432
PAYSTACK_PUBLIC_KEY=pk_live_485228adec2487e9d81fe542775f148c9ff43606
PAYSTACK_ENVIRONMENT=live
```

---

## Documentation
- **FreeRADIUS Setup**: `/app/docs/FREERADIUS_SETUP.md`

## Last Updated: February 13, 2026 - Version 9.2
