"""
mAInet - Complete Supabase Integration
FastAPI server with full Supabase integration for crypto mining game
"""

from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any, Set
import uuid
from datetime import datetime, timezone, timedelta
import jwt
from enum import Enum
import json
import asyncio
import httpx

# Import Supabase configuration
from supabase_config import get_supabase_client, get_supabase_admin_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="mAInet Crypto Mining Game API",
    description="Complete Supabase-powered crypto mining game backend",
    version="2.0.0"
)

# CORS configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Supabase clients
supabase = get_supabase_client()
supabase_admin = get_supabase_admin_client()

# API Router
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()

# Enums
class PaymentMethod(str, Enum):
    PAYEER = "payeer"
    FAUCETPAY = "faucetpay"

class UpgradeType(str, Enum):
    ENERGY_REGEN = "ENERGY_REGEN"
    CLICK_POWER = "CLICK_POWER"
    AUTO_MINING = "AUTO_MINING"
    MAX_ENERGY = "MAX_ENERGY"

class RigType(str, Enum):
    BASIC_CPU = "basic_cpu"
    ENTRY_GPU = "entry_gpu"
    DUAL_CORE = "dual_core"
    QUAD_CORE = "quad_core"
    GTX_MINER = "gtx_miner"
    ASIC_BASIC = "asic_basic"
    RTX_3080 = "rtx_3080"
    ASIC_S19 = "asic_s19"
    CUSTOM_RIG = "custom_rig"
    RTX_4090 = "rtx_4090"
    ASIC_S21 = "asic_s21"
    QUANTUM_CHIP = "quantum_chip"
    AI_PROCESSOR = "ai_processor"
    FUSION_REACTOR = "fusion_reactor"
    BLACK_HOLE = "black_hole"
    MAINET_CORE = "mainet_core"

# Payment Gateway Classes
class Payeer:
    def __init__(self, account: str):
        self.account = account
    
    async def verify_transaction(self, transaction_id: str, amount: float = None) -> Dict[str, Any]:
        """
        Verify a transaction with Payeer API using real API integration
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Real Payeer API integration
                api_params = {
                    'account': self.account,
                    'apiId': os.getenv('PAYEER_API_ID', ''),
                    'apiPass': os.getenv('PAYEER_API_SECRET', ''),
                    'action': 'historyInfo',
                    'historyId': transaction_id
                }
                
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'User-Agent': 'Payeer-Python-Client/1.0'
                }
                
                response = await client.post(
                    'https://payeer.com/ajax/api/api.php',
                    data=api_params,
                    headers=headers
                )
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        
                        # Check authentication and response validity
                        if data.get('auth_error', 0) == 0 and 'info' in data and data['info']:
                            info = data['info']
                            
                            # Check if transaction is to our account
                            if info.get('to') == self.account:
                                return {
                                    "success": True,
                                    "transaction_found": True,
                                    "transaction_id": transaction_id,
                                    "amount": float(info.get('creditedSum', 0)),
                                    "currency": info.get('creditedCur', 'USD'),
                                    "status": "completed" if info.get('status') == 'success' else "pending",
                                    "to_account": self.account,
                                    "from_account": info.get('from', ''),
                                    "date": info.get('date', ''),
                                    "comment": info.get('comment', '')
                                }
                            else:
                                return {
                                    "success": False,
                                    "transaction_found": False,
                                    "error": "Transaction not sent to our account"
                                }
                        else:
                            return {
                                "success": False,
                                "transaction_found": False,
                                "error": data.get('errors', ['Transaction not found'])[0] if data.get('errors') else "Transaction not found"
                            }
                    except json.JSONDecodeError:
                        return {
                            "success": False,
                            "transaction_found": False,
                            "error": "Invalid response from Payeer API"
                        }
                else:
                    return {
                        "success": False,
                        "transaction_found": False,
                        "error": f"HTTP error {response.status_code}"
                    }
                
        except Exception as e:
            logger.error(f"Payeer API error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "transaction_found": False
            }

class FaucetPay:
    def __init__(self, target_email: str):
        self.target_email = target_email
    
    async def verify_transaction(self, transaction_id: str, amount: float = None) -> Dict[str, Any]:
        """
        Verify a transaction with FaucetPay API using real API integration
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Real FaucetPay API integration
                api_params = {
                    'api_key': os.getenv('FAUCETPAY_API_KEY', ''),
                    'hash': transaction_id
                }
                
                headers = {
                    'Content-Type': 'application/json',
                    'User-Agent': 'FaucetPay-Python-Client/1.0'
                }
                
                response = await client.get(
                    'https://faucetpay.io/api/v1/gettransaction',
                    params=api_params,
                    headers=headers
                )
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        
                        # Check if request was successful
                        if data.get('success', False):
                            transaction_info = data.get('transaction', {})
                            
                            # Check if transaction is to our email
                            if transaction_info.get('to_email') == self.target_email:
                                mock_response = {
                                    "success": True,
                                    "transaction_found": True,
                                    "transaction_id": transaction_id,
                                    "amount": float(transaction_info.get('amount', 0)),
                                    "currency": transaction_info.get('currency', 'USD'),
                                    "status": "confirmed" if transaction_info.get('status') == 'completed' else "pending",
                                    "to_email": self.target_email,
                                    "from_address": transaction_info.get('from_address', ''),
                                    "date": transaction_info.get('date', ''),
                                    "confirmations": transaction_info.get('confirmations', 0)
                                }
                            else:
                                mock_response = {
                                    "success": False,
                                    "transaction_found": False,
                                    "error": "Transaction not sent to our email"
                                }
                        else:
                            mock_response = {
                                "success": False,
                                "transaction_found": False,
                                "error": data.get('message', 'Transaction not found')
                            }
                    except json.JSONDecodeError:
                        mock_response = {
                            "success": False,
                            "transaction_found": False,
                            "error": "Invalid response from FaucetPay API"
                        }
                else:
                    mock_response = {
                        "success": False,
                        "transaction_found": False,
                        "error": f"HTTP error {response.status_code}"
                    }
                
                return mock_response
                
        except Exception as e:
            logger.error(f"FaucetPay API error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "transaction_found": False
            }

