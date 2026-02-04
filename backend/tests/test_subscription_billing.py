"""
Test Suite for Subscription & Billing System
Tests: Invoice APIs, Subscription Status, Admin Invoice Management
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestSubscriptionBillingSystem:
    """Test subscription and billing APIs"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.admin_email = "admin@caiwave.com"
        self.admin_password = "admin123"
        self.owner_email = "owner@caiwave.com"
        self.owner_password = "owner123"
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def get_admin_token(self):
        """Get admin authentication token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": self.admin_email,
            "password": self.admin_password
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    
    def get_owner_token(self):
        """Get owner authentication token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": self.owner_email,
            "password": self.owner_password
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    
    # ==================== Health Check ====================
    def test_health_check(self):
        """Test API health endpoint"""
        response = self.session.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✅ Health check passed")
    
    # ==================== Authentication Tests ====================
    def test_admin_login(self):
        """Test admin login"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": self.admin_email,
            "password": self.admin_password
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "super_admin"
        print("✅ Admin login successful")
    
    def test_owner_login(self):
        """Test owner login"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": self.owner_email,
            "password": self.owner_password
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "hotspot_owner"
        print("✅ Owner login successful")
    
    # ==================== Subscription Status API Tests ====================
    def test_subscription_status_requires_auth(self):
        """Test subscription status requires authentication"""
        response = self.session.get(f"{BASE_URL}/api/subscriptions/status")
        assert response.status_code == 401
        print("✅ Subscription status requires auth")
    
    def test_subscription_status_owner(self):
        """Test GET /api/subscriptions/status for owner"""
        token = self.get_owner_token()
        assert token is not None, "Owner login failed"
        
        response = self.session.get(
            f"{BASE_URL}/api/subscriptions/status",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "subscription_status" in data
        assert "trial_days_remaining" in data
        assert "hotspot_count" in data
        assert "monthly_fee" in data
        
        # Verify subscription status is valid
        valid_statuses = ["trial", "active", "grace_period", "suspended"]
        assert data["subscription_status"] in valid_statuses
        
        # Verify trial days is a number
        assert isinstance(data["trial_days_remaining"], int)
        assert data["trial_days_remaining"] >= 0
        
        print(f"✅ Subscription status: {data['subscription_status']}, Trial days: {data['trial_days_remaining']}")
    
    # ==================== Invoices API Tests ====================
    def test_invoices_requires_auth(self):
        """Test invoices endpoint requires authentication"""
        response = self.session.get(f"{BASE_URL}/api/invoices/")
        assert response.status_code == 401
        print("✅ Invoices endpoint requires auth")
    
    def test_invoices_owner(self):
        """Test GET /api/invoices/ for owner"""
        token = self.get_owner_token()
        assert token is not None, "Owner login failed"
        
        response = self.session.get(
            f"{BASE_URL}/api/invoices/",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Response should be a list
        assert isinstance(data, list)
        
        # If invoices exist, verify structure
        if len(data) > 0:
            invoice = data[0]
            assert "id" in invoice
            assert "invoice_number" in invoice
            assert "owner_id" in invoice
            assert "amount" in invoice
            assert "status" in invoice
            assert "due_date" in invoice
            
            # Verify status is valid
            valid_statuses = ["draft", "trial", "unpaid", "paid", "overdue"]
            assert invoice["status"] in valid_statuses
            
            print(f"✅ Owner has {len(data)} invoice(s), first status: {invoice['status']}")
        else:
            print("✅ Owner has no invoices yet")
    
    def test_current_invoice_owner(self):
        """Test GET /api/invoices/current for owner"""
        token = self.get_owner_token()
        assert token is not None, "Owner login failed"
        
        response = self.session.get(
            f"{BASE_URL}/api/invoices/current",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Response should have invoice and subscription_status
        if data.get("invoice"):
            assert "invoice_number" in data["invoice"]
            assert "amount" in data["invoice"]
            assert "status" in data["invoice"]
            print(f"✅ Current invoice: {data['invoice']['invoice_number']}")
        else:
            print("✅ No current invoice found")
    
    # ==================== Admin Invoice Management Tests ====================
    def test_admin_invoices_requires_admin(self):
        """Test admin invoices endpoint requires admin role"""
        # Test without auth
        response = self.session.get(f"{BASE_URL}/api/invoices/admin/all")
        assert response.status_code == 401
        
        # Test with owner token (should fail)
        owner_token = self.get_owner_token()
        response = self.session.get(
            f"{BASE_URL}/api/invoices/admin/all",
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        assert response.status_code == 403
        print("✅ Admin invoices requires admin role")
    
    def test_admin_get_all_invoices(self):
        """Test GET /api/invoices/admin/all for admin"""
        token = self.get_admin_token()
        assert token is not None, "Admin login failed"
        
        response = self.session.get(
            f"{BASE_URL}/api/invoices/admin/all",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "invoices" in data
        assert "stats" in data
        
        # Verify stats structure
        stats = data["stats"]
        assert "total" in stats
        assert "paid" in stats
        assert "trial" in stats
        assert "unpaid" in stats
        assert "overdue" in stats
        assert "total_revenue" in stats
        
        # Verify stats are numbers
        assert isinstance(stats["total"], int)
        assert isinstance(stats["total_revenue"], (int, float))
        
        print(f"✅ Admin invoices: Total={stats['total']}, Trial={stats['trial']}, Paid={stats['paid']}, Revenue=KES {stats['total_revenue']}")
    
    def test_admin_mark_paid_requires_admin(self):
        """Test mark paid endpoint requires admin role"""
        owner_token = self.get_owner_token()
        response = self.session.post(
            f"{BASE_URL}/api/invoices/admin/mark-paid/fake-id",
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        assert response.status_code == 403
        print("✅ Mark paid requires admin role")
    
    def test_admin_suspend_overdue_requires_admin(self):
        """Test suspend overdue endpoint requires admin role"""
        owner_token = self.get_owner_token()
        response = self.session.post(
            f"{BASE_URL}/api/invoices/admin/suspend-overdue",
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        assert response.status_code == 403
        print("✅ Suspend overdue requires admin role")
    
    # ==================== Start Trial Tests ====================
    def test_start_trial_requires_owner(self):
        """Test start trial requires owner role"""
        admin_token = self.get_admin_token()
        response = self.session.post(
            f"{BASE_URL}/api/subscriptions/start-trial",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # Admin should not be able to start trial (requires owner role)
        assert response.status_code == 403
        print("✅ Start trial requires owner role")
    
    # ==================== Invoice Payment Tests ====================
    def test_pay_invoice_requires_auth(self):
        """Test pay invoice requires authentication"""
        response = self.session.post(
            f"{BASE_URL}/api/invoices/pay/fake-id",
            json={"phone_number": "254712345678"}
        )
        assert response.status_code == 401
        print("✅ Pay invoice requires auth")


class TestSubscriptionPricing:
    """Test subscription pricing constants"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.owner_email = "owner@caiwave.com"
        self.owner_password = "owner123"
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def get_owner_token(self):
        """Get owner authentication token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": self.owner_email,
            "password": self.owner_password
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    
    def test_subscription_price_is_500_kes(self):
        """Test subscription price is KES 500 per hotspot per month"""
        token = self.get_owner_token()
        assert token is not None, "Owner login failed"
        
        response = self.session.get(
            f"{BASE_URL}/api/subscriptions/status",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Monthly fee should be 500 * hotspot_count
        hotspot_count = data.get("hotspot_count", 0)
        expected_fee = 500 * max(1, hotspot_count)  # At least 500 for 1 hotspot
        
        if hotspot_count > 0:
            assert data["monthly_fee"] == expected_fee
            print(f"✅ Monthly fee is KES {data['monthly_fee']} for {hotspot_count} hotspot(s)")
        else:
            print("✅ No hotspots, monthly fee calculation skipped")
    
    def test_trial_period_is_14_days(self):
        """Test trial period is 14 days"""
        token = self.get_owner_token()
        assert token is not None, "Owner login failed"
        
        response = self.session.get(
            f"{BASE_URL}/api/subscriptions/status",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # If in trial, days remaining should be <= 14
        if data["subscription_status"] == "trial":
            assert data["trial_days_remaining"] <= 14
            assert data["trial_days_remaining"] >= 0
            print(f"✅ Trial days remaining: {data['trial_days_remaining']} (max 14)")
        else:
            print(f"✅ Not in trial (status: {data['subscription_status']})")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
