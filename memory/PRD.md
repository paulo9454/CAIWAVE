# CAITECH Wi-Fi Hotspot Billing Platform - PRD v2.0

## Project Overview
Production-ready Wi-Fi hotspot billing platform with integrated advertising engine, managed exclusively by CAITECH as Super Admin. Features real M-Pesa integration, FreeRADIUS support, and dynamic revenue sharing.

## Branding (LOCKED)
- **Logo**: Blue (#0032FA) background with white WiFi signal icon
- **Mandatory Footer**: "Powered by CAITECH © 2026. All Rights Reserved."
- Partners cannot remove or modify branding

## Target Users
1. **Super Admin (CAITECH)** - Full platform control, ad approval, revenue settings
2. **Hotspot Owner (Partner)** - ISP dashboard, assisted setup, no monthly fees
3. **Advertiser** - Ad submission (requires admin approval)
4. **End User** - WiFi purchase via captive portal

## Core Requirements (Static)
- Package pricing is PREDEFINED (no custom pricing)
- All ads MUST be approved by CAITECH admin
- Dynamic revenue sharing (NOT fixed 70/30)
- Real M-Pesa Daraja integration (sandbox-ready)
- Real FreeRADIUS structure (MikroTik-compatible)
- SMS/WhatsApp notification support

## Package Pricing (FIXED)
| Duration | Price (KES) |
|----------|-------------|
| 30 min   | 5           |
| 4 hours  | 15          |
| 8 hours  | 25          |
| 12 hours | 30          |
| 24 hours | 35          |
| 1 week   | 200         |
| 1 month  | 600         |

## Tech Stack
- **Backend**: FastAPI + Python
- **Frontend**: React + TailwindCSS
- **Database**: MongoDB
- **Auth**: JWT-based multi-role
- **Payments**: M-Pesa Daraja API (real)
- **Router**: MikroTik via FreeRADIUS
- **SMS**: Africa's Talking / Centipid
- **WhatsApp**: Twilio

---

## What's Been Implemented (v2.0 - Feb 2026)

### Backend Features
- [x] Multi-role authentication (JWT)
- [x] New package pricing (KES 5-600)
- [x] Dynamic revenue sharing formula
- [x] Ad approval workflow (pending → approved/rejected)
- [x] Real M-Pesa Daraja STK Push integration structure
- [x] M-Pesa callback handling
- [x] SMS service (Africa's Talking / Centipid)
- [x] WhatsApp service (Twilio)
- [x] Voucher generation and redemption
- [x] RADIUS credential generation
- [x] Session management with expiry
- [x] Hotspot status management (admin can suspend)
- [x] Revenue configuration API
- [x] Integration status endpoints

### Frontend Features
- [x] Landing page with new pricing
- [x] Captive portal (mobile-first)
- [x] Admin Dashboard with:
  - Ad Approval workflow
  - Revenue Settings configuration
  - Integration status monitoring
  - Hotspot suspension controls
- [x] Owner Dashboard
- [x] Advertiser Dashboard
- [x] Mandatory CAITECH branding/footer

### Ad Approval Workflow
1. Advertiser creates ad → Status: PENDING
2. Admin reviews in Ad Approval page
3. Admin approves → Status: APPROVED, is_active: true
4. OR Admin rejects → Status: REJECTED with reason
5. Admin can later suspend approved ads

### Dynamic Revenue Formula
```
Partner % = Base + Coverage Bonus + Client Bonus + Ad Bonus + Uptime Bonus
```
- **Base: 30%** (configurable)
- Coverage: +0.5% per 100 sqm (max +5%)
- Clients: +0.5% per 10 daily clients (max +5%)
- Ads: +1% per 1000 impressions delivered (max +5%)
- Uptime: +2% if ≥99% uptime
- **Max cap: 50%** (configurable)

**Revenue Split:**
- Partner receives: 30% - 50% (depending on bonuses)
- CAITECH receives: 50% - 70%

---

## Integration Setup Instructions

### M-Pesa Daraja API
1. Register at https://developer.safaricom.co.ke/
2. Create sandbox app
3. Add to backend/.env:
```
MPESA_CONSUMER_KEY=your_key
MPESA_CONSUMER_SECRET=your_secret
MPESA_SHORTCODE=your_shortcode
MPESA_PASSKEY=your_passkey
MPESA_CALLBACK_URL=https://your-domain/api/mpesa/callback
```

### SMS (Africa's Talking)
1. Register at https://account.africastalking.com/
2. Add to backend/.env:
```
SMS_PROVIDER=africas_talking
SMS_API_KEY=your_api_key
SMS_USERNAME=your_username
SMS_SENDER_ID=CAITECH
```

### WhatsApp (Twilio)
1. Get credentials from https://www.twilio.com/console
2. Enable WhatsApp sandbox
3. Add to backend/.env:
```
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_NUMBER=+14155238886
```

---

## Prioritized Backlog

### P0 - Critical (Next Sprint)
- [ ] Add M-Pesa production credentials
- [ ] FreeRADIUS server deployment
- [ ] MikroTik router connection testing

### P1 - Important
- [ ] Withdrawal system for partners
- [ ] Ad file upload (images/videos)
- [ ] SMS balance tracking
- [ ] Voucher printing UI
- [ ] Equipment marketplace management

### P2 - Nice to Have
- [ ] Real-time session monitoring
- [ ] Revenue reports export
- [ ] Mobile app (React Native)
- [ ] Email notifications

---

## Credentials
- **Admin**: admin@caitech.com / admin123

## Next Tasks
1. Add real M-Pesa Daraja credentials
2. Deploy FreeRADIUS server
3. Test with MikroTik router
4. Configure SMS gateway
5. Add Twilio WhatsApp credentials