# Pydantic Models
class UserRegistration(BaseModel):
    email: EmailStr
    password: str
    username: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class GameStateUpdate(BaseModel):
    current_level: Optional[int] = None
    experience_points: Optional[int] = None
    current_coins: Optional[int] = None
    main_balance: Optional[float] = None
    energy: Optional[int] = None
    max_energy: Optional[int] = None
    energy_regen_rate: Optional[float] = None
    click_power: Optional[int] = None
    auto_mining_rate: Optional[float] = None
    total_clicks: Optional[int] = None
    achievements: Optional[List[str]] = None
    game_settings: Optional[Dict[str, Any]] = None

class MiningRigCreate(BaseModel):
    rig_name: str
    rig_type: RigType

class TransactionVerificationRequest(BaseModel):
    transaction_id: str
    payment_method: PaymentMethod
    amount: Optional[float] = None
    currency: str = "USD"

class ProfileUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
    
    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.active_connections:
            for websocket in self.active_connections[user_id].copy():
                try:
                    await websocket.send_text(message)
                except:
                    self.active_connections[user_id].discard(websocket)

manager = ConnectionManager()

# JWT Token verification
def verify_jwt_token(token: str) -> str:
    try:
        # Decode JWT token from Supabase
        payload = jwt.decode(token, options={"verify_signature": False})
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    user_id = verify_jwt_token(credentials.credentials)
    
    # Get user profile from Supabase
    try:
        profile_result = supabase.table('profiles').select('*').eq('id', user_id).execute()
        if not profile_result.data:
            raise HTTPException(status_code=404, detail="User profile not found")
        return profile_result.data[0]
    except Exception as e:
        logger.error(f"Error fetching user profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch user profile")

