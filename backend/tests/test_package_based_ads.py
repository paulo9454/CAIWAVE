"""
Test Package-Based Advertising System for CAIWAVE Wi-Fi Platform
Tests:
- Ad packages API (GET /api/ad-packages)
- Locations API (counties and constituencies)
- Advertiser login and ad management
- Admin login and ad approval workflow
"""

import pytest
import requests
import os
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://wifi-platform.preview.emergentagent.com')

# Test credentials
ADMIN_EMAIL = "admin@caiwave.com"
ADMIN_PASSWORD = "admin123"
ADVERTISER_EMAIL = "advertiser@caiwave.com"
ADVERTISER_PASSWORD = "advertiser123"


class TestAdPackagesAPI:
    """Test Ad Packages API - GET /api/ad-packages"""
    
    def test_get_ad_packages_returns_3_packages(self):
        """GET /api/ad-packages should return 3 packages"""
        response = requests.get(f"{BASE_URL}/api/ad-packages/")
        assert response.status_code == 200
        
        packages = response.json()
        assert isinstance(packages, list)
        assert len(packages) == 3, f"Expected 3 packages, got {len(packages)}"
        
        # Verify package names
        package_names = [p["name"] for p in packages]
        assert "Small Area" in package_names
        assert "Large Area" in package_names
        assert "Wide Area" in package_names
    
    def test_small_area_package_details(self):
        """Small Area package should have correct pricing and scope"""
        response = requests.get(f"{BASE_URL}/api/ad-packages/")
        assert response.status_code == 200
        
        packages = response.json()
        small_area = next((p for p in packages if p["name"] == "Small Area"), None)
        
        assert small_area is not None
        assert small_area["price"] == 300.0
        assert small_area["duration_days"] == 3
        assert small_area["coverage_scope"] == "constituency"
        assert small_area["status"] == "active"
    
    def test_large_area_package_details(self):
        """Large Area package should have correct pricing and scope"""
        response = requests.get(f"{BASE_URL}/api/ad-packages/")
        assert response.status_code == 200
        
        packages = response.json()
        large_area = next((p for p in packages if p["name"] == "Large Area"), None)
        
        assert large_area is not None
        assert large_area["price"] == 1000.0
        assert large_area["duration_days"] == 7
        assert large_area["coverage_scope"] == "county"
        assert large_area["status"] == "active"
    
    def test_wide_area_package_details(self):
        """Wide Area package should have correct pricing and scope"""
        response = requests.get(f"{BASE_URL}/api/ad-packages/")
        assert response.status_code == 200
        
        packages = response.json()
        wide_area = next((p for p in packages if p["name"] == "Wide Area"), None)
        
        assert wide_area is not None
        assert wide_area["price"] == 3500.0
        assert wide_area["duration_days"] == 14
        assert wide_area["coverage_scope"] == "national"
        assert wide_area["status"] == "active"


class TestLocationsAPI:
    """Test Locations API - counties and constituencies"""
    
    def test_get_counties_returns_kenya_counties(self):
        """GET /api/locations/counties should return Kenya counties"""
        response = requests.get(f"{BASE_URL}/api/locations/counties")
        assert response.status_code == 200
        
        data = response.json()
        assert "counties" in data
        counties = data["counties"]
        
        assert isinstance(counties, list)
        assert len(counties) > 0
        
        # Verify some expected counties
        assert "Nairobi" in counties
        assert "Mombasa" in counties
        assert "Kisumu" in counties
        assert "Nakuru" in counties
    
    def test_get_nairobi_constituencies(self):
        """GET /api/locations/constituencies?county=Nairobi should return Nairobi constituencies"""
        response = requests.get(f"{BASE_URL}/api/locations/constituencies?county=Nairobi")
        assert response.status_code == 200
        
        data = response.json()
        assert "constituencies" in data
        constituencies = data["constituencies"]
        
        assert isinstance(constituencies, list)
        assert len(constituencies) > 0
        
        # Verify some expected Nairobi constituencies
        assert "Westlands" in constituencies
        assert "Langata" in constituencies
        assert "Kibra" in constituencies
    
    def test_get_all_constituencies_without_county_filter(self):
        """GET /api/locations/constituencies without county should return all"""
        response = requests.get(f"{BASE_URL}/api/locations/constituencies")
        assert response.status_code == 200
        
        data = response.json()
        assert "constituencies" in data
        constituencies = data["constituencies"]
        
        # Should return list of objects with county and constituency
        assert isinstance(constituencies, list)
        assert len(constituencies) > 0


