# CAIWAVE Wi-Fi Hotspot Platform - PRD v9.0

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

### Phase 1-7: Previously Completed ✅
- Branding (CAIWAVE)
- Admin Features (Campaigns, CAIWAVE TV, Subsidized Uptime)
- Paystack Payments (M-Pesa + Card)
- MikroTik Integration
- Package-Based Advertising
- Subscription & Billing
- Enhanced Ad Management

### Phase 8: Captive Portal & Ad Visibility Fixes ✅ (Feb 12, 2026)

**Captive Portal Implementation:**
- Fixed API endpoint from `/api/ads/public/active` to `/api/ads/active`
- Captive Portal at `/portal/:hotspotId` now displays active ads
- Ads rotate automatically every 5 seconds
- WhatsApp and Website click-through buttons shown for ads
- WiFi packages displayed for purchase
- CAIWAVE TV streams preview

**Advertiser Dashboard Ad Visibility Fix:**
- Fixed video ad preview in AdCard component
- Added play button overlay for video ads
- Implemented `preload="auto"` and `onCanPlay` handlers
- Added error state handling for failed video loads
- Video plays on hover, pauses on mouse leave

---

## Key API Endpoints

### Public Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/ads/active` | GET | Get active ads for captive portal |
| `/api/packages/` | GET | Get WiFi packages |
| `/api/streams/live` | GET | Get live CAIWAVE TV streams |

### Paystack Payments (PRIMARY)
| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/paystack/config` | GET | No | Get Paystack config |
| `/api/paystack/owner/pay-subscription` | POST | Owner | Pay subscription |
| `/api/paystack/advertiser/pay-ad` | POST | Advertiser | Pay for ad |
| `/api/paystack/client/pay-wifi` | POST | No | Pay for WiFi |

---

## Credentials
- **Admin**: admin@caiwave.com / admin123
- **Hotspot Owner**: owner@caiwave.com / owner123
- **Advertiser**: advertiser@caiwave.com / advertiser123

## Key Files
- **Backend**: `/app/backend/server.py`
- **Frontend Captive Portal**: `/app/frontend/src/pages/CaptivePortal.jsx`
- **Frontend Advertiser**: `/app/frontend/src/pages/advertiser/Dashboard.jsx`
- **Frontend Admin**: `/app/frontend/src/pages/admin/Dashboard.jsx`
- **Frontend Owner**: `/app/frontend/src/pages/owner/Dashboard.jsx`

---

## Testing Status (Feb 12, 2026)
- ✅ Homepage loads correctly (no dark screen)
- ✅ Captive Portal shows ads and WiFi packages
- ✅ Login works for all user roles
- ✅ Advertiser Dashboard shows stats and ad cards
- ✅ Video ad preview with play button overlay
- ✅ 100% frontend test pass rate

---

## Future Tasks (Backlog)

### P0 - Critical
- None (all critical issues resolved)

### P1 - High Priority
- Add "Click to WhatsApp" wa.me link feature for ads
- Add analytics to Hotspot Owner dashboard (area-based connection data)
- Partner Onboarding Wizard

### P2 - Medium Priority
- Two-Factor Authentication (2FA)
- Final admin role protection audit
- Voucher Printing System
- Invoice PDF/CSV Export
- SMS notification integration

### P3 - Low Priority
- Equipment Marketplace UI
- System Audit Logs
- Backend route modularization
- Frontend component modularization

---

## Last Updated: February 12, 2026 - Version 9.0