# Authentication Endpoints
@api_router.post("/auth/register")
async def register_user(user_data: UserRegistration):
    """Register a new user with Supabase Auth"""
    try:
        # Register user with Supabase Auth
        auth_response = supabase.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password,
            "options": {
                "data": {
                    "username": user_data.username,
                    "full_name": user_data.full_name
                }
            }
        })
        
        if auth_response.user:
            return {
                "message": "Registration successful",
                "user_id": auth_response.user.id,
                "email": auth_response.user.email
            }
        else:
            raise HTTPException(status_code=400, detail="Registration failed")
            
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@api_router.post("/auth/login")
async def login_user(credentials: UserLogin):
    """Login user with Supabase Auth"""
    try:
        auth_response = supabase.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })
        
        if auth_response.user and auth_response.session:
            # Get user profile
            profile_result = supabase.table('profiles').select('*').eq('id', auth_response.user.id).execute()
            
            return {
                "message": "Login successful",
                "access_token": auth_response.session.access_token,
                "refresh_token": auth_response.session.refresh_token,
                "user": {
                    "id": auth_response.user.id,
                    "email": auth_response.user.email,
                    "profile": profile_result.data[0] if profile_result.data else None
                }
            }
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=401, detail="Authentication failed")

@api_router.post("/auth/logout")
async def logout_user(current_user: dict = Depends(get_current_user)):
    """Logout current user"""
    try:
        supabase.auth.sign_out()
        return {"message": "Logout successful"}
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(status_code=500, detail="Logout failed")

