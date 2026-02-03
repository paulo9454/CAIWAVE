"""
Phase 2 Backend Tests - CAIWAVE Wi-Fi Hotspot Billing Platform
Tests for: Campaigns, CAIWAVE TV Streams, Subsidized Uptime
All features are admin-only controlled
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@caiwave.com"
ADMIN_PASSWORD = "admin123"


class TestAdminAuth:
    """Test admin authentication for Phase 2 features"""
    
    def test_admin_login_success(self):
        """Test admin login with correct credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["role"] == "super_admin"
        assert data["user"]["email"] == ADMIN_EMAIL
        print(f"✅ Admin login successful - Role: {data['user']['role']}")
    
    def test_admin_login_wrong_password(self):
        """Test admin login with wrong password"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("✅ Wrong password correctly rejected")


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json()["token"]
    pytest.skip("Admin authentication failed")


@pytest.fixture
def auth_headers(admin_token):
    """Get authorization headers"""
    return {"Authorization": f"Bearer {admin_token}"}


class TestCampaignsAPI:
    """Test Campaigns CRUD operations - Admin Only"""
    
    def test_get_campaigns_list(self, auth_headers):
        """Test fetching campaigns list"""
        response = requests.get(f"{BASE_URL}/api/campaigns/", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get campaigns: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Campaigns list retrieved - Count: {len(data)}")
    
    def test_create_campaign(self, auth_headers):
        """Test creating a new campaign"""
        start_date = datetime.now() + timedelta(days=1)
        end_date = datetime.now() + timedelta(days=30)
        
        campaign_data = {
            "name": "TEST_Campaign_Phase2",
            "description": "Test campaign for Phase 2 testing",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "target_regions": ["Nairobi", "Mombasa"],
            "target_hotspot_ids": [],
            "assigned_ad_ids": []
        }
        
        response = requests.post(f"{BASE_URL}/api/campaigns/", json=campaign_data, headers=auth_headers)
        assert response.status_code == 200, f"Failed to create campaign: {response.text}"
        
        data = response.json()
        assert data["name"] == "TEST_Campaign_Phase2"
        assert data["status"] == "draft"
        assert "id" in data
        print(f"✅ Campaign created - ID: {data['id']}, Status: {data['status']}")
        return data["id"]
    
    def test_get_campaign_by_id(self, auth_headers):
        """Test getting a specific campaign"""
        # First create a campaign
        start_date = datetime.now() + timedelta(days=1)
        end_date = datetime.now() + timedelta(days=30)
        
        campaign_data = {
            "name": "TEST_Campaign_GetById",
            "description": "Test campaign for get by ID",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "target_regions": [],
            "target_hotspot_ids": [],
            "assigned_ad_ids": []
        }
        
        create_response = requests.post(f"{BASE_URL}/api/campaigns/", json=campaign_data, headers=auth_headers)
        assert create_response.status_code == 200
        campaign_id = create_response.json()["id"]
        
        # Get the campaign
        response = requests.get(f"{BASE_URL}/api/campaigns/{campaign_id}", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get campaign: {response.text}"
        
        data = response.json()
        assert data["id"] == campaign_id
        assert data["name"] == "TEST_Campaign_GetById"
        print(f"✅ Campaign retrieved by ID: {campaign_id}")
    
    def test_update_campaign_status_activate(self, auth_headers):
        """Test activating a campaign"""
        # Create a campaign first
        start_date = datetime.now() + timedelta(days=1)
        end_date = datetime.now() + timedelta(days=30)
        
        campaign_data = {
            "name": "TEST_Campaign_Activate",
            "description": "Test campaign for activation",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "target_regions": [],
            "target_hotspot_ids": [],
            "assigned_ad_ids": []
        }
        
        create_response = requests.post(f"{BASE_URL}/api/campaigns/", json=campaign_data, headers=auth_headers)
        assert create_response.status_code == 200
        campaign_id = create_response.json()["id"]
        
        # Activate the campaign
        response = requests.post(f"{BASE_URL}/api/campaigns/{campaign_id}/status?status=active", headers=auth_headers)
        assert response.status_code == 200, f"Failed to activate campaign: {response.text}"
        
        data = response.json()
        assert data["new_status"] == "active"
        print(f"✅ Campaign activated - ID: {campaign_id}")
    
    def test_update_campaign_status_pause(self, auth_headers):
        """Test pausing an active campaign"""
        # Create and activate a campaign first
        start_date = datetime.now() + timedelta(days=1)
        end_date = datetime.now() + timedelta(days=30)
        
        campaign_data = {
            "name": "TEST_Campaign_Pause",
            "description": "Test campaign for pausing",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "target_regions": [],
            "target_hotspot_ids": [],
            "assigned_ad_ids": []
        }
        
        create_response = requests.post(f"{BASE_URL}/api/campaigns/", json=campaign_data, headers=auth_headers)
        campaign_id = create_response.json()["id"]
        
        # Activate first
        requests.post(f"{BASE_URL}/api/campaigns/{campaign_id}/status?status=active", headers=auth_headers)
        
        # Then pause
        response = requests.post(f"{BASE_URL}/api/campaigns/{campaign_id}/status?status=paused", headers=auth_headers)
        assert response.status_code == 200, f"Failed to pause campaign: {response.text}"
        
        data = response.json()
        assert data["new_status"] == "paused"
        print(f"✅ Campaign paused - ID: {campaign_id}")
    
    def test_delete_campaign(self, auth_headers):
        """Test deleting a campaign"""
        # Create a campaign first
        start_date = datetime.now() + timedelta(days=1)
        end_date = datetime.now() + timedelta(days=30)
        
        campaign_data = {
            "name": "TEST_Campaign_Delete",
            "description": "Test campaign for deletion",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "target_regions": [],
            "target_hotspot_ids": [],
            "assigned_ad_ids": []
        }
        
        create_response = requests.post(f"{BASE_URL}/api/campaigns/", json=campaign_data, headers=auth_headers)
        campaign_id = create_response.json()["id"]
        
        # Delete the campaign
        response = requests.delete(f"{BASE_URL}/api/campaigns/{campaign_id}", headers=auth_headers)
        assert response.status_code == 200, f"Failed to delete campaign: {response.text}"
        
        # Verify deletion
        get_response = requests.get(f"{BASE_URL}/api/campaigns/{campaign_id}", headers=auth_headers)
        assert get_response.status_code == 404
        print(f"✅ Campaign deleted and verified - ID: {campaign_id}")


class TestStreamsAPI:
    """Test CAIWAVE TV Streams CRUD operations - Admin Only"""
    
    def test_get_streams_list(self, auth_headers):
        """Test fetching streams list"""
        response = requests.get(f"{BASE_URL}/api/streams/", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get streams: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Streams list retrieved - Count: {len(data)}")
    
    def test_create_stream(self, auth_headers):
        """Test creating a new stream"""
        start_time = datetime.now() + timedelta(hours=1)
        end_time = datetime.now() + timedelta(hours=4)
        
        stream_data = {
            "name": "TEST_Stream_Phase2",
            "description": "Test stream for Phase 2 testing",
            "stream_url": "https://stream.caiwave.com/test/live",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "access_type": "paid",
            "price": 50.0,
            "allowed_hotspot_ids": [],
            "allowed_regions": ["Nairobi"],
            "pre_roll_ad_ids": [],
            "thumbnail_url": "https://example.com/thumbnail.jpg"
        }
        
        response = requests.post(f"{BASE_URL}/api/streams/", json=stream_data, headers=auth_headers)
        assert response.status_code == 200, f"Failed to create stream: {response.text}"
        
        data = response.json()
        assert data["name"] == "TEST_Stream_Phase2"
        assert data["is_active"] == True
        assert data["access_type"] == "paid"
        assert data["price"] == 50.0
        assert "id" in data
        print(f"✅ Stream created - ID: {data['id']}, Access: {data['access_type']}")
        return data["id"]
    
    def test_create_free_stream(self, auth_headers):
        """Test creating a free stream"""
        start_time = datetime.now() + timedelta(hours=1)
        end_time = datetime.now() + timedelta(hours=4)
        
        stream_data = {
            "name": "TEST_Free_Stream",
            "description": "Free stream with ads",
            "stream_url": "https://stream.caiwave.com/test/free",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "access_type": "free",
            "price": 0,
            "allowed_hotspot_ids": [],
            "allowed_regions": [],
            "pre_roll_ad_ids": [],
            "thumbnail_url": ""
        }
        
        response = requests.post(f"{BASE_URL}/api/streams/", json=stream_data, headers=auth_headers)
        assert response.status_code == 200, f"Failed to create free stream: {response.text}"
        
        data = response.json()
        assert data["access_type"] == "free"
        assert data["price"] == 0
        print(f"✅ Free stream created - ID: {data['id']}")
    
    def test_get_stream_by_id(self, auth_headers):
        """Test getting a specific stream"""
        # First create a stream
        start_time = datetime.now() + timedelta(hours=1)
        end_time = datetime.now() + timedelta(hours=4)
        
        stream_data = {
            "name": "TEST_Stream_GetById",
            "description": "Test stream for get by ID",
            "stream_url": "https://stream.caiwave.com/test/getbyid",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "access_type": "paid",
            "price": 30.0,
            "allowed_hotspot_ids": [],
            "allowed_regions": [],
            "pre_roll_ad_ids": [],
            "thumbnail_url": ""
        }
        
        create_response = requests.post(f"{BASE_URL}/api/streams/", json=stream_data, headers=auth_headers)
        assert create_response.status_code == 200
        stream_id = create_response.json()["id"]
        
        # Get the stream
        response = requests.get(f"{BASE_URL}/api/streams/{stream_id}", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get stream: {response.text}"
        
        data = response.json()
        assert data["id"] == stream_id
        assert data["name"] == "TEST_Stream_GetById"
        print(f"✅ Stream retrieved by ID: {stream_id}")
    
    def test_toggle_stream_disable(self, auth_headers):
        """Test disabling a stream"""
        # Create a stream first
        start_time = datetime.now() + timedelta(hours=1)
        end_time = datetime.now() + timedelta(hours=4)
        
        stream_data = {
            "name": "TEST_Stream_Toggle",
            "description": "Test stream for toggle",
            "stream_url": "https://stream.caiwave.com/test/toggle",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "access_type": "paid",
            "price": 25.0,
            "allowed_hotspot_ids": [],
            "allowed_regions": [],
            "pre_roll_ad_ids": [],
            "thumbnail_url": ""
        }
        
        create_response = requests.post(f"{BASE_URL}/api/streams/", json=stream_data, headers=auth_headers)
        stream_id = create_response.json()["id"]
        
        # Toggle (disable)
        response = requests.post(f"{BASE_URL}/api/streams/{stream_id}/toggle", headers=auth_headers)
        assert response.status_code == 200, f"Failed to toggle stream: {response.text}"
        
        data = response.json()
        assert data["is_active"] == False
        print(f"✅ Stream disabled - ID: {stream_id}")
    
    def test_toggle_stream_enable(self, auth_headers):
        """Test enabling a disabled stream"""
        # Create and disable a stream first
        start_time = datetime.now() + timedelta(hours=1)
        end_time = datetime.now() + timedelta(hours=4)
        
        stream_data = {
            "name": "TEST_Stream_Enable",
            "description": "Test stream for enable",
            "stream_url": "https://stream.caiwave.com/test/enable",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "access_type": "paid",
            "price": 25.0,
            "allowed_hotspot_ids": [],
            "allowed_regions": [],
            "pre_roll_ad_ids": [],
            "thumbnail_url": ""
        }
        
        create_response = requests.post(f"{BASE_URL}/api/streams/", json=stream_data, headers=auth_headers)
        stream_id = create_response.json()["id"]
        
        # Disable first
        requests.post(f"{BASE_URL}/api/streams/{stream_id}/toggle", headers=auth_headers)
        
        # Enable again
        response = requests.post(f"{BASE_URL}/api/streams/{stream_id}/toggle", headers=auth_headers)
        assert response.status_code == 200, f"Failed to enable stream: {response.text}"
        
        data = response.json()
        assert data["is_active"] == True
        print(f"✅ Stream enabled - ID: {stream_id}")
    
    def test_delete_stream(self, auth_headers):
        """Test deleting a stream"""
        # Create a stream first
        start_time = datetime.now() + timedelta(hours=1)
        end_time = datetime.now() + timedelta(hours=4)
        
        stream_data = {
            "name": "TEST_Stream_Delete",
            "description": "Test stream for deletion",
            "stream_url": "https://stream.caiwave.com/test/delete",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "access_type": "paid",
            "price": 25.0,
            "allowed_hotspot_ids": [],
            "allowed_regions": [],
            "pre_roll_ad_ids": [],
            "thumbnail_url": ""
        }
        
        create_response = requests.post(f"{BASE_URL}/api/streams/", json=stream_data, headers=auth_headers)
        stream_id = create_response.json()["id"]
        
        # Delete the stream
        response = requests.delete(f"{BASE_URL}/api/streams/{stream_id}", headers=auth_headers)
        assert response.status_code == 200, f"Failed to delete stream: {response.text}"
        
        # Verify deletion
        get_response = requests.get(f"{BASE_URL}/api/streams/{stream_id}", headers=auth_headers)
        assert get_response.status_code == 404
        print(f"✅ Stream deleted and verified - ID: {stream_id}")
    
    def test_get_live_streams_public(self):
        """Test public endpoint for live streams"""
        response = requests.get(f"{BASE_URL}/api/streams/live")
        assert response.status_code == 200, f"Failed to get live streams: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Live streams public endpoint working - Count: {len(data)}")


class TestSubsidizedUptimeAPI:
    """Test Subsidized Uptime CRUD operations - Admin Only"""
    
    def test_get_subsidized_uptimes_list(self, auth_headers):
        """Test fetching subsidized uptimes list"""
        response = requests.get(f"{BASE_URL}/api/subsidized-uptime/", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get subsidized uptimes: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Subsidized uptimes list retrieved - Count: {len(data)}")
    
    def test_create_subsidized_uptime(self, auth_headers):
        """Test creating a new subsidized uptime offer"""
        start_date = datetime.now() + timedelta(days=1)
        end_date = datetime.now() + timedelta(days=30)
        
        uptime_data = {
            "name": "TEST_Subsidy_Phase2",
            "description": "Test subsidized uptime for Phase 2 testing",
            "original_price": 35.0,
            "discounted_price": 15.0,
            "duration_hours": 25,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "daily_start_time": "08:00",
            "daily_end_time": "22:00",
            "allowed_hotspot_ids": [],
            "allowed_regions": ["Nairobi"],
            "max_uses": 1000,
            "linked_campaign_id": None,
            "linked_stream_id": None
        }
        
        response = requests.post(f"{BASE_URL}/api/subsidized-uptime/", json=uptime_data, headers=auth_headers)
        assert response.status_code == 200, f"Failed to create subsidized uptime: {response.text}"
        
        data = response.json()
        assert data["name"] == "TEST_Subsidy_Phase2"
        assert data["status"] == "draft"
        assert data["original_price"] == 35.0
        assert data["discounted_price"] == 15.0
        assert data["duration_hours"] == 25
        assert "id" in data
        print(f"✅ Subsidized uptime created - ID: {data['id']}, Status: {data['status']}")
        return data["id"]
    
    def test_create_unlimited_subsidized_uptime(self, auth_headers):
        """Test creating a subsidized uptime with unlimited uses"""
        start_date = datetime.now() + timedelta(days=1)
        end_date = datetime.now() + timedelta(days=30)
        
        uptime_data = {
            "name": "TEST_Subsidy_Unlimited",
            "description": "Unlimited uses subsidized uptime",
            "original_price": 30.0,
            "discounted_price": 10.0,
            "duration_hours": 12,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "daily_start_time": None,
            "daily_end_time": None,
            "allowed_hotspot_ids": [],
            "allowed_regions": [],
            "max_uses": None,
            "linked_campaign_id": None,
            "linked_stream_id": None
        }
        
        response = requests.post(f"{BASE_URL}/api/subsidized-uptime/", json=uptime_data, headers=auth_headers)
        assert response.status_code == 200, f"Failed to create unlimited subsidized uptime: {response.text}"
        
        data = response.json()
        assert data["max_uses"] is None
        print(f"✅ Unlimited subsidized uptime created - ID: {data['id']}")
    
    def test_get_subsidized_uptime_by_id(self, auth_headers):
        """Test getting a specific subsidized uptime"""
        # First create a subsidized uptime
        start_date = datetime.now() + timedelta(days=1)
        end_date = datetime.now() + timedelta(days=30)
        
        uptime_data = {
            "name": "TEST_Subsidy_GetById",
            "description": "Test subsidized uptime for get by ID",
            "original_price": 35.0,
            "discounted_price": 20.0,
            "duration_hours": 24,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "daily_start_time": None,
            "daily_end_time": None,
            "allowed_hotspot_ids": [],
            "allowed_regions": [],
            "max_uses": None,
            "linked_campaign_id": None,
            "linked_stream_id": None
        }
        
        create_response = requests.post(f"{BASE_URL}/api/subsidized-uptime/", json=uptime_data, headers=auth_headers)
        assert create_response.status_code == 200
        uptime_id = create_response.json()["id"]
        
        # Get the subsidized uptime
        response = requests.get(f"{BASE_URL}/api/subsidized-uptime/{uptime_id}", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get subsidized uptime: {response.text}"
        
        data = response.json()
        assert data["id"] == uptime_id
        assert data["name"] == "TEST_Subsidy_GetById"
        print(f"✅ Subsidized uptime retrieved by ID: {uptime_id}")
    
    def test_update_subsidized_uptime_status_activate(self, auth_headers):
        """Test activating a subsidized uptime"""
        # Create a subsidized uptime first
        start_date = datetime.now() + timedelta(days=1)
        end_date = datetime.now() + timedelta(days=30)
        
        uptime_data = {
            "name": "TEST_Subsidy_Activate",
            "description": "Test subsidized uptime for activation",
            "original_price": 35.0,
            "discounted_price": 15.0,
            "duration_hours": 25,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "daily_start_time": None,
            "daily_end_time": None,
            "allowed_hotspot_ids": [],
            "allowed_regions": [],
            "max_uses": None,
            "linked_campaign_id": None,
            "linked_stream_id": None
        }
        
        create_response = requests.post(f"{BASE_URL}/api/subsidized-uptime/", json=uptime_data, headers=auth_headers)
        assert create_response.status_code == 200
        uptime_id = create_response.json()["id"]
        
        # Activate the subsidized uptime
        response = requests.post(f"{BASE_URL}/api/subsidized-uptime/{uptime_id}/status?status=active", headers=auth_headers)
        assert response.status_code == 200, f"Failed to activate subsidized uptime: {response.text}"
        
        data = response.json()
        assert data["new_status"] == "active"
        print(f"✅ Subsidized uptime activated - ID: {uptime_id}")
    
    def test_update_subsidized_uptime_status_expired(self, auth_headers):
        """Test marking a subsidized uptime as expired"""
        # Create a subsidized uptime first
        start_date = datetime.now() + timedelta(days=1)
        end_date = datetime.now() + timedelta(days=30)
        
        uptime_data = {
            "name": "TEST_Subsidy_Expire",
            "description": "Test subsidized uptime for expiration",
            "original_price": 35.0,
            "discounted_price": 15.0,
            "duration_hours": 25,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "daily_start_time": None,
            "daily_end_time": None,
            "allowed_hotspot_ids": [],
            "allowed_regions": [],
            "max_uses": None,
            "linked_campaign_id": None,
            "linked_stream_id": None
        }
        
        create_response = requests.post(f"{BASE_URL}/api/subsidized-uptime/", json=uptime_data, headers=auth_headers)
        uptime_id = create_response.json()["id"]
        
        # Mark as expired
        response = requests.post(f"{BASE_URL}/api/subsidized-uptime/{uptime_id}/status?status=expired", headers=auth_headers)
        assert response.status_code == 200, f"Failed to expire subsidized uptime: {response.text}"
        
        data = response.json()
        assert data["new_status"] == "expired"
        print(f"✅ Subsidized uptime expired - ID: {uptime_id}")
    
    def test_delete_subsidized_uptime(self, auth_headers):
        """Test deleting a subsidized uptime"""
        # Create a subsidized uptime first
        start_date = datetime.now() + timedelta(days=1)
        end_date = datetime.now() + timedelta(days=30)
        
        uptime_data = {
            "name": "TEST_Subsidy_Delete",
            "description": "Test subsidized uptime for deletion",
            "original_price": 35.0,
            "discounted_price": 15.0,
            "duration_hours": 25,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "daily_start_time": None,
            "daily_end_time": None,
            "allowed_hotspot_ids": [],
            "allowed_regions": [],
            "max_uses": None,
            "linked_campaign_id": None,
            "linked_stream_id": None
        }
        
        create_response = requests.post(f"{BASE_URL}/api/subsidized-uptime/", json=uptime_data, headers=auth_headers)
        uptime_id = create_response.json()["id"]
        
        # Delete the subsidized uptime
        response = requests.delete(f"{BASE_URL}/api/subsidized-uptime/{uptime_id}", headers=auth_headers)
        assert response.status_code == 200, f"Failed to delete subsidized uptime: {response.text}"
        
        # Verify deletion
        get_response = requests.get(f"{BASE_URL}/api/subsidized-uptime/{uptime_id}", headers=auth_headers)
        assert get_response.status_code == 404
        print(f"✅ Subsidized uptime deleted and verified - ID: {uptime_id}")
    
    def test_get_active_subsidized_uptimes_public(self):
        """Test public endpoint for active subsidized uptimes"""
        response = requests.get(f"{BASE_URL}/api/subsidized-uptime/active")
        assert response.status_code == 200, f"Failed to get active subsidized uptimes: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Active subsidized uptimes public endpoint working - Count: {len(data)}")


class TestUnauthorizedAccess:
    """Test that Phase 2 features require admin authentication"""
    
    def test_campaigns_requires_auth(self):
        """Test that campaigns endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/campaigns/")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✅ Campaigns endpoint correctly requires authentication")
    
    def test_create_campaign_requires_admin(self):
        """Test that creating campaign requires admin role"""
        # First login as a non-admin user (if exists) or just test without auth
        response = requests.post(f"{BASE_URL}/api/campaigns/", json={
            "name": "Unauthorized Campaign",
            "description": "Should fail",
            "start_date": datetime.now().isoformat(),
            "end_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "target_regions": [],
            "target_hotspot_ids": [],
            "assigned_ad_ids": []
        })
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✅ Create campaign correctly requires admin authentication")
    
    def test_streams_admin_only(self):
        """Test that creating streams requires admin role"""
        response = requests.post(f"{BASE_URL}/api/streams/", json={
            "name": "Unauthorized Stream",
            "stream_url": "https://test.com",
            "start_time": datetime.now().isoformat(),
            "end_time": (datetime.now() + timedelta(hours=4)).isoformat(),
            "access_type": "paid",
            "price": 50.0,
            "allowed_hotspot_ids": [],
            "allowed_regions": [],
            "pre_roll_ad_ids": [],
            "thumbnail_url": ""
        })
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✅ Create stream correctly requires admin authentication")
    
    def test_subsidized_uptime_admin_only(self):
        """Test that creating subsidized uptime requires admin role"""
        response = requests.post(f"{BASE_URL}/api/subsidized-uptime/", json={
            "name": "Unauthorized Subsidy",
            "original_price": 35.0,
            "discounted_price": 15.0,
            "duration_hours": 25,
            "start_date": datetime.now().isoformat(),
            "end_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "allowed_hotspot_ids": [],
            "allowed_regions": []
        })
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✅ Create subsidized uptime correctly requires admin authentication")