class TestAdvertiserAuth:
    """Test Advertiser authentication"""
    
    def test_advertiser_login_success(self):
        """Advertiser should be able to login with valid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADVERTISER_EMAIL, "password": ADVERTISER_PASSWORD}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == ADVERTISER_EMAIL
        assert data["user"]["role"] == "advertiser"
    
    def test_advertiser_login_invalid_password(self):
        """Advertiser login should fail with wrong password"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADVERTISER_EMAIL, "password": "wrongpassword"}
        )
        assert response.status_code == 401


class TestAdminAuth:
    """Test Admin authentication"""
    
    def test_admin_login_success(self):
        """Admin should be able to login with valid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == ADMIN_EMAIL
        assert data["user"]["role"] == "super_admin"
    
    def test_admin_login_invalid_password(self):
        """Admin login should fail with wrong password"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": "wrongpassword"}
        )
        assert response.status_code == 401


class TestAdvertiserAdsAPI:
    """Test Advertiser Ads API endpoints"""
    
    @pytest.fixture
    def advertiser_token(self):
        """Get advertiser auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADVERTISER_EMAIL, "password": ADVERTISER_PASSWORD}
        )
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Advertiser login failed")
    
    def test_get_advertiser_ads(self, advertiser_token):
        """Advertiser should be able to get their ads list"""
        response = requests.get(
            f"{BASE_URL}/api/ads/",
            headers={"Authorization": f"Bearer {advertiser_token}"}
        )
        assert response.status_code == 200
        
        ads = response.json()
        assert isinstance(ads, list)
    
    def test_get_ads_requires_auth(self):
        """GET /api/ads/ should require authentication"""
        response = requests.get(f"{BASE_URL}/api/ads/")
        assert response.status_code in [401, 403]


class TestAdminAdsAPI:
    """Test Admin Ads API endpoints"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Admin login failed")
    
    def test_admin_get_all_ads(self, admin_token):
        """Admin should be able to get all ads"""
        response = requests.get(
            f"{BASE_URL}/api/ads/",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        
        ads = response.json()
        assert isinstance(ads, list)
    
    def test_admin_get_pending_ads(self, admin_token):
        """Admin should be able to get pending ads"""
        response = requests.get(
            f"{BASE_URL}/api/ads/pending",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        
        ads = response.json()
        assert isinstance(ads, list)
    
    def test_get_pending_ads_requires_admin(self):
        """GET /api/ads/pending should require admin role"""
        # Try without auth
        response = requests.get(f"{BASE_URL}/api/ads/pending")
        assert response.status_code in [401, 403]
        
        # Try with advertiser token
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADVERTISER_EMAIL, "password": ADVERTISER_PASSWORD}
        )
        if login_response.status_code == 200:
            advertiser_token = login_response.json()["token"]
            response = requests.get(
                f"{BASE_URL}/api/ads/pending",
                headers={"Authorization": f"Bearer {advertiser_token}"}
            )
            assert response.status_code == 403


class TestActiveAdsAPI:
    """Test public active ads endpoint"""
    
    def test_get_active_ads_public(self):
        """GET /api/ads/active should be public (for captive portal)"""
        response = requests.get(f"{BASE_URL}/api/ads/active")
        assert response.status_code == 200
        
        ads = response.json()
        assert isinstance(ads, list)


class TestAnalyticsDashboard:
    """Test Analytics Dashboard API"""
    
    def test_get_dashboard_stats(self):
        """GET /api/analytics/dashboard should return stats"""
        response = requests.get(f"{BASE_URL}/api/analytics/dashboard")
        assert response.status_code == 200
        
        data = response.json()
        # Verify expected fields exist
        assert "total_revenue" in data or "pending_ads" in data or "active_ads" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