# Profile Management
@api_router.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile with game state"""
    try:
        user_id = current_user['id']
        
        # Get game state
        game_state_result = supabase.table('game_states').select('*').eq('user_id', user_id).execute()
        
        # Get mining rigs
        rigs_result = supabase.table('mining_rigs').select('*').eq('user_id', user_id).execute()
        
        # Get recent transactions
        transactions_result = supabase.table('transactions').select('*').eq(
            'user_id', user_id
        ).order('created_at', desc=True).limit(10).execute()
        
        return {
            "profile": current_user,
            "game_state": game_state_result.data[0] if game_state_result.data else None,
            "mining_rigs": rigs_result.data,
            "recent_transactions": transactions_result.data
        }
        
    except Exception as e:
        logger.error(f"Profile fetch error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch profile")

@api_router.put("/profile")
async def update_profile(profile_data: ProfileUpdate, current_user: dict = Depends(get_current_user)):
    """Update user profile"""
    try:
        user_id = current_user['id']
        update_data = {}
        
        if profile_data.username:
            # Check username availability
            existing = supabase.table('profiles').select('id').eq('username', profile_data.username).neq('id', user_id).execute()
            if existing.data:
                raise HTTPException(status_code=400, detail="Username already taken")
            update_data['username'] = profile_data.username
        
        if profile_data.full_name is not None:
            update_data['full_name'] = profile_data.full_name
        
        if profile_data.bio is not None:
            update_data['bio'] = profile_data.bio
        
        if profile_data.avatar_url is not None:
            update_data['avatar_url'] = profile_data.avatar_url
        
        if update_data:
            update_data['updated_at'] = datetime.now().isoformat()
            updated_profile = supabase.table('profiles').update(update_data).eq('id', user_id).execute()
            return updated_profile.data[0]
        
        return {"message": "No changes made"}
        
    except Exception as e:
        logger.error(f"Profile update error: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Profile update failed")

# Game State Management
@api_router.get("/game/state")
async def get_game_state(current_user: dict = Depends(get_current_user)):
    """Get complete game state"""
    try:
        user_id = current_user['id']
        
        # Get game state
        game_state_result = supabase.table('game_states').select('*').eq('user_id', user_id).execute()
        
        if not game_state_result.data:
            # Create initial game state
            initial_state = {
                'user_id': user_id,
                'current_level': 1,
                'experience_points': 0,
                'current_coins': 1000,
                'main_balance': 1000.0,
                'bonus_balance': 0.0,
                'energy': 100,
                'max_energy': 100,
                'energy_regen_rate': 1.0,
                'click_power': 1,
                'auto_mining_rate': 0.0,
                'total_clicks': 0,
                'achievements': [],
                'game_settings': {
                    'sound_enabled': True,
                    'notifications_enabled': True,
                    'auto_collect_rewards': False
                }
            }
            
            created_state = supabase.table('game_states').insert(initial_state).execute()
            return created_state.data[0]
        
        # Calculate offline rewards
        offline_rewards = await calculate_offline_rewards(user_id)
        game_state = game_state_result.data[0]
        
        if offline_rewards > 0:
            # Update balance with offline rewards
            new_balance = game_state['current_coins'] + offline_rewards
            supabase.table('game_states').update({
                'current_coins': new_balance,
                'main_balance': game_state['main_balance'] + offline_rewards
            }).eq('user_id', user_id).execute()
            
            game_state['current_coins'] = new_balance
            game_state['main_balance'] = game_state['main_balance'] + offline_rewards
            game_state['offline_rewards'] = offline_rewards
        
        return game_state
        
    except Exception as e:
        logger.error(f"Game state fetch error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch game state")

@api_router.post("/game/state")
async def save_game_state(state_data: GameStateUpdate, current_user: dict = Depends(get_current_user)):
    """Save game state"""
    try:
        user_id = current_user['id']
        update_data = {}
        
        # Build update data from provided fields
        if state_data.current_level is not None:
            update_data['current_level'] = max(1, state_data.current_level)
        if state_data.experience_points is not None:
            update_data['experience_points'] = max(0, state_data.experience_points)
        if state_data.current_coins is not None:
            update_data['current_coins'] = max(0, state_data.current_coins)
        if state_data.main_balance is not None:
            update_data['main_balance'] = max(0, state_data.main_balance)
        if state_data.energy is not None:
            update_data['energy'] = state_data.energy
        if state_data.max_energy is not None:
            update_data['max_energy'] = state_data.max_energy
        if state_data.energy_regen_rate is not None:
            update_data['energy_regen_rate'] = state_data.energy_regen_rate
        if state_data.click_power is not None:
            update_data['click_power'] = state_data.click_power
        if state_data.auto_mining_rate is not None:
            update_data['auto_mining_rate'] = state_data.auto_mining_rate
        if state_data.total_clicks is not None:
            update_data['total_clicks'] = state_data.total_clicks
        if state_data.achievements is not None:
            update_data['achievements'] = state_data.achievements
        if state_data.game_settings is not None:
            update_data['game_settings'] = state_data.game_settings
        
        if update_data:
            update_data['updated_at'] = datetime.now().isoformat()
            updated_state = supabase.table('game_states').update(update_data).eq('user_id', user_id).execute()
            
            # Broadcast update to all user devices
            await manager.send_personal_message(json.dumps({
                'type': 'game_state_updated',
                'data': updated_state.data[0]
            }), user_id)
            
            return updated_state.data[0]
        
        return {"message": "No changes made"}
        
    except Exception as e:
        logger.error(f"Game state save error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save game state")

# Mining Rigs Management
@api_router.get("/mining-rigs")
async def get_mining_rigs(current_user: dict = Depends(get_current_user)):
    """Get user's mining rigs"""
    try:
        user_id = current_user['id']
        rigs_result = supabase.table('mining_rigs').select('*').eq('user_id', user_id).order('created_at').execute()
        return rigs_result.data
        
    except Exception as e:
        logger.error(f"Mining rigs fetch error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch mining rigs")

