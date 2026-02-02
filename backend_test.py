#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class CaitechAPITester:
    def __init__(self, base_url="https://caitech-wifi.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.admin_user_id = None
        self.created_package_id = None
        self.created_hotspot_id = None

    def log(self, message):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=30)

            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                self.log(f"✅ {name} - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, {}
            else:
                error_msg = f"Expected {expected_status}, got {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f" - {error_detail}"
                except:
                    error_msg += f" - {response.text[:200]}"
                
                self.log(f"❌ {name} - {error_msg}")
                self.failed_tests.append({
                    "test": name,
                    "endpoint": endpoint,
                    "expected": expected_status,
                    "actual": response.status_code,
                    "error": error_msg
                })
                return False, {}

        except Exception as e:
            self.log(f"❌ {name} - Exception: {str(e)}")
            self.failed_tests.append({
                "test": name,
                "endpoint": endpoint,
                "error": str(e)
            })
            return False, {}

    def test_health_check(self):
        """Test API health"""
        return self.run_test("Health Check", "GET", "health", 200)

    def test_seed_data(self):
        """Seed default data"""
        success, response = self.run_test("Seed Data", "POST", "seed", 200)
        if success:
            self.log("🌱 Seed data created successfully")
        return success

    def test_get_packages(self):
        """Test getting packages"""
        success, response = self.run_test("Get Packages", "GET", "packages/", 200)
        if success and response:
            packages = response if isinstance(response, list) else []
            self.log(f"📦 Found {len(packages)} packages")
            if packages:
                self.created_package_id = packages[0].get('id')
                self.log(f"🎯 Using package ID: {self.created_package_id}")
        return success

    def test_admin_login(self):
        """Test admin login"""
        login_data = {
            "email": "admin@caitech.com",
            "password": "admin123"
        }
        
        success, response = self.run_test("Admin Login", "POST", "auth/login", 200, login_data)
        if success and response:
            self.token = response.get("token")
            user_data = response.get("user", {})
            self.admin_user_id = user_data.get("id")
            self.log(f"🔐 Admin login successful, user ID: {self.admin_user_id}")
            self.log(f"👤 Role: {user_data.get('role')}")
        return success

    def test_register_hotspot_owner(self):
        """Test registering a hotspot owner"""
        register_data = {
            "email": f"owner_{datetime.now().strftime('%H%M%S')}@test.com",
            "name": "Test Hotspot Owner",
            "password": "test123",
            "phone": "+254700123456",
            "role": "hotspot_owner"
        }
        
        return self.run_test("Register Hotspot Owner", "POST", "auth/register", 200, register_data)

    def test_register_advertiser(self):
        """Test registering an advertiser"""
        register_data = {
            "email": f"advertiser_{datetime.now().strftime('%H%M%S')}@test.com", 
            "name": "Test Advertiser",
            "password": "test123",
            "phone": "+254700123456",
            "role": "advertiser"
        }
        
        return self.run_test("Register Advertiser", "POST", "auth/register", 200, register_data)

    def test_get_dashboard_stats(self):
        """Test dashboard stats (requires authentication)"""
        if not self.token:
            self.log("⚠️  Skipping dashboard stats - no auth token")
            return False
        
        return self.run_test("Dashboard Stats", "GET", "analytics/dashboard", 200)

    def test_create_hotspot(self):
        """Test creating a hotspot (requires admin auth)"""
        if not self.token or not self.admin_user_id:
            self.log("⚠️  Skipping hotspot creation - no auth token")
            return False
            
        hotspot_data = {
            "name": "Test Hotspot",
            "ssid": "CAITECH-TEST",
            "location_name": "Test Location",
            "ward": "Test Ward", 
            "constituency": "Test Constituency",
            "county": "Test County",
            "owner_id": self.admin_user_id,
            "is_active": True
        }
        
        success, response = self.run_test("Create Hotspot", "POST", "hotspots/", 200, hotspot_data)
        if success and response:
            self.created_hotspot_id = response.get('id')
            self.log(f"🏢 Created hotspot ID: {self.created_hotspot_id}")
        return success

    def test_get_hotspots(self):
        """Test getting hotspots"""
        if not self.token:
            self.log("⚠️  Skipping get hotspots - no auth token")
            return False
            
        return self.run_test("Get Hotspots", "GET", "hotspots/", 200)

    def test_get_portal_data(self):
        """Test captive portal data endpoint"""
        if not self.created_hotspot_id:
            self.log("⚠️  Skipping portal data - no hotspot ID available")
            return False
            
        return self.run_test("Portal Data", "GET", f"portal/{self.created_hotspot_id}", 200)

    def test_create_session(self):
        """Test creating a session"""
        if not self.created_package_id or not self.created_hotspot_id:
            self.log("⚠️  Skipping session creation - missing package or hotspot ID")
            return False
            
        session_data = {
            "package_id": self.created_package_id,
            "hotspot_id": self.created_hotspot_id,
            "user_mac": "AA:BB:CC:DD:EE:FF"
        }
        
        return self.run_test("Create Session", "POST", "sessions/", 200, session_data)

    def test_mock_payment(self):
        """Test mock M-Pesa payment"""
        if not self.created_package_id or not self.created_hotspot_id:
            self.log("⚠️  Skipping payment test - missing package or hotspot ID")
            return False
            
        payment_data = {
            "amount": 20,
            "phone_number": "254700123456",
            "package_id": self.created_package_id,
            "hotspot_id": self.created_hotspot_id
        }
        
        return self.run_test("Mock Payment", "POST", "payments/initiate", 200, payment_data)

    def run_all_tests(self):
        """Run all API tests"""
        self.log("🚀 Starting CAITECH API Testing")
        self.log(f"🌐 Base URL: {self.base_url}")
        
        # Basic health and setup tests
        self.test_health_check()
        self.test_seed_data()
        
        # Package tests
        self.test_get_packages()
        
        # Authentication tests
        self.test_admin_login()
        self.test_register_hotspot_owner()
        self.test_register_advertiser()
        
        # Authenticated API tests
        self.test_get_dashboard_stats()
        self.test_create_hotspot()
        self.test_get_hotspots()
        
        # Portal and session tests
        self.test_get_portal_data()
        self.test_create_session()
        self.test_mock_payment()
        
        # Print results
        self.print_results()
        
        return self.tests_passed == self.tests_run

    def print_results(self):
        """Print test results summary"""
        self.log("\n" + "="*50)
        self.log("📊 TEST RESULTS SUMMARY")
        self.log("="*50)
        self.log(f"✅ Tests passed: {self.tests_passed}/{self.tests_run}")
        self.log(f"❌ Tests failed: {len(self.failed_tests)}")
        
        if self.failed_tests:
            self.log("\n🚨 FAILED TESTS:")
            for fail in self.failed_tests:
                self.log(f"  ❌ {fail['test']}: {fail.get('error', 'Unknown error')}")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        self.log(f"\n📈 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            self.log("🎉 API testing mostly successful!")
        elif success_rate >= 60:
            self.log("⚠️  API has some issues but core functionality works")
        else:
            self.log("🚨 API has significant issues")

def main():
    tester = CaitechAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())