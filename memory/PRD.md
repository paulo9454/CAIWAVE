# CAITECH Wi-Fi Hotspot Billing Platform - PRD

## Project Overview
Production-ready Wi-Fi hotspot billing platform with integrated advertising engine managed by CAITECH.

## Target Users
1. **Super Admin (CAITECH)** - Platform management, packages, campaigns
2. **Hotspot Owner (Partner)** - ISP dashboard, revenue tracking, hotspot management
3. **Advertiser** - Ad creation, campaign targeting, performance tracking
4. **End User** - WiFi purchase via captive portal

## Core Requirements (Static)
- Paid internet access from KES 5
- Free WiFi sponsored by ads
- Location-based advertising engine
- MikroTik router integration (RADIUS)
- M-Pesa payment integration
- No monthly subscription for hotspot owners
- 70/30 revenue sharing model

## Tech Stack
- **Backend**: FastAPI + Python
- **Frontend**: React + TailwindCSS
- **Database**: MongoDB
- **Auth**: JWT-based multi-role
- **Payments**: M-Pesa (Mock/Sandbox)
- **Router**: MikroTik (Mock RADIUS)

---

## What's Been Implemented (v1.0 - Feb 2026)

### Backend API Endpoints
- [x] Authentication (register, login, JWT)
- [x] Packages CRUD (5 default tiers: KES 5-100)
- [x] Hotspots management
- [x] Sessions tracking
- [x] Payments (Mock M-Pesa STK Push)
- [x] Ads CRUD
- [x] Campaigns with targeting
- [x] Analytics dashboard
- [x] Captive portal data endpoint
- [x] Free WiFi via ads endpoint
- [x] Seed data initialization

### Frontend Pages
- [x] Landing page (marketing)
- [x] Login/Register (multi-role)
- [x] Captive Portal (mobile-first)
- [x] Admin Dashboard (overview, packages, hotspots, campaigns, users)
- [x] Hotspot Owner Dashboard (overview, hotspots, payments)
- [x] Advertiser Dashboard (overview, ads, campaigns)

### Features
- [x] Multi-role JWT authentication
- [x] ISP-style package dropdown
- [x] Revenue analytics with charts
- [x] Location-based ad targeting (global/local)
- [x] Dark theme UI
- [x] Mock payment confirmation

---

## Prioritized Backlog

### P0 - Critical (Next Sprint)
- [ ] Real M-Pesa Daraja API integration
- [ ] Actual MikroTik RADIUS implementation
- [ ] Session enforcement (auto-disconnect)

### P1 - Important
- [ ] Withdrawal system for owners
- [ ] SMS notifications
- [ ] Ad upload with file storage
- [ ] Campaign approval workflow
- [ ] Revenue reports export

### P2 - Nice to Have
- [ ] Equipment shop integration
- [ ] Documentation pages
- [ ] Support ticket system
- [ ] Mobile app (React Native)
- [ ] Real-time session monitoring

---

## Next Tasks
1. Integrate real M-Pesa Daraja API
2. Implement MikroTik RADIUS server connection
3. Add withdrawal/payout functionality
4. Build ad file upload system
5. Create admin campaign approval flow
