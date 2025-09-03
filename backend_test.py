import requests
import sys
import json
from datetime import datetime

class mAInetAPITester:
    def __init__(self, base_url="https://payeer-deposit.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_user_email = f"test_user_{datetime.now().strftime('%H%M%S')}@test.com"
        self.test_username = f"testuser_{datetime.now().strftime('%H%M%S')}"
        self.test_password = "TestPass123!"

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}" if endpoint else self.base_url
        
        if headers is None:
            headers = {'Content-Type': 'application/json'}
        
        if self.token and 'Authorization' not in headers:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict) and len(response_data) <= 5:
                        print(f"   Response: {response_data}")
                    elif isinstance(response_data, list):
                        print(f"   Response: List with {len(response_data)} items")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except requests.exceptions.RequestException as e:
            print(f"❌ Failed - Network Error: {str(e)}")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        return self.run_test("Root API Endpoint", "GET", "", 200)

    def test_register(self):
        """Test user registration"""
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data={
                "email": self.test_user_email,
                "username": self.test_username,
                "password": self.test_password
            }
        )
        if success and 'token' in response:
            self.token = response['token']
            self.user_id = response.get('user_id')
            print(f"   Token obtained: {self.token[:20]}...")
            return True
        return False

    def test_login(self):
        """Test user login"""
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data={
                "email": self.test_user_email,
                "password": self.test_password
            }
        )
        if success and 'token' in response:
            self.token = response['token']
            self.user_id = response.get('user_id')
            return True
        return False

    def test_get_user_profile(self):
        """Test getting user profile"""
        success, response = self.run_test(
            "Get User Profile",
            "GET",
            "auth/me",
            200
        )
        return success

    def test_init_sample_data(self):
        """Test initializing sample data"""
        return self.run_test(
            "Initialize Sample Data",
            "POST",
            "init-data",
            200
        )

    def test_get_products(self):
        """Test getting all products"""
        success, response = self.run_test(
            "Get All Products",
            "GET",
            "products",
            200
        )
        if success and isinstance(response, list):
            print(f"   Found {len(response)} products")
        return success

    def test_get_products_by_category(self):
        """Test getting products by category"""
        categories = ["equipment", "cloud_mining", "contracts"]
        all_passed = True
        
        for category in categories:
            success, response = self.run_test(
                f"Get Products - {category}",
                "GET",
                f"products?category={category}",
                200
            )
            if success and isinstance(response, list):
                print(f"   Found {len(response)} {category} products")
            all_passed = all_passed and success
        
        return all_passed

    def test_get_tasks(self):
        """Test getting all tasks"""
        success, response = self.run_test(
            "Get All Tasks",
            "GET",
            "tasks",
            200
        )
        if success and isinstance(response, list):
            print(f"   Found {len(response)} tasks")
            self.available_tasks = response
        return success

    def test_complete_task(self):
        """Test completing a task"""
        if not hasattr(self, 'available_tasks') or not self.available_tasks:
            print("❌ No tasks available to complete")
            return False
        
        task_id = self.available_tasks[0]['id']
        success, response = self.run_test(
            "Complete Task",
            "POST",
            f"tasks/{task_id}/complete",
            200
        )
        return success

    def test_get_my_tasks(self):
        """Test getting user's completed tasks"""
        return self.run_test(
            "Get My Tasks",
            "GET",
            "tasks/my",
            200
        )

    def test_create_deposit(self):
        """Test creating a deposit"""
        success, response = self.run_test(
            "Create Deposit",
            "POST",
            "deposits",
            200,
            data={
                "amount": 100.0,
                "payment_method": "payeer",
                "transaction_id": f"TXN_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            }
        )
        return success

    def test_get_my_deposits(self):
        """Test getting user's deposits"""
        return self.run_test(
            "Get My Deposits",
            "GET",
            "deposits/my",
            200
        )

    def test_get_stats(self):
        """Test getting user stats"""
        success, response = self.run_test(
            "Get User Stats",
            "GET",
            "stats",
            200
        )
        if success:
            expected_keys = ['balance', 'bonus_balance', 'total_earned', 'completed_tasks', 'total_deposited', 'referral_code']
            for key in expected_keys:
                if key not in response:
                    print(f"   ⚠️  Missing key in stats: {key}")
        return success

    def test_referral_system(self):
        """Test referral system by creating a new user with referral code"""
        # First get the referral code from current user
        success, user_data = self.run_test(
            "Get Referral Code",
            "GET",
            "auth/me",
            200
        )
        
        if not success or 'referral_code' not in user_data:
            print("❌ Could not get referral code")
            return False
        
        referral_code = user_data['referral_code']
        print(f"   Using referral code: {referral_code}")
        
        # Create new user with referral code
        new_user_email = f"referred_user_{datetime.now().strftime('%H%M%S')}@test.com"
        new_username = f"referreduser_{datetime.now().strftime('%H%M%S')}"
        
        success, response = self.run_test(
            "Register with Referral Code",
            "POST",
            "auth/register",
            200,
            data={
                "email": new_user_email,
                "username": new_username,
                "password": self.test_password,
                "referral_code": referral_code
            }
        )
        return success

    # NEW GAME FUNCTIONALITY TESTS
    def test_game_status(self):
        """Test getting game status"""
        success, response = self.run_test(
            "Get Game Status",
            "GET",
            "game/status",
            200
        )
        if success:
            expected_keys = ['energy', 'max_energy', 'energy_regen_rate', 'click_power', 'auto_mining_rate', 'total_clicks', 'game_balance']
            for key in expected_keys:
                if key not in response:
                    print(f"   ⚠️  Missing key in game status: {key}")
            self.game_status = response
        return success

    def test_game_click(self):
        """Test clicking in the game"""
        success, response = self.run_test(
            "Game Click Action",
            "POST",
            "game/click",
            200,
            data={"clicks": 1}
        )
        if success:
            expected_keys = ['tokens_earned', 'energy_remaining', 'total_clicks']
            for key in expected_keys:
                if key not in response:
                    print(f"   ⚠️  Missing key in click response: {key}")
            print(f"   Tokens earned: {response.get('tokens_earned', 0)}")
            print(f"   Energy remaining: {response.get('energy_remaining', 0)}")
        return success

    def test_game_multiple_clicks(self):
        """Test multiple clicks to drain energy"""
        success, response = self.run_test(
            "Game Multiple Clicks",
            "POST",
            "game/click",
            200,
            data={"clicks": 5}
        )
        return success

    def test_game_click_no_energy(self):
        """Test clicking when no energy (should fail)"""
        # First drain all energy
        for i in range(20):  # Try to drain energy
            self.run_test(
                f"Drain Energy Click {i+1}",
                "POST",
                "game/click",
                200,
                data={"clicks": 10}
            )
        
        # Now try to click with no energy - should fail
        success, response = self.run_test(
            "Game Click No Energy (Should Fail)",
            "POST",
            "game/click",
            400,  # Should return 400 for insufficient energy
            data={"clicks": 1}
        )
        return success

    def test_game_transfer_balance(self):
        """Test transferring game balance to main balance"""
        # First make sure we have some game balance by clicking
        self.run_test(
            "Generate Game Balance",
            "POST",
            "game/click",
            200,
            data={"clicks": 1}
        )
        
        success, response = self.run_test(
            "Transfer Game Balance",
            "POST",
            "game/transfer",
            200
        )
        if success and 'transferred_amount' in response:
            print(f"   Transferred amount: {response['transferred_amount']}")
        return success

    def test_get_upgrades(self):
        """Test getting all available upgrades"""
        success, response = self.run_test(
            "Get All Upgrades",
            "GET",
            "upgrades",
            200
        )
        if success and isinstance(response, list):
            print(f"   Found {len(response)} upgrades")
            self.available_upgrades = response
            for upgrade in response:
                print(f"   - {upgrade.get('name', 'Unknown')}: {upgrade.get('upgrade_type', 'Unknown')} (${upgrade.get('base_price', 0)})")
        return success

    def test_get_my_upgrades(self):
        """Test getting user's upgrades"""
        success, response = self.run_test(
            "Get My Upgrades",
            "GET",
            "upgrades/my",
            200
        )
        if success and isinstance(response, list):
            print(f"   User has {len(response)} upgrades")
        return success

    def test_buy_upgrade(self):
        """Test buying an upgrade"""
        if not hasattr(self, 'available_upgrades') or not self.available_upgrades:
            print("❌ No upgrades available to buy")
            return False
        
        # Find the cheapest upgrade
        cheapest_upgrade = min(self.available_upgrades, key=lambda x: x.get('base_price', float('inf')))
        upgrade_id = cheapest_upgrade['id']
        
        success, response = self.run_test(
            f"Buy Upgrade: {cheapest_upgrade.get('name', 'Unknown')}",
            "POST",
            f"upgrades/{upgrade_id}/buy",
            200
        )
        if success:
            print(f"   New level: {response.get('new_level', 'Unknown')}")
            print(f"   Price paid: ${response.get('price', 0)}")
        return success

    def test_affordable_products(self):
        """Test that affordable products (< $100) exist"""
        success, response = self.run_test(
            "Check Affordable Products",
            "GET",
            "products",
            200
        )
        if success and isinstance(response, list):
            affordable_products = [p for p in response if p.get('price', float('inf')) < 100]
            print(f"   Found {len(affordable_products)} affordable products (< $100)")
            
            expected_affordable = [
                "USB ASIC Miner",
                "Starter Cloud Mining",
                "Basic Cloud Mining", 
                "Mini Mining Contract"
            ]
            
            found_names = [p.get('name', '') for p in affordable_products]
            for expected in expected_affordable:
                if any(expected in name for name in found_names):
                    print(f"   ✅ Found expected affordable product: {expected}")
                else:
                    print(f"   ⚠️  Missing expected affordable product: {expected}")
            
            return len(affordable_products) >= 4  # Should have at least 4 affordable products
        return False

def main():
    print("🚀 Starting mAInet API Testing...")
    print("=" * 50)
    
    tester = mAInetAPITester()
    
    # Test sequence
    tests = [
        ("Root Endpoint", tester.test_root_endpoint),
        ("User Registration", tester.test_register),
        ("User Login", tester.test_login),
        ("Get User Profile", tester.test_get_user_profile),
        ("Initialize Sample Data", tester.test_init_sample_data),
        ("Get All Products", tester.test_get_products),
        ("Get Products by Category", tester.test_get_products_by_category),
        ("Get All Tasks", tester.test_get_tasks),
        ("Complete Task", tester.test_complete_task),
        ("Get My Tasks", tester.test_get_my_tasks),
        ("Create Deposit", tester.test_create_deposit),
        ("Get My Deposits", tester.test_get_my_deposits),
        ("Get User Stats", tester.test_get_stats),
        ("Test Referral System", tester.test_referral_system),
    ]
    
    failed_tests = []
    
    for test_name, test_func in tests:
        try:
            if not test_func():
                failed_tests.append(test_name)
        except Exception as e:
            print(f"❌ {test_name} - Exception: {str(e)}")
            failed_tests.append(test_name)
    
    # Print results
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS")
    print("=" * 50)
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Tests Failed: {len(failed_tests)}")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run*100):.1f}%")
    
    if failed_tests:
        print(f"\n❌ Failed Tests:")
        for test in failed_tests:
            print(f"   - {test}")
    else:
        print(f"\n✅ All tests passed!")
    
    return 0 if len(failed_tests) == 0 else 1

if __name__ == "__main__":
    sys.exit(main())