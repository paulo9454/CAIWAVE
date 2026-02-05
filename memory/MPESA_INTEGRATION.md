# CAIWAVE M-Pesa Integration Guide

## Overview

The CAIWAVE platform integrates M-Pesa Daraja API for three payment types:

| Role | Endpoint | Post-Payment Action |
|------|----------|---------------------|
| Hotspot Owner | `/api/mpesa/owner/pay-subscription` | Activates subscription |
| Advertiser | `/api/mpesa/advertiser/pay-ad` | Ad goes live |
| WiFi Client | `/api/mpesa/client/pay-wifi` | Grants WiFi access |

---

## Current Configuration (Sandbox)

The system is configured with Safaricom **sandbox** credentials:

```
MPESA_ENV=sandbox
MPESA_CONSUMER_KEY=7ONektuabEWBEDGNKM4UgvdBb9le0XdIG3Q0PMfHfqnq3MeM
MPESA_CONSUMER_SECRET=ujIPEkJIpeNtvv7dkGIQ29y9lz7fN3SDGyzLUbasGJAmkqNksldGSu7CgJ3vI7ni
MPESA_SHORTCODE=174379
MPESA_PASSKEY=bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919
```

---

## Testing M-Pesa in Sandbox

### Step 1: Set Up ngrok for Callbacks

M-Pesa callbacks require a publicly accessible HTTPS URL. Use ngrok:

```bash
# Install ngrok
# https://ngrok.com/download

# Expose your backend (port 8001)
ngrok http 8001
```

Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)

### Step 2: Configure Callback URL

Update `/app/backend/.env`:

```
MPESA_CALLBACK_URL=https://abc123.ngrok.io/api/mpesa/callback
```

Restart backend:
```bash
sudo supervisorctl restart backend
```

### Step 3: Test STK Push

**Generic STK Push Test:**
```bash
curl -X POST "https://your-domain/api/mpesa/stk-push" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "254712345678",
    "amount": 1,
    "account_reference": "TEST001",
    "transaction_desc": "Test Payment"
  }'
```

**Owner Subscription Payment:**
```bash
curl -X POST "https://your-domain/api/mpesa/owner/pay-subscription" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {token}" \
  -d '{
    "phone_number": "254715669244",
    "invoice_id": "{invoice_id}"
  }'
```

**WiFi Client Payment (no auth required):**
```bash
curl -X POST "https://your-domain/api/mpesa/client/pay-wifi" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "254712345678",
    "package_id": "{package_id}",
    "hotspot_id": "{hotspot_id}"
  }'
```

### Step 4: Monitor Callbacks

1. Open ngrok dashboard: http://127.0.0.1:4040
2. Watch for POST requests to `/api/mpesa/callback`
3. Check transaction status:

```bash
curl "https://your-domain/api/mpesa/status/{checkout_request_id}"
```

---

## Switching to Production

### Step 1: Get Production Credentials

1. Register at https://developer.safaricom.co.ke/
2. Create a production app
3. Get approved for STK Push (Lipa Na M-Pesa)

### Step 2: Update Configuration

Edit `/app/backend/.env`:

```env
# Switch to production
MPESA_ENV=production

# Production Credentials
MPESA_CONSUMER_KEY=your_production_consumer_key
MPESA_CONSUMER_SECRET=your_production_consumer_secret
MPESA_SHORTCODE=6386009
MPESA_PASSKEY=your_production_passkey

# Production Callback (your actual domain)
MPESA_CALLBACK_URL=https://your-production-domain.com/api/mpesa/callback

# Production business details
MPESA_TILL_NUMBER=8573842
MPESA_OPERATOR_ID=PM
MPESA_BUSINESS_PHONE=0715669244
```

### Step 3: Restart and Test

```bash
sudo supervisorctl restart backend
```

Test with small amounts first!

---

## API Endpoints Reference

### Payment Initiation

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/mpesa/stk-push` | POST | No | Generic STK Push |
| `/api/mpesa/owner/pay-subscription` | POST | Owner/Admin | Pay subscription |
| `/api/mpesa/advertiser/pay-ad` | POST | Advertiser/Admin | Pay for ad |
| `/api/mpesa/client/pay-wifi` | POST | No | Pay for WiFi |

### Callback & Status

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/mpesa/callback` | POST | No | Safaricom callback |
| `/api/mpesa/status/{checkout_id}` | GET | No | Check payment status |
| `/api/mpesa/transaction/{id}` | GET | No | Get transaction details |
| `/api/mpesa/wifi-credentials/{checkout_id}` | GET | No | Get WiFi credentials |
| `/api/mpesa/transactions` | GET | Admin | List all transactions |
| `/api/mpesa/config-status` | GET | Admin | Check M-Pesa config |

---

## Troubleshooting

### "M-Pesa not configured"
- Check that all credentials are set in `/app/backend/.env`
- Restart backend after changes

### "Failed to get access token"
- Verify consumer key and secret
- Check if using correct environment (sandbox vs production)

### "Callback not received"
- Ensure ngrok is running and callback URL is set
- Check ngrok dashboard for incoming requests
- Verify the callback URL doesn't have trailing slash issues

### "Payment timeout"
- Sandbox has longer processing times
- In production, ensure good network connectivity

---

## Production Checklist

- [ ] Get production API credentials from Safaricom
- [ ] Update `.env` with production values
- [ ] Set up SSL/HTTPS for your domain
- [ ] Configure production callback URL
- [ ] Test with small amounts
- [ ] Monitor first few live transactions
- [ ] Set up error alerting for failed callbacks

---

## Contact

For M-Pesa integration support:
- Safaricom Developer Portal: https://developer.safaricom.co.ke/
- M-Pesa API Support: daraja@safaricom.co.ke