# Cleanup fixture to remove test data
@pytest.fixture(scope="module", autouse=True)
def cleanup_test_data(admin_token):
    """Cleanup TEST_ prefixed data after all tests complete"""
    yield
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Cleanup campaigns
    try:
        campaigns = requests.get(f"{BASE_URL}/api/campaigns/", headers=headers).json()
        for campaign in campaigns:
            if campaign.get("name", "").startswith("TEST_"):
                requests.delete(f"{BASE_URL}/api/campaigns/{campaign['id']}", headers=headers)
    except:
        pass
    
    # Cleanup streams
    try:
        streams = requests.get(f"{BASE_URL}/api/streams/", headers=headers).json()
        for stream in streams:
            if stream.get("name", "").startswith("TEST_"):
                requests.delete(f"{BASE_URL}/api/streams/{stream['id']}", headers=headers)
    except:
        pass
    
    # Cleanup subsidized uptimes
    try:
        uptimes = requests.get(f"{BASE_URL}/api/subsidized-uptime/", headers=headers).json()
        for uptime in uptimes:
            if uptime.get("name", "").startswith("TEST_"):
                requests.delete(f"{BASE_URL}/api/subsidized-uptime/{uptime['id']}", headers=headers)
    except:
        pass
    
    print("✅ Test data cleanup completed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
