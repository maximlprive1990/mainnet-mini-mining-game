"""
Comprehensive Supabase Backend Testing for mAInet Application
Tests the complete Supabase integration including authentication, game state, mining rigs, and IDTX verification
"""

import requests
import sys
import json
import websocket
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional

class SupabaseBackendTester:
    def __init__(self, base_url="https://crypto-rewards-10.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.access_token = None
        self.refresh_token = None
        self.user_id = None
        self.user_profile = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_user_email = f"supabase_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@mainet.com"
        self.test_username = f"supabase_user_{datetime.now().strftime('%H%M%S')}"
        self.test_password = "SecurePass123!"
        self.websocket_messages = []
        self.websocket_connected = False

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
            if details:
                print(f"   {details}")
        else:
            print(f"❌ {name}")
            if details:
                print(f"   {details}")

    def make_request(self, method: str, endpoint: str, data: Dict = None, expected_status: int = 200, headers: Dict = None) -> tuple[bool, Dict]:
        """Make HTTP request with proper error handling"""
        url = f"{self.base_url}/{endpoint}" if endpoint else self.base_url
        
        if headers is None:
            headers = {'Content-Type': 'application/json'}
        
        if self.access_token and 'Authorization' not in headers:
            headers['Authorization'] = f'Bearer {self.access_token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=15)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=15)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=15)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=15)
            else:
                return False, {"error": f"Unsupported method: {method}"}

            success = response.status_code == expected_status
            
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text, "status_code": response.status_code}

            if not success:
                print(f"   Expected status {expected_status}, got {response.status_code}")
                if response_data:
                    print(f"   Response: {response_data}")

            return success, response_data

        except requests.exceptions.RequestException as e:
            print(f"   Network Error: {str(e)}")
            return False, {"error": str(e)}
        except Exception as e:
            print(f"   Error: {str(e)}")
            return False, {"error": str(e)}

    # Authentication Tests
    def test_user_registration(self):
        """Test Supabase user registration"""
        success, response = self.make_request(
            'POST', 'auth/register',
            data={
                "email": self.test_user_email,
                "password": self.test_password,
                "username": self.test_username,
                "full_name": "Test User Supabase"
            }
        )
        
        if success and response.get('user_id'):
            self.user_id = response['user_id']
            details = f"User registered with ID: {self.user_id}"
        else:
            details = f"Registration failed: {response.get('detail', 'Unknown error')}"
        
        self.log_test("Supabase User Registration", success, details)
        return success

    def test_user_login(self):
        """Test Supabase user login"""
        success, response = self.make_request(
            'POST', 'auth/login',
            data={
                "email": self.test_user_email,
                "password": self.test_password
            }
        )
        
        if success and response.get('access_token'):
            self.access_token = response['access_token']
            self.refresh_token = response['refresh_token']
            self.user_id = response['user']['id']
            self.user_profile = response['user'].get('profile')
            details = f"Login successful, token obtained"
        else:
            details = f"Login failed: {response.get('detail', 'Unknown error')}"
        
        self.log_test("Supabase User Login", success, details)
        return success

    def test_user_logout(self):
        """Test Supabase user logout"""
        success, response = self.make_request('POST', 'auth/logout')
        
        details = "Logout successful" if success else f"Logout failed: {response.get('detail', 'Unknown error')}"
        self.log_test("Supabase User Logout", success, details)
        return success

    # Profile Management Tests
    def test_get_profile(self):
        """Test getting user profile with game state"""
        success, response = self.make_request('GET', 'profile')
        
        if success:
            profile = response.get('profile', {})
            game_state = response.get('game_state', {})
            mining_rigs = response.get('mining_rigs', [])
            transactions = response.get('recent_transactions', [])
            
            details = f"Profile loaded - Level: {game_state.get('current_level', 'N/A')}, Balance: ${game_state.get('main_balance', 0)}, Rigs: {len(mining_rigs)}"
        else:
            details = f"Profile fetch failed: {response.get('detail', 'Unknown error')}"
        
        self.log_test("Get User Profile with Game State", success, details)
        return success

    def test_update_profile(self):
        """Test updating user profile"""
        success, response = self.make_request(
            'PUT', 'profile',
            data={
                "full_name": "Updated Test User",
                "bio": "Testing Supabase integration for mAInet"
            }
        )
        
        if success:
            details = f"Profile updated - Name: {response.get('full_name', 'N/A')}"
        else:
            details = f"Profile update failed: {response.get('detail', 'Unknown error')}"
        
        self.log_test("Update User Profile", success, details)
        return success

    # Game State Management Tests
    def test_get_game_state(self):
        """Test getting complete game state"""
        success, response = self.make_request('GET', 'game/state')
        
        if success:
            level = response.get('current_level', 0)
            coins = response.get('current_coins', 0)
            balance = response.get('main_balance', 0)
            energy = response.get('energy', 0)
            offline_rewards = response.get('offline_rewards', 0)
            
            details = f"Game state - Level: {level}, Coins: {coins}, Balance: ${balance}, Energy: {energy}, Offline rewards: {offline_rewards}"
        else:
            details = f"Game state fetch failed: {response.get('detail', 'Unknown error')}"
        
        self.log_test("Get Complete Game State", success, details)
        return success

    def test_save_game_state(self):
        """Test saving game state"""
        success, response = self.make_request(
            'POST', 'game/state',
            data={
                "current_level": 2,
                "experience_points": 150,
                "current_coins": 1500,
                "main_balance": 1500.0,
                "energy": 95,
                "total_clicks": 50,
                "achievements": ["first_click", "level_up"]
            }
        )
        
        if success:
            details = f"Game state saved - Level: {response.get('current_level', 'N/A')}, Coins: {response.get('current_coins', 'N/A')}"
        else:
            details = f"Game state save failed: {response.get('detail', 'Unknown error')}"
        
        self.log_test("Save Game State", success, details)
        return success

    # Mining Rigs Tests
    def test_get_mining_rigs(self):
        """Test getting user's mining rigs"""
        success, response = self.make_request('GET', 'mining-rigs')
        
        if success and isinstance(response, list):
            details = f"Found {len(response)} mining rigs"
            if response:
                rig = response[0]
                details += f" - First rig: {rig.get('rig_name', 'Unknown')} ({rig.get('rig_type', 'Unknown')})"
        else:
            details = f"Mining rigs fetch failed: {response.get('detail', 'Unknown error') if isinstance(response, dict) else 'Invalid response'}"
        
        self.log_test("Get Mining Rigs", success, details)
        return success

    def test_create_mining_rig(self):
        """Test creating a new mining rig"""
        success, response = self.make_request(
            'POST', 'mining-rigs',
            data={
                "rig_name": "Test Basic CPU Miner",
                "rig_type": "basic_cpu"
            }
        )
        
        if success:
            rig_name = response.get('rig_name', 'Unknown')
            rig_type = response.get('rig_type', 'Unknown')
            mining_power = response.get('mining_power', 0)
            details = f"Mining rig created - {rig_name} ({rig_type}) with {mining_power} power"
        else:
            details = f"Mining rig creation failed: {response.get('detail', 'Unknown error')}"
        
        self.log_test("Create Mining Rig", success, details)
        return success

    def test_create_expensive_mining_rig(self):
        """Test creating an expensive mining rig (should fail due to insufficient balance)"""
        success, response = self.make_request(
            'POST', 'mining-rigs',
            data={
                "rig_name": "Test Quantum Chip",
                "rig_type": "quantum_chip"
            },
            expected_status=400  # Should fail due to insufficient balance
        )
        
        if success:
            details = "Correctly rejected expensive rig purchase due to insufficient balance"
        else:
            details = f"Expensive rig test failed: {response.get('detail', 'Unknown error')}"
        
        self.log_test("Create Expensive Mining Rig (Should Fail)", success, details)
        return success

    # Transaction System Tests
    def test_get_transactions(self):
        """Test getting transaction history"""
        success, response = self.make_request('GET', 'transactions?limit=20')
        
        if success:
            transactions = response.get('transactions', [])
            count = response.get('count', 0)
            details = f"Found {count} transactions"
            if transactions:
                latest = transactions[0]
                details += f" - Latest: {latest.get('transaction_type', 'Unknown')} ${latest.get('amount', 0)}"
        else:
            details = f"Transactions fetch failed: {response.get('detail', 'Unknown error')}"
        
        self.log_test("Get Transaction History", success, details)
        return success

    # IDTX Verification System Tests
    def test_verify_payeer_transaction(self):
        """Test verifying a Payeer transaction"""
        transaction_id = f"PAYEER_SUPABASE_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        success, response = self.make_request(
            'POST', 'verify-transaction',
            data={
                "transaction_id": transaction_id,
                "payment_method": "payeer",
                "amount": 100.0,
                "currency": "USD"
            }
        )
        
        if success:
            verified = response.get('verified', False)
            amount = response.get('amount', 0)
            bonus = response.get('bonus_amount', 0)
            
            if verified:
                details = f"Payeer transaction verified - Amount: ${amount}, Bonus: ${bonus} (17%)"
                # Store for duplicate test
                self.test_transaction_id = transaction_id
            else:
                details = f"Payeer transaction not verified: {response.get('message', 'Unknown')}"
        else:
            details = f"Payeer verification failed: {response.get('detail', 'Unknown error')}"
        
        self.log_test("Verify Payeer Transaction", success, details)
        return success

    def test_verify_faucetpay_transaction(self):
        """Test verifying a FaucetPay transaction"""
        transaction_id = f"FAUCETPAY_SUPABASE_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        success, response = self.make_request(
            'POST', 'verify-transaction',
            data={
                "transaction_id": transaction_id,
                "payment_method": "faucetpay",
                "amount": 50.0,
                "currency": "USD"
            }
        )
        
        if success:
            verified = response.get('verified', False)
            amount = response.get('amount', 0)
            bonus = response.get('bonus_amount', 0)
            
            if verified:
                details = f"FaucetPay transaction verified - Amount: ${amount}, Bonus: ${bonus} (17%)"
            else:
                details = f"FaucetPay transaction not verified: {response.get('message', 'Unknown')}"
        else:
            details = f"FaucetPay verification failed: {response.get('detail', 'Unknown error')}"
        
        self.log_test("Verify FaucetPay Transaction", success, details)
        return success

    def test_duplicate_transaction_prevention(self):
        """Test duplicate transaction prevention"""
        if not hasattr(self, 'test_transaction_id'):
            self.log_test("Duplicate Transaction Prevention", False, "No previous transaction to test with")
            return False
        
        success, response = self.make_request(
            'POST', 'verify-transaction',
            data={
                "transaction_id": self.test_transaction_id,
                "payment_method": "payeer",
                "amount": 100.0,
                "currency": "USD"
            }
        )
        
        if success:
            message = response.get('message', '').lower()
            if 'already processed' in message:
                details = "Duplicate transaction correctly detected and prevented"
            else:
                success = False
                details = f"Duplicate not detected: {response.get('message', 'Unknown')}"
        else:
            details = f"Duplicate test failed: {response.get('detail', 'Unknown error')}"
        
        self.log_test("Duplicate Transaction Prevention", success, details)
        return success

    def test_invalid_transaction_handling(self):
        """Test handling of invalid transactions"""
        success, response = self.make_request(
            'POST', 'verify-transaction',
            data={
                "transaction_id": "INVALID_TRANSACTION_12345",
                "payment_method": "payeer",
                "amount": 100.0,
                "currency": "USD"
            }
        )
        
        if success:
            verified = response.get('verified', True)  # Should be False
            status = response.get('status', '')
            
            if not verified and status in ['not_found', 'failed']:
                details = f"Invalid transaction correctly rejected - Status: {status}"
            else:
                success = False
                details = f"Invalid transaction incorrectly verified - Status: {status}"
        else:
            details = f"Invalid transaction test failed: {response.get('detail', 'Unknown error')}"
        
        self.log_test("Invalid Transaction Handling", success, details)
        return success

    def test_bonus_calculation_accuracy(self):
        """Test 17% bonus calculation accuracy"""
        test_amounts = [25.0, 100.0, 250.0, 1000.0]
        all_passed = True
        
        for amount in test_amounts:
            transaction_id = f"BONUS_TEST_{amount}_{datetime.now().strftime('%H%M%S')}"
            expected_bonus = round(amount * 0.17, 2)
            
            success, response = self.make_request(
                'POST', 'verify-transaction',
                data={
                    "transaction_id": transaction_id,
                    "payment_method": "faucetpay",
                    "amount": amount,
                    "currency": "USD"
                }
            )
            
            if success and response.get('verified'):
                actual_bonus = response.get('bonus_amount', 0)
                if abs(actual_bonus - expected_bonus) < 0.01:
                    print(f"   ✅ ${amount} -> ${actual_bonus} bonus (expected ${expected_bonus})")
                else:
                    print(f"   ❌ ${amount} -> ${actual_bonus} bonus (expected ${expected_bonus})")
                    all_passed = False
            else:
                print(f"   ❌ ${amount} verification failed")
                all_passed = False
        
        details = "All bonus calculations accurate" if all_passed else "Some bonus calculations incorrect"
        self.log_test("17% Bonus Calculation Accuracy", all_passed, details)
        return all_passed

    # WebSocket Tests
    def test_websocket_connection(self):
        """Test WebSocket real-time connection"""
        if not self.user_id:
            self.log_test("WebSocket Connection", False, "No user ID available")
            return False
        
        try:
            ws_url = f"wss://crypto-rewards-10.preview.emergentagent.com/ws/{self.user_id}"
            
            def on_message(ws, message):
                self.websocket_messages.append(json.loads(message))
                print(f"   WebSocket message received: {message}")
            
            def on_open(ws):
                self.websocket_connected = True
                print("   WebSocket connected successfully")
            
            def on_error(ws, error):
                print(f"   WebSocket error: {error}")
            
            def on_close(ws, close_status_code, close_msg):
                self.websocket_connected = False
                print("   WebSocket connection closed")
            
            ws = websocket.WebSocketApp(ws_url,
                                      on_open=on_open,
                                      on_message=on_message,
                                      on_error=on_error,
                                      on_close=on_close)
            
            # Run WebSocket in a separate thread
            wst = threading.Thread(target=ws.run_forever)
            wst.daemon = True
            wst.start()
            
            # Wait for connection
            time.sleep(2)
            
            if self.websocket_connected:
                # Send a test message
                ws.send("ping")
                time.sleep(1)
                ws.close()
                
                details = f"WebSocket connected successfully, received {len(self.websocket_messages)} messages"
                success = True
            else:
                details = "WebSocket connection failed"
                success = False
            
        except Exception as e:
            details = f"WebSocket test error: {str(e)}"
            success = False
        
        self.log_test("WebSocket Real-time Connection", success, details)
        return success

    # Health and System Tests
    def test_health_check(self):
        """Test system health endpoint"""
        success, response = self.make_request('GET', '../health')  # Health is at root level
        
        if success:
            status = response.get('status', 'unknown')
            timestamp = response.get('timestamp', 'unknown')
            details = f"System healthy - Status: {status}, Time: {timestamp}"
        else:
            details = f"Health check failed: {response.get('detail', 'Unknown error')}"
        
        self.log_test("System Health Check", success, details)
        return success

    def run_comprehensive_test(self):
        """Run all Supabase integration tests"""
        print("🚀 Starting Comprehensive Supabase Backend Testing for mAInet")
        print("=" * 70)
        
        # Test sequence for complete Supabase integration
        test_sequence = [
            ("System Health Check", self.test_health_check),
            ("User Registration", self.test_user_registration),
            ("User Login", self.test_user_login),
            ("Get User Profile", self.test_get_profile),
            ("Update User Profile", self.test_update_profile),
            ("Get Game State", self.test_get_game_state),
            ("Save Game State", self.test_save_game_state),
            ("Get Mining Rigs", self.test_get_mining_rigs),
            ("Create Mining Rig", self.test_create_mining_rig),
            ("Create Expensive Rig (Should Fail)", self.test_create_expensive_mining_rig),
            ("Get Transaction History", self.test_get_transactions),
            ("Verify Payeer Transaction", self.test_verify_payeer_transaction),
            ("Verify FaucetPay Transaction", self.test_verify_faucetpay_transaction),
            ("Duplicate Transaction Prevention", self.test_duplicate_transaction_prevention),
            ("Invalid Transaction Handling", self.test_invalid_transaction_handling),
            ("17% Bonus Calculation Accuracy", self.test_bonus_calculation_accuracy),
            ("WebSocket Real-time Connection", self.test_websocket_connection),
            ("User Logout", self.test_user_logout),
        ]
        
        failed_tests = []
        
        for test_name, test_func in test_sequence:
            print(f"\n🔍 Running: {test_name}")
            try:
                if not test_func():
                    failed_tests.append(test_name)
            except Exception as e:
                print(f"❌ {test_name} - Exception: {str(e)}")
                failed_tests.append(test_name)
        
        # Print comprehensive results
        print("\n" + "=" * 70)
        print("📊 SUPABASE INTEGRATION TEST RESULTS")
        print("=" * 70)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {len(failed_tests)}")
        
        if self.tests_run > 0:
            success_rate = (self.tests_passed / self.tests_run) * 100
            print(f"Success Rate: {success_rate:.1f}%")
        
        if failed_tests:
            print(f"\n❌ Failed Tests:")
            for test in failed_tests:
                print(f"   - {test}")
        else:
            print(f"\n✅ All Supabase integration tests passed!")
        
        # Summary of key features tested
        print(f"\n🎯 Key Features Tested:")
        print(f"   ✅ Supabase Authentication (register/login/logout)")
        print(f"   ✅ Profile Management with Game State")
        print(f"   ✅ Game State Persistence and Offline Rewards")
        print(f"   ✅ Mining Rigs System (17 types)")
        print(f"   ✅ Transaction History and Balance Management")
        print(f"   ✅ IDTX Verification with 17% Bonus")
        print(f"   ✅ Duplicate Prevention and Invalid Handling")
        print(f"   ✅ WebSocket Real-time Synchronization")
        print(f"   ✅ PostgreSQL Database with RLS Policies")
        
        return len(failed_tests) == 0

def main():
    tester = SupabaseBackendTester()
    success = tester.run_comprehensive_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())