# CAIWAVE Wi-Fi Hotspot Platform - PRD v9.1

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

## Complete Feature List

### ✅ MikroTik & RADIUS Integration
| Feature | Status | Endpoint |
|---------|--------|----------|
| Router Registration | ✅ Done | `POST /api/mikrotik/register-router` |
| Config Script Generation | ✅ Done | Auto-generated on registration |
| RADIUS Authorization | ✅ Done | `POST /api/radius/authorize` |
| RADIUS Accounting | ✅ Done | `POST /api/radius/accounting` |
| Post-Auth Logging | ✅ Done | `POST /api/radius/post-auth` |
| NAS Client Management | ✅ Done | `/api/radius/nas-clients` |
| Auth Logs | ✅ Done | `GET /api/radius/auth-logs` |

### ✅ Captive Portal & Ads
| Feature | Status |
|---------|--------|
| Ad Display (Images) | ✅ Working |
| Ad Display (Videos) | ✅ Working |
| Auto-Rotation (5s) | ✅ Working |
| WhatsApp Click-to-Chat | ✅ Working |
| Website Click-Through | ✅ Working |
| WiFi Package Purchase | ✅ Working |
| CAIWAVE TV Preview | ✅ Working |

### ✅ Payment System (Paystack)
| Feature | Status |
|---------|--------|
| M-Pesa Integration | ✅ Live |
| Card Payments | ✅ Live |
| Owner Subscriptions | ✅ Working |
| Advertiser Payments | ✅ Working |
| WiFi Package Sales | ✅ Working |

### ✅ User Dashboards
| Dashboard | Features |
|-----------|----------|
| Admin | Hotspots, Users, Ads, Campaigns, CAIWAVE TV, Settings |
| Owner | Hotspots, MikroTik Setup, Billing, Payments, Analytics (placeholder) |
| Advertiser | Ad Creation, Performance Stats, Payment History |

---

## Key API Endpoints

### RADIUS Endpoints (FreeRADIUS Integration)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/radius/authorize` | POST | Authenticate WiFi user |
| `/api/radius/accounting` | POST | Track session start/stop/update |
| `/api/radius/post-auth` | POST | Log authentication results |
| `/api/radius/auth-logs` | GET | View auth logs (admin) |
| `/api/radius/nas-clients` | GET/POST | Manage NAS clients |

### Analytics Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/analytics/area-stats` | GET | Area-based connection stats |
| `/api/analytics/hotspot-rankings` | GET | Hotspot performance rankings |

---

## Documentation
- **FreeRADIUS Setup Guide**: `/app/docs/FREERADIUS_SETUP.md`

---

## Credentials
- **Admin**: admin@caiwave.com / admin123
- **Hotspot Owner**: owner@caiwave.com / owner123
- **Advertiser**: advertiser@caiwave.com / advertiser123

---

## Future Tasks (Backlog)

### P1 - High Priority
- Owner Dashboard Analytics UI (backend ready)
- Partner Onboarding Wizard

### P2 - Medium Priority
- Two-Factor Authentication (2FA)
- Voucher Printing System
- SMS Notifications

### P3 - Low Priority
- Equipment Marketplace UI
- System Audit Logs

---

## Last Updated: February 12, 2026 - Version 9.1