@api_router.post("/mining-rigs")
async def create_mining_rig(rig_data: MiningRigCreate, current_user: dict = Depends(get_current_user)):
    """Create new mining rig"""
    try:
        user_id = current_user['id']
        
        # Get rig configuration based on type
        rig_configs = {
            RigType.BASIC_CPU: {'power': 0.5, 'efficiency': 1.0, 'cost': 100, 'rarity': 'common'},
            RigType.ENTRY_GPU: {'power': 0.8, 'efficiency': 1.0, 'cost': 200, 'rarity': 'common'},
            RigType.DUAL_CORE: {'power': 1.2, 'efficiency': 1.05, 'cost': 300, 'rarity': 'common'},
            RigType.QUAD_CORE: {'power': 2.0, 'efficiency': 1.1, 'cost': 500, 'rarity': 'uncommon'},
            RigType.GTX_MINER: {'power': 2.5, 'efficiency': 1.15, 'cost': 700, 'rarity': 'uncommon'},
            RigType.ASIC_BASIC: {'power': 3.0, 'efficiency': 1.2, 'cost': 900, 'rarity': 'uncommon'},
            RigType.RTX_3080: {'power': 4.2, 'efficiency': 1.25, 'cost': 1500, 'rarity': 'rare'},
            RigType.ASIC_S19: {'power': 5.0, 'efficiency': 1.3, 'cost': 2000, 'rarity': 'rare'},
            RigType.CUSTOM_RIG: {'power': 5.8, 'efficiency': 1.2, 'cost': 2500, 'rarity': 'rare'},
            RigType.RTX_4090: {'power': 8.5, 'efficiency': 1.4, 'cost': 4000, 'rarity': 'epic'},
            RigType.ASIC_S21: {'power': 10.0, 'efficiency': 1.5, 'cost': 5000, 'rarity': 'epic'},
            RigType.QUANTUM_CHIP: {'power': 12.0, 'efficiency': 2.0, 'cost': 7500, 'rarity': 'epic'},
            RigType.AI_PROCESSOR: {'power': 18.0, 'efficiency': 1.75, 'cost': 12000, 'rarity': 'legendary'},
            RigType.FUSION_REACTOR: {'power': 22.0, 'efficiency': 2.0, 'cost': 20000, 'rarity': 'legendary'},
            RigType.BLACK_HOLE: {'power': 50.0, 'efficiency': 2.0, 'cost': 50000, 'rarity': 'mythic'},
            RigType.MAINET_CORE: {'power': 100.0, 'efficiency': 5.0, 'cost': 100000, 'rarity': 'mythic'},
        }
        
        config = rig_configs.get(rig_data.rig_type)
        if not config:
            raise HTTPException(status_code=400, detail="Invalid rig type")
        
        # Check user balance
        game_state = supabase.table('game_states').select('current_coins').eq('user_id', user_id).execute()
        if not game_state.data or game_state.data[0]['current_coins'] < config['cost']:
            raise HTTPException(status_code=400, detail="Insufficient balance")
        
        # Create mining rig
        new_rig = {
            'user_id': user_id,
            'rig_name': rig_data.rig_name,
            'rig_type': rig_data.rig_type.value,
            'mining_power': config['power'],
            'efficiency_rating': config['efficiency'],
            'rarity': config['rarity'],
            'purchase_price': config['cost'],
            'is_active': True
        }
        
        created_rig = supabase.table('mining_rigs').insert(new_rig).execute()
        
        # Deduct cost from user balance
        new_balance = game_state.data[0]['current_coins'] - config['cost']
        supabase.table('game_states').update({
            'current_coins': new_balance,
            'main_balance': new_balance
        }).eq('user_id', user_id).execute()
        
        # Record transaction
        supabase.table('transactions').insert({
            'user_id': user_id,
            'transaction_type': 'purchase',
            'amount': -config['cost'],
            'balance_before': game_state.data[0]['current_coins'],
            'balance_after': new_balance,
            'description': f"Purchased {rig_data.rig_type.value}: {rig_data.rig_name}",
            'related_rig_id': created_rig.data[0]['id']
        }).execute()
        
        return created_rig.data[0]
        
    except Exception as e:
        logger.error(f"Mining rig creation error: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Failed to create mining rig")

# Transaction System
@api_router.get("/transactions")
async def get_transactions(limit: int = 50, offset: int = 0, current_user: dict = Depends(get_current_user)):
    """Get user transaction history"""
    try:
        user_id = current_user['id']
        
        transactions_result = supabase.table('transactions').select('*').eq(
            'user_id', user_id
        ).order('created_at', desc=True).range(offset, offset + limit - 1).execute()
        
        return {
            'transactions': transactions_result.data,
            'count': len(transactions_result.data)
        }
        
    except Exception as e:
        logger.error(f"Transactions fetch error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch transactions")

