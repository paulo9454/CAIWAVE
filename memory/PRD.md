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

### Phase 2: Admin Campaigns + CAIWAVE TV ✅ COMPLETE
- **Campaigns System (Admin Only)**
  - Full CRUD for campaigns
  - Campaign status management (draft, scheduled, active, paused, completed)
  - Target regions and hotspots
  - Assigned ads linking
  - Performance tracking (impressions, clicks)
  
- **CAIWAVE TV Streams (Admin Only)**
  - Full CRUD for live streams
  - Stream scheduling (start/end times)
  - Access types: free, discounted, sponsored, paid
  - Regional access control
  - View tracking
  - Live status indicator
  
- **Subsidized Uptime (Admin Only)**
  - Full CRUD for subsidized offers
  - Original vs discounted pricing
  - Time-limited offers (date range)
  - Daily time windows (optional)
  - Max uses limit (optional)
  - Regional targeting
  - Usage tracking
  
- **Landing Page Updates**
  - Added CAIWAVE TV navigation link
  - Added CAIWAVE TV section with features
  - Added broadcast CTA for events

### Backend Features
- FastAPI with JWT authentication
- MongoDB database with Mongoose-like models
- Package management (7 predefined packages)
- Dynamic revenue configuration (30% base, 50% max cap)
- Ad submission and approval workflow
- Hotspot management
- Payment tracking
- Session management structure
- **NEW**: Campaign management APIs
- **NEW**: Stream management APIs
- **NEW**: Subsidized uptime APIs

### Frontend Features  
- Dark theme UI with modern design
- Landing page with all sections + CAIWAVE TV
- Login/Register pages
- Admin Dashboard with:
  - Overview
  - **Campaigns** (NEW)
  - **CAIWAVE TV** (NEW)
  - **Subsidized Uptime** (NEW)
  - Ad Approval
  - Package management
  - Revenue settings
  - Hotspot management
  - Integration settings
- Owner Dashboard
- Advertiser Dashboard
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
- **NEW Campaigns**:
  - `GET /api/campaigns/` - List campaigns
  - `POST /api/campaigns/` - Create campaign
  - `PUT /api/campaigns/{id}` - Update campaign
  - `POST /api/campaigns/{id}/status` - Update status
  - `DELETE /api/campaigns/{id}` - Delete campaign
- **NEW Streams (CAIWAVE TV)**:
  - `GET /api/streams/` - List streams
  - `GET /api/streams/live` - Live streams (public)
  - `POST /api/streams/` - Create stream
  - `PUT /api/streams/{id}` - Update stream
  - `POST /api/streams/{id}/toggle` - Toggle active
  - `POST /api/streams/{id}/view` - Record view
  - `DELETE /api/streams/{id}` - Delete stream
- **NEW Subsidized Uptime**:
  - `GET /api/subsidized-uptime/` - List offers
  - `GET /api/subsidized-uptime/active` - Active offers (public)
  - `POST /api/subsidized-uptime/` - Create offer
  - `PUT /api/subsidized-uptime/{id}` - Update offer
  - `POST /api/subsidized-uptime/{id}/status` - Update status
  - `POST /api/subsidized-uptime/{id}/use` - Record use
  - `DELETE /api/subsidized-uptime/{id}` - Delete offer

---

## Upcoming Tasks (Priority Order)

### Phase 3: Integrations (NEXT)
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
- Link campaigns to streams and subsidized uptime
- Pre-roll ads for streams

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

### Campaign (IMPLEMENTED)
```javascript
{
  id: String,
  name: String,
  description: String,
  start_date: DateTime,
  end_date: DateTime,
  target_regions: [String],
  target_hotspot_ids: [String],
  assigned_ad_ids: [String],
  stream_id: String (optional),
  subsidized_uptime_id: String (optional),
  status: ['draft', 'scheduled', 'active', 'paused', 'completed'],
  created_by: String,
  total_impressions: Number,
  total_clicks: Number
}
```

### Stream (IMPLEMENTED)
```javascript
{
  id: String,
  name: String,
  description: String,
  stream_url: String,
  start_time: DateTime,
  end_time: DateTime,
  access_type: ['free', 'discounted', 'sponsored', 'paid'],
  price: Number,
  allowed_hotspot_ids: [String],
  allowed_regions: [String],
  pre_roll_ad_ids: [String],
  thumbnail_url: String,
  is_active: Boolean,
  total_views: Number,
  created_by: String
}
```

### SubsidizedUptime (IMPLEMENTED)
```javascript
{
  id: String,
  name: String,
  description: String,
  original_price: Number,
  discounted_price: Number,
  duration_hours: Number,
  start_date: DateTime,
  end_date: DateTime,
  daily_start_time: String,
  daily_end_time: String,
  allowed_hotspot_ids: [String],
  allowed_regions: [String],
  max_uses: Number,
  status: ['draft', 'scheduled', 'active', 'expired'],
  total_uses: Number,
  created_by: String
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
- **Landing Page**: `/app/frontend/src/pages/LandingPage.jsx`
- **Backend Server**: `/app/backend/server.py`
- **Auth Module**: `/app/frontend/src/lib/auth.js`
