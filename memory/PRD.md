# CAIWAVE Wi-Fi Hotspot Billing Platform - PRD v3.0

## Project Overview
Production-ready Wi-Fi hotspot billing, advertising, and premium live access platform (CAIWAVE). Features ISP-grade MikroTik integration, integrated advertising engine, admin-controlled campaigns, and CAIWAVE TV streaming service.

## Branding (LOCKED - Updated Feb 2026)
- **Brand Name**: CAIWAVE
- **Logo**: Blue (#0032FA) background with white WiFi signal icon + "C" letter at center
- **Mandatory Footer**: "Powered by CAIWAVE WiFi © 2026. All Rights Reserved."
- Partners cannot remove or modify branding

## Target Users
1. **Super Admin (CAIWAVE)** - Full platform control, ad approval, campaign management, CAIWAVE TV control
2. **Hotspot Owner (Partner)** - ISP dashboard, assisted setup, no monthly fees
3. **Advertiser** - Ad submission only (requires admin approval, NO campaign creation)
4. **End User** - WiFi purchase via captive portal, stream access

## Core Platform Philosophy
- Plug-and-play for partners
- Centralized control by CAIWAVE
- Verified & trusted advertising
- No monthly fees
- No uncontrolled free internet
- Revenue scales with usage

## Core Requirements (Static)
- Package pricing is PREDEFINED (no custom pricing)
- All ads MUST be approved by CAIWAVE admin
- Campaigns are ADMIN-ONLY (advertisers create ads, not campaigns)
- Dynamic revenue sharing (NOT fixed percentages)
- Real M-Pesa Daraja integration
- Real FreeRADIUS structure (MikroTik-compatible)
- SMS/WhatsApp notification support
- CAIWAVE TV for premium live streaming

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
- **Frontend**: React + TailwindCSS + Shadcn UI
- **Database**: MongoDB
- **Auth**: JWT-based multi-role
- **Payments**: M-Pesa Daraja API (real)
- **Router**: MikroTik via FreeRADIUS
- **SMS**: Flexible gateway (Africa's Talking / Centipid)
- **WhatsApp**: Twilio

---

## What's Been Implemented (v3.0 - Feb 2026)

### Phase 1: Branding Rebrand ✅ COMPLETE
- Rebranded from CAITECH to CAIWAVE
- New logo with WiFi icon + "C" letter center
- Updated all UI components (LandingPage, LoginPage, RegisterPage, CaptivePortal)
- Updated Admin, Owner, and Advertiser dashboards
- Updated footer across all pages
- Updated backend seed data and SMS messages
- New admin credentials: admin@caiwave.com / admin123

### Backend Features
- FastAPI with JWT authentication
- MongoDB database with Mongoose-like models
- Package management (7 predefined packages)
- Dynamic revenue configuration (30% base, 50% max cap)
- Ad submission and approval workflow
- Hotspot management
- Payment tracking
- Session management structure

### Frontend Features  
- Dark theme UI with modern design
- Landing page with all sections
- Login/Register pages
- Admin Dashboard with:
  - Ad Approval section
  - Package management
  - Revenue settings (dynamic calculation)
  - Hotspot management
  - Integration settings
- Owner Dashboard with:
  - Hotspot management
  - Payment history
  - Analytics
- Advertiser Dashboard with:
  - Ad creation
  - Campaign management
  - Performance tracking
- Captive Portal for end users

### API Endpoints
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `GET /api/packages` - List packages
- `GET /api/settings/revenue-config` - Revenue settings
- `PUT /api/settings/revenue-config` - Update revenue
- `GET /api/ads/pending` - Pending ads (admin)
- `POST /api/ads/{id}/approve` - Approve/reject ads
- `GET /api/hotspots` - List hotspots
- `POST /api/hotspots` - Create hotspot
- `GET /api/portal/{hotspot_id}` - Captive portal data
- `POST /api/seed` - Seed database

---

## Upcoming Tasks (Priority Order)

### Phase 2: Core Features (NEXT)
1. **Admin-Only Campaigns System**
   - Create Campaign model (admin-only creation)
   - Campaign controls: dates, regions, assigned ads
   - Link campaigns to CAIWAVE TV streams
   - Link campaigns to subsidized uptime

2. **Ads vs Campaigns Distinction**
   - Ads: Created by Advertisers → Pending → Approved → Paid → Active
   - Campaigns: Admin-only containers for approved ads
   - Payment integration for ad activation

3. **CAIWAVE TV Section**
   - Admin creates/manages streams
   - Stream config: name, URL, start/end time, access type
   - Access types: Free, Discounted, Sponsored
   - Ads display before stream access

4. **Subsidized/Discounted Uptime**
   - Admin-controlled cheaper rates (e.g., KES 15 → 25 hours)
   - Time-limited, region-limited
   - Event-based activation

### Phase 3: Integrations
1. **M-Pesa Daraja Integration**
   - STK Push for payments
   - Callback handling
   - Payment status tracking
   - Sandbox environment setup

2. **MikroTik RADIUS Integration**
   - FreeRADIUS setup
   - Auto-generated router config
   - Session control
   - IP bindings

3. **SMS Gateway Architecture**
   - Flexible provider selection
   - Africa's Talking support
   - Payment confirmations
   - Session alerts

4. **WhatsApp Notifications (Twilio)**
   - Business notifications
   - Session reminders

### Future Tasks (Backlog)
- Partner Onboarding Wizard
- Voucher Printing System
- Equipment Marketplace UI
- System Audit Logs
- Two-Factor Authentication (2FA)
- MikroTik network rules for streaming domains

---

## Key Database Schemas

### User
```javascript
{
  name: String,
  email: String (unique),
  password: String (hashed),
  role: ['super_admin', 'hotspot_owner', 'advertiser', 'end_user'],
  phone: String,
  is_active: Boolean
}
```

### Package
```javascript
{
  name: String,
  price: Number,
  duration_minutes: Number,
  speed_mbps: Number,
  is_active: Boolean
}
```

### Ad
```javascript
{
  title: String,
  ad_type: ['image', 'video', 'text', 'link'],
  content_url: String,
  text_content: String,
  status: ['pending', 'approved', 'rejected', 'suspended'],
  advertiser_id: ObjectId,
  impressions: Number,
  clicks: Number
}
```

### Campaign (TO BE IMPLEMENTED)
```javascript
{
  name: String,
  status: ['draft', 'active', 'paused', 'completed'],
  start_date: Date,
  end_date: Date,
  target_regions: [String],
  target_hotspots: [ObjectId],
  assigned_ads: [ObjectId],
  stream_id: ObjectId (optional),
  subsidized_uptime_id: ObjectId (optional),
  created_by: ObjectId (admin only)
}
```

### Stream (TO BE IMPLEMENTED)
```javascript
{
  name: String,
  stream_url: String,
  start_time: Date,
  end_time: Date,
  access_type: ['free', 'discounted', 'sponsored'],
  allowed_hotspots: [ObjectId],
  pre_roll_ads: [ObjectId],
  is_active: Boolean
}
```

---

## Credentials
- **Admin**: admin@caiwave.com / admin123
- **Demo Portal**: /portal/demo

## Files Reference
- **Logo**: `/app/frontend/public/logo.svg`
- **Logo Component**: `/app/frontend/src/components/CaiwaveLogo.jsx`
- **Admin Dashboard**: `/app/frontend/src/pages/admin/Dashboard.jsx`
- **Owner Dashboard**: `/app/frontend/src/pages/owner/Dashboard.jsx`
- **Advertiser Dashboard**: `/app/frontend/src/pages/advertiser/Dashboard.jsx`
- **Captive Portal**: `/app/frontend/src/pages/CaptivePortal.jsx`
- **Backend Server**: `/app/backend/server.py`