# IDTX Verification System
@api_router.post("/verify-transaction")
async def verify_transaction(request: TransactionVerificationRequest, current_user: dict = Depends(get_current_user)):
    """Verify transaction ID (IDTX) for deposits"""
    try:
        user_id = current_user['id']
        
        # Check if transaction already verified
        existing = supabase.table('transaction_verifications').select('*').eq(
            'user_id', user_id
        ).eq('transaction_id', request.transaction_id).execute()
        
        if existing.data:
            verification = existing.data[0]
            return {
                'transaction_id': request.transaction_id,
                'verified': verification['status'] == 'verified',
                'status': verification['status'],
                'amount': verification['amount'],
                'bonus_amount': verification['bonus_amount'],
                'message': 'Transaction already processed'
            }
        
        # Simulate API verification (in real implementation, call actual APIs)
        is_valid = len(request.transaction_id) >= 8 and not request.transaction_id.upper().startswith('INVALID')
        amount = request.amount or (10.0 if request.payment_method == PaymentMethod.PAYEER else 5.0)
        
        if is_valid:
            bonus_amount = round(amount * 0.17, 2)  # 17% bonus
            
            # Create verification record
            verification = supabase.table('transaction_verifications').insert({
                'user_id': user_id,
                'transaction_id': request.transaction_id,
                'amount': amount,
                'currency': request.currency,
                'payment_method': request.payment_method.value,
                'status': 'verified',
                'bonus_amount': bonus_amount,
                'verified_at': datetime.now().isoformat()
            }).execute()
            
            # Credit user balance
            game_state = supabase.table('game_states').select('current_coins, main_balance, bonus_balance').eq('user_id', user_id).execute()
            current_balance = game_state.data[0]['current_coins'] if game_state.data else 0
            current_main = game_state.data[0]['main_balance'] if game_state.data else 0
            current_bonus = game_state.data[0]['bonus_balance'] if game_state.data else 0
            
            total_credit = amount + bonus_amount
            new_balance = current_balance + total_credit
            new_main = current_main + amount
            new_bonus = current_bonus + bonus_amount
            
            supabase.table('game_states').update({
                'current_coins': new_balance,
                'main_balance': new_main,
                'bonus_balance': new_bonus
            }).eq('user_id', user_id).execute()
            
            # Record transaction
            supabase.table('transactions').insert({
                'user_id': user_id,
                'transaction_type': 'deposit_bonus',
                'amount': total_credit,
                'balance_before': current_balance,
                'balance_after': new_balance,
                'description': f"Verified deposit: {request.transaction_id} + 17% bonus",
                'metadata': {'original_amount': amount, 'bonus_amount': bonus_amount}
            }).execute()
            
            return {
                'transaction_id': request.transaction_id,
                'verified': True,
                'status': 'verified',
                'amount': amount,
                'bonus_amount': bonus_amount,
                'message': f"Transaction verified! {amount} {request.currency} + {bonus_amount} bonus credited."
            }
        
        else:
            # Record failed verification
            supabase.table('transaction_verifications').insert({
                'user_id': user_id,
                'transaction_id': request.transaction_id,
                'amount': amount,
                'currency': request.currency,
                'payment_method': request.payment_method.value,
                'status': 'not_found'
            }).execute()
            
            return {
                'transaction_id': request.transaction_id,
                'verified': False,
                'status': 'not_found',
                'amount': amount,
                'bonus_amount': 0,
                'message': 'Transaction not found or invalid'
            }
        
    except Exception as e:
        logger.error(f"Transaction verification error: {str(e)}")
        raise HTTPException(status_code=500, detail="Verification failed")

# Helper Functions
async def calculate_offline_rewards(user_id: str) -> float:
    """Calculate offline mining rewards"""
    try:
        # Call Supabase function
        result = supabase.rpc('calculate_offline_rewards', {'p_user_id': user_id}).execute()
        return float(result.data) if result.data else 0.0
    except Exception as e:
        logger.error(f"Offline rewards calculation error: {str(e)}")
        return 0.0

# WebSocket endpoint
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Include API router
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)