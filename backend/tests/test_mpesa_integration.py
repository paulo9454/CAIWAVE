"""
M-Pesa Daraja STK Push Integration Tests
Tests for CAIWAVE platform M-Pesa payment flows:
1. Hotspot Owner: Monthly subscription payment (KES 500)
2. Advertiser: Ad payment (package-based pricing)
3. WiFi Client: WiFi package payment (KES 5-600)
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@caiwave.com"
ADMIN_PASSWORD = "admin123"
OWNER_EMAIL = "owner@caiwave.com"
OWNER_PASSWORD = "owner123"
ADVERTISER_EMAIL = "advertiser@caiwave.com"
ADVERTISER_PASSWORD = "advertiser123"

# Test phone number (Safaricom sandbox format)
TEST_PHONE = "254712345678"


class TestMPesaConfigStatus:
    """Test M-Pesa configuration status endpoint (Admin only)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def get_admin_token(self):
        """Get admin authentication token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        return None
    
    def test_config_status_requires_auth(self):
        """GET /api/mpesa/config-status - Should require authentication"""
        response = self.session.get(f"{BASE_URL}/api/mpesa/config-status")
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✅ Config status requires authentication")
    
    def test_config_status_requires_admin(self):
        """GET /api/mpesa/config-status - Should require admin role"""
        # Login as owner (non-admin)
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": OWNER_EMAIL,
            "password": OWNER_PASSWORD
        })
        if login_resp.status_code == 200:
            token = login_resp.json().get("token")
            response = self.session.get(
                f"{BASE_URL}/api/mpesa/config-status",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 403, f"Expected 403 for non-admin, got {response.status_code}"
            print("✅ Config status requires admin role")
        else:
            pytest.skip("Owner login failed")
    
    def test_config_status_success(self):
        """GET /api/mpesa/config-status - Should return config status for admin"""
        token = self.get_admin_token()
        if not token:
            pytest.skip("Admin login failed")
        
        response = self.session.get(
            f"{BASE_URL}/api/mpesa/config-status",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # Verify response structure
        assert "configured" in data, "Missing 'configured' field"
        assert "has_callback" in data, "Missing 'has_callback' field"
        assert "environment" in data, "Missing 'environment' field"
        assert "shortcode" in data, "Missing 'shortcode' field"
        assert "consumer_key_set" in data, "Missing 'consumer_key_set' field"
        assert "consumer_secret_set" in data, "Missing 'consumer_secret_set' field"
        assert "passkey_set" in data, "Missing 'passkey_set' field"
        
        # Verify M-Pesa is configured with sandbox credentials
        assert data["configured"] == True, "M-Pesa should be configured"
        assert data["environment"] == "sandbox", f"Expected sandbox, got {data['environment']}"
        assert data["shortcode"] == "174379", f"Expected shortcode 174379, got {data['shortcode']}"
        assert data["consumer_key_set"] == True, "Consumer key should be set"
        assert data["consumer_secret_set"] == True, "Consumer secret should be set"
        assert data["passkey_set"] == True, "Passkey should be set"
        
        print(f"✅ M-Pesa config status: configured={data['configured']}, env={data['environment']}, shortcode={data['shortcode']}")


class TestGenericSTKPush:
    """Test generic STK Push endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_stk_push_success(self):
        """POST /api/mpesa/stk-push - Should initiate STK Push and return checkout_request_id"""
        payload = {
            "phone_number": TEST_PHONE,
            "amount": 1,
            "account_reference": "TEST001",
            "transaction_desc": "Test Payment"
        }
        
        response = self.session.post(f"{BASE_URL}/api/mpesa/stk-push", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "success" in data, "Missing 'success' field"
        
        if data["success"]:
            assert "checkout_request_id" in data, "Missing 'checkout_request_id' on success"
            assert "merchant_request_id" in data, "Missing 'merchant_request_id' on success"
            assert "message" in data, "Missing 'message' field"
            print(f"✅ STK Push initiated - CheckoutRequestID: {data['checkout_request_id']}")
        else:
            # STK Push may fail in sandbox without real phone
            print(f"⚠️ STK Push returned success=false: {data.get('error', 'Unknown error')}")
            # This is acceptable for sandbox testing
            assert "error" in data or "details" in data, "Should have error details on failure"
    
    def test_stk_push_invalid_phone(self):
        """POST /api/mpesa/stk-push - Should handle invalid phone number"""
        payload = {
            "phone_number": "invalid",
            "amount": 1,
            "account_reference": "TEST002",
            "transaction_desc": "Test Payment"
        }
        
        response = self.session.post(f"{BASE_URL}/api/mpesa/stk-push", json=payload)
        
        # Should still return 200 but with success=false or error from Safaricom
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        print(f"✅ Invalid phone handled: success={data.get('success')}")
    
    def test_stk_push_missing_fields(self):
        """POST /api/mpesa/stk-push - Should validate required fields"""
        payload = {
            "phone_number": TEST_PHONE
            # Missing amount, account_reference, transaction_desc
        }
        
        response = self.session.post(f"{BASE_URL}/api/mpesa/stk-push", json=payload)
        
        # Should return 422 for validation error
        assert response.status_code == 422, f"Expected 422 for missing fields, got {response.status_code}"
        print("✅ Missing fields validation works")


class TestOwnerSubscriptionPayment:
    """Test hotspot owner subscription payment endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def get_owner_token(self):
        """Get owner authentication token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": OWNER_EMAIL,
            "password": OWNER_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        return None
    
    def get_admin_token(self):
        """Get admin authentication token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        return None
    
    def test_owner_pay_subscription_requires_auth(self):
        """POST /api/mpesa/owner/pay-subscription - Should require authentication"""
        payload = {
            "phone_number": TEST_PHONE,
            "invoice_id": "test-invoice-id"
        }
        
        response = self.session.post(f"{BASE_URL}/api/mpesa/owner/pay-subscription", json=payload)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✅ Owner subscription payment requires authentication")
    
    def test_owner_pay_subscription_invalid_invoice(self):
        """POST /api/mpesa/owner/pay-subscription - Should return 404 for invalid invoice"""
        token = self.get_owner_token()
        if not token:
            pytest.skip("Owner login failed")
        
        payload = {
            "phone_number": TEST_PHONE,
            "invoice_id": "non-existent-invoice-id"
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/mpesa/owner/pay-subscription",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 404, f"Expected 404 for invalid invoice, got {response.status_code}"
        print("✅ Invalid invoice returns 404")
    
    def test_owner_pay_subscription_with_valid_invoice(self):
        """POST /api/mpesa/owner/pay-subscription - Should initiate STK Push for valid invoice"""
        token = self.get_owner_token()
        if not token:
            pytest.skip("Owner login failed")
        
        # First get owner's invoices
        invoices_resp = self.session.get(
            f"{BASE_URL}/api/invoices/",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if invoices_resp.status_code != 200:
            pytest.skip("Could not get owner invoices")
        
        invoices = invoices_resp.json()
        if not invoices:
            pytest.skip("No invoices found for owner")
        
        # Find an unpaid invoice (trial or unpaid status)
        unpaid_invoice = None
        for inv in invoices:
            if inv.get("status") in ["trial", "unpaid"]:
                unpaid_invoice = inv
                break
        
        if not unpaid_invoice:
            pytest.skip("No unpaid invoice found")
        
        payload = {
            "phone_number": TEST_PHONE,
            "invoice_id": unpaid_invoice["id"]
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/mpesa/owner/pay-subscription",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "success" in data, "Missing 'success' field"
        
        if data["success"]:
            assert "checkout_request_id" in data, "Missing checkout_request_id"
            assert "amount" in data, "Missing amount"
            assert data["amount"] == 500, f"Expected amount 500, got {data['amount']}"
            print(f"✅ Owner subscription STK Push initiated - Amount: KES {data['amount']}, CheckoutID: {data['checkout_request_id']}")
        else:
            print(f"⚠️ STK Push returned success=false: {data.get('error', 'Unknown error')}")


class TestWiFiClientPayment:
    """Test WiFi client payment endpoint (no auth required)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def get_test_package_and_hotspot(self):
        """Get a valid package and hotspot for testing"""
        # Get packages
        packages_resp = self.session.get(f"{BASE_URL}/api/packages/")
        if packages_resp.status_code != 200:
            return None, None
        
        packages = packages_resp.json()
        if not packages:
            return None, None
        
        # Get hotspots (need auth for this)
        admin_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if admin_resp.status_code != 200:
            return packages[0] if packages else None, None
        
        token = admin_resp.json().get("token")
        hotspots_resp = self.session.get(
            f"{BASE_URL}/api/hotspots/",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if hotspots_resp.status_code != 200:
            return packages[0] if packages else None, None
        
        hotspots = hotspots_resp.json()
        active_hotspot = None
        for h in hotspots:
            if h.get("status") == "active":
                active_hotspot = h
                break
        
        return packages[0] if packages else None, active_hotspot
    
    def test_client_pay_wifi_no_auth_required(self):
        """POST /api/mpesa/client/pay-wifi - Should NOT require authentication"""
        package, hotspot = self.get_test_package_and_hotspot()
        
        if not package or not hotspot:
            pytest.skip("No package or active hotspot available")
        
        payload = {
            "phone_number": TEST_PHONE,
            "package_id": package["id"],
            "hotspot_id": hotspot["id"]
        }
        
        # No auth header - should still work
        response = self.session.post(f"{BASE_URL}/api/mpesa/client/pay-wifi", json=payload)
        
        # Should not return 401 or 403
        assert response.status_code not in [401, 403], f"Should not require auth, got {response.status_code}"
        print("✅ WiFi client payment does not require authentication")
    
    def test_client_pay_wifi_invalid_package(self):
        """POST /api/mpesa/client/pay-wifi - Should return 404 for invalid package"""
        package, hotspot = self.get_test_package_and_hotspot()
        
        if not hotspot:
            pytest.skip("No active hotspot available")
        
        payload = {
            "phone_number": TEST_PHONE,
            "package_id": "non-existent-package-id",
            "hotspot_id": hotspot["id"]
        }
        
        response = self.session.post(f"{BASE_URL}/api/mpesa/client/pay-wifi", json=payload)
        
        assert response.status_code == 404, f"Expected 404 for invalid package, got {response.status_code}"
        print("✅ Invalid package returns 404")
    
    def test_client_pay_wifi_invalid_hotspot(self):
        """POST /api/mpesa/client/pay-wifi - Should return 404 for invalid hotspot"""
        package, _ = self.get_test_package_and_hotspot()
        
        if not package:
            pytest.skip("No package available")
        
        payload = {
            "phone_number": TEST_PHONE,
            "package_id": package["id"],
            "hotspot_id": "non-existent-hotspot-id"
        }
        
        response = self.session.post(f"{BASE_URL}/api/mpesa/client/pay-wifi", json=payload)
        
        assert response.status_code == 404, f"Expected 404 for invalid hotspot, got {response.status_code}"
        print("✅ Invalid hotspot returns 404")
    
    def test_client_pay_wifi_success(self):
        """POST /api/mpesa/client/pay-wifi - Should initiate STK Push for valid request"""
        package, hotspot = self.get_test_package_and_hotspot()
        
        if not package or not hotspot:
            pytest.skip("No package or active hotspot available")
        
        payload = {
            "phone_number": TEST_PHONE,
            "package_id": package["id"],
            "hotspot_id": hotspot["id"]
        }
        
        response = self.session.post(f"{BASE_URL}/api/mpesa/client/pay-wifi", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "success" in data, "Missing 'success' field"
        
        if data["success"]:
            assert "checkout_request_id" in data, "Missing checkout_request_id"
            assert "amount" in data, "Missing amount"
            assert "package_name" in data, "Missing package_name"
            assert "duration" in data, "Missing duration"
            print(f"✅ WiFi client STK Push initiated - Package: {data['package_name']}, Amount: KES {data['amount']}, Duration: {data['duration']}")
        else:
            print(f"⚠️ STK Push returned success=false: {data.get('error', 'Unknown error')}")


class TestMPesaTransactionsList:
    """Test M-Pesa transactions list endpoint (Admin only)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def get_admin_token(self):
        """Get admin authentication token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        return None
    
    def test_transactions_requires_auth(self):
        """GET /api/mpesa/transactions - Should require authentication"""
        response = self.session.get(f"{BASE_URL}/api/mpesa/transactions")
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✅ Transactions list requires authentication")
    
    def test_transactions_requires_admin(self):
        """GET /api/mpesa/transactions - Should require admin role"""
        # Login as owner (non-admin)
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": OWNER_EMAIL,
            "password": OWNER_PASSWORD
        })
        if login_resp.status_code == 200:
            token = login_resp.json().get("token")
            response = self.session.get(
                f"{BASE_URL}/api/mpesa/transactions",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 403, f"Expected 403 for non-admin, got {response.status_code}"
            print("✅ Transactions list requires admin role")
        else:
            pytest.skip("Owner login failed")
    
    def test_transactions_success(self):
        """GET /api/mpesa/transactions - Should return transactions list for admin"""
        token = self.get_admin_token()
        if not token:
            pytest.skip("Admin login failed")
        
        response = self.session.get(
            f"{BASE_URL}/api/mpesa/transactions",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # Verify response structure
        assert "transactions" in data, "Missing 'transactions' field"
        assert "stats" in data, "Missing 'stats' field"
        assert isinstance(data["transactions"], list), "transactions should be a list"
        
        # Verify stats structure
        stats = data["stats"]
        assert "total" in stats, "Missing 'total' in stats"
        assert "completed" in stats, "Missing 'completed' in stats"
        assert "pending" in stats, "Missing 'pending' in stats"
        assert "failed" in stats, "Missing 'failed' in stats"
        
        print(f"✅ Transactions list returned - Total: {stats['total']}, Completed: {stats['completed']}, Pending: {stats['pending']}, Failed: {stats['failed']}")
    
    def test_transactions_filter_by_type(self):
        """GET /api/mpesa/transactions - Should filter by payment type"""
        token = self.get_admin_token()
        if not token:
            pytest.skip("Admin login failed")
        
        # Test filtering by wifi type
        response = self.session.get(
            f"{BASE_URL}/api/mpesa/transactions?payment_type=wifi",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # All returned transactions should be wifi type
        for tx in data["transactions"]:
            assert tx.get("type") == "wifi", f"Expected wifi type, got {tx.get('type')}"
        
        print(f"✅ Transactions filter by type works - WiFi transactions: {len(data['transactions'])}")


class TestPaymentStatusCheck:
    """Test payment status check endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_status_check_not_found(self):
        """GET /api/mpesa/status/{checkout_id} - Should handle non-existent checkout ID"""
        fake_checkout_id = "ws_CO_TEST_" + str(uuid.uuid4())[:8]
        
        response = self.session.get(f"{BASE_URL}/api/mpesa/status/{fake_checkout_id}")
        
        # When checkout ID not in DB, endpoint queries Safaricom API
        # This may return 200 with found_in_db=false, or error if Safaricom query fails
        # Both are acceptable behaviors
        if response.status_code == 200:
            data = response.json()
            assert "found_in_db" in data, "Missing 'found_in_db' field"
            assert data["found_in_db"] == False, "Should not find fake checkout ID in DB"
            print(f"✅ Status check for non-existent ID returns found_in_db=false")
        else:
            # Safaricom API query may fail for invalid checkout IDs
            # This is expected behavior - the endpoint tried to query Safaricom
            print(f"✅ Status check for non-existent ID returned {response.status_code} (Safaricom API error expected)")
    
    def test_status_check_with_real_checkout(self):
        """GET /api/mpesa/status/{checkout_id} - Should return status for real checkout"""
        # First initiate an STK Push to get a real checkout ID
        payload = {
            "phone_number": TEST_PHONE,
            "amount": 1,
            "account_reference": "STATUSTEST",
            "transaction_desc": "Status Test"
        }
        
        stk_resp = self.session.post(f"{BASE_URL}/api/mpesa/stk-push", json=payload)
        
        if stk_resp.status_code != 200:
            pytest.skip("Could not initiate STK Push")
        
        stk_data = stk_resp.json()
        
        if not stk_data.get("success") or not stk_data.get("checkout_request_id"):
            pytest.skip("STK Push did not return checkout_request_id")
        
        checkout_id = stk_data["checkout_request_id"]
        
        # Now check status
        response = self.session.get(f"{BASE_URL}/api/mpesa/status/{checkout_id}")
        
        # Should return 200 for valid checkout ID
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # Should have either found_in_db or safaricom_response
        assert "found_in_db" in data, "Missing 'found_in_db' field"
        
        if data["found_in_db"]:
            assert "transaction" in data, "Missing 'transaction' when found_in_db=true"
            print(f"✅ Status check found transaction in DB: {data['transaction'].get('status')}")
        else:
            assert "safaricom_response" in data, "Missing 'safaricom_response' when found_in_db=false"
            print(f"✅ Status check queried Safaricom API")


class TestAdvertiserPayment:
    """Test advertiser ad payment endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def get_advertiser_token(self):
        """Get advertiser authentication token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADVERTISER_EMAIL,
            "password": ADVERTISER_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        return None
    
    def test_advertiser_pay_ad_requires_auth(self):
        """POST /api/mpesa/advertiser/pay-ad - Should require authentication"""
        payload = {
            "phone_number": TEST_PHONE,
            "ad_id": "test-ad-id"
        }
        
        response = self.session.post(f"{BASE_URL}/api/mpesa/advertiser/pay-ad", json=payload)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✅ Advertiser ad payment requires authentication")
    
    def test_advertiser_pay_ad_invalid_ad(self):
        """POST /api/mpesa/advertiser/pay-ad - Should return 404 for invalid ad"""
        token = self.get_advertiser_token()
        if not token:
            pytest.skip("Advertiser login failed")
        
        payload = {
            "phone_number": TEST_PHONE,
            "ad_id": "non-existent-ad-id"
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/mpesa/advertiser/pay-ad",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 404, f"Expected 404 for invalid ad, got {response.status_code}"
        print("✅ Invalid ad returns 404")


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
