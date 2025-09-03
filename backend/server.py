from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import bcrypt
import jwt
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')

# Enums
class ProductCategory(str, Enum):
    EQUIPMENT = "equipment"
    CLOUD_MINING = "cloud_mining"
    CONTRACTS = "contracts"

class TaskType(str, Enum):
    TELEGRAM_JOIN = "telegram_join"
    SOCIAL_FOLLOW = "social_follow"
    DAILY_LOGIN = "daily_login"
    REFERRAL = "referral"

class PaymentMethod(str, Enum):
    PAYEER = "payeer"
    FAUCETPAY = "faucetpay"

class UpgradeType(str, Enum):
    ENERGY_REGEN = "energy_regen"
    DOUBLE_CLICK = "double_click"
    AUTO_MINING = "auto_mining"
    MAX_ENERGY = "max_energy"
    MAX_ENERGY = "max_energy"

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    username: str
    password_hash: str
    balance: float = 0.0
    bonus_balance: float = 0.0
    total_earned: float = 0.0
    referral_code: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    referred_by: Optional[str] = None
    is_verified: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    referral_code: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Product(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    price: float
    category: ProductCategory
    image_url: str
    stock: int = 100
    features: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    reward: float
    task_type: TaskType
    requirements: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserTask(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    task_id: str
    completed: bool = False
    completed_at: Optional[datetime] = None
    verified: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Deposit(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    amount: float
    bonus_amount: float
    payment_method: PaymentMethod
    transaction_id: str
    status: str = "pending"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DepositCreate(BaseModel):
    amount: float
    payment_method: PaymentMethod
    transaction_id: str

# Game Models
class UserGame(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    energy: int = 100
    max_energy: int = 100
    energy_regen_rate: int = 1  # per minute
    click_power: int = 1
    auto_mining_rate: float = 0.0  # tokens per minute
    total_clicks: int = 0
    game_balance: float = 0.0
    last_energy_update: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Upgrade(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    upgrade_type: UpgradeType
    base_price: float
    price_multiplier: float = 1.5
    effect_value: float
    max_level: int = 20
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserUpgrade(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    upgrade_id: str
    level: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ClickAction(BaseModel):
    clicks: int = 1

# Helper functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(user_id: str) -> str:
    payload = {"user_id": user_id, "exp": datetime.now(timezone.utc).timestamp() + 86400}  # 24 hours
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_jwt_token(token: str) -> str:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload["user_id"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    user_id = verify_jwt_token(credentials.credentials)
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user)

async def get_or_create_user_game(user_id: str) -> UserGame:
    user_game = await db.user_games.find_one({"user_id": user_id})
    if not user_game:
        user_game_obj = UserGame(user_id=user_id)
        await db.user_games.insert_one(user_game_obj.dict())
        return user_game_obj
    return UserGame(**user_game)

async def update_energy(user_game: UserGame) -> UserGame:
    now = datetime.now(timezone.utc)
    
    # Ensure last_energy_update has timezone info
    last_update = user_game.last_energy_update
    if last_update.tzinfo is None:
        last_update = last_update.replace(tzinfo=timezone.utc)
    
    time_diff = (now - last_update).total_seconds() / 60  # minutes
    
    energy_gained = int(time_diff * user_game.energy_regen_rate)
    if energy_gained > 0:
        user_game.energy = min(user_game.max_energy, user_game.energy + energy_gained)
        user_game.last_energy_update = now
        
        # Update auto mining
        auto_tokens = time_diff * user_game.auto_mining_rate
        if auto_tokens > 0:
            user_game.game_balance += auto_tokens
            
        await db.user_games.update_one(
            {"user_id": user_game.user_id},
            {"$set": user_game.dict()}
        )
    
    return user_game

# Routes
@api_router.get("/")
async def root():
    return {"message": "mAInet Airdrop & Mining Shop API"}

# Auth routes
@api_router.post("/auth/register")
async def register(user_data: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"$or": [{"email": user_data.email}, {"username": user_data.username}]})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Create user
    hashed_password = hash_password(user_data.password)
    user = User(
        email=user_data.email,
        username=user_data.username,
        password_hash=hashed_password,
        referred_by=user_data.referral_code
    )
    
    await db.users.insert_one(user.dict())
    
    # Create user game profile
    user_game = UserGame(user_id=user.id)
    await db.user_games.insert_one(user_game.dict())
    
    # Give referral bonus if applicable
    if user_data.referral_code:
        referrer = await db.users.find_one({"referral_code": user_data.referral_code})
        if referrer:
            await db.users.update_one(
                {"id": referrer["id"]},
                {"$inc": {"bonus_balance": 50.0, "total_earned": 50.0}}
            )
    
    token = create_jwt_token(user.id)
    return {"message": "User created successfully", "token": token, "user_id": user.id}

@api_router.post("/auth/login")
async def login(login_data: UserLogin):
    user = await db.users.find_one({"email": login_data.email})
    if not user or not verify_password(login_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Update last login
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"last_login": datetime.now(timezone.utc)}}
    )
    
    token = create_jwt_token(user["id"])
    return {"token": token, "user_id": user["id"]}

@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# Products routes
@api_router.get("/products", response_model=List[Product])
async def get_products(category: Optional[ProductCategory] = None):
    query = {"category": category} if category else {}
    products = await db.products.find(query).to_list(length=None)
    return [Product(**product) for product in products]

@api_router.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str):
    product = await db.products.find_one({"id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return Product(**product)

# Tasks routes
@api_router.get("/tasks", response_model=List[Task])
async def get_tasks():
    tasks = await db.tasks.find({"is_active": True}).to_list(length=None)
    return [Task(**task) for task in tasks]

@api_router.post("/tasks/{task_id}/complete")
async def complete_task(task_id: str, current_user: User = Depends(get_current_user)):
    # Check if task exists
    task = await db.tasks.find_one({"id": task_id, "is_active": True})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check if already completed
    user_task = await db.user_tasks.find_one({"user_id": current_user.id, "task_id": task_id})
    if user_task and user_task["completed"]:
        raise HTTPException(status_code=400, detail="Task already completed")
    
    # Create or update user task
    user_task_data = UserTask(
        user_id=current_user.id,
        task_id=task_id,
        completed=True,
        completed_at=datetime.now(timezone.utc),
        verified=True  # Auto-verify for now
    )
    
    if user_task:
        await db.user_tasks.update_one(
            {"id": user_task["id"]},
            {"$set": user_task_data.dict()}
        )
    else:
        await db.user_tasks.insert_one(user_task_data.dict())
    
    # Add reward to user balance
    task_obj = Task(**task)
    await db.users.update_one(
        {"id": current_user.id},
        {"$inc": {"balance": task_obj.reward, "total_earned": task_obj.reward}}
    )
    
    return {"message": "Task completed successfully", "reward": task_obj.reward}

@api_router.get("/tasks/my")
async def get_my_tasks(current_user: User = Depends(get_current_user)):
    user_tasks = await db.user_tasks.find({"user_id": current_user.id}).to_list(length=None)
    return [UserTask(**user_task) for user_task in user_tasks]

# Deposits routes
@api_router.post("/deposits")
async def create_deposit(deposit_data: DepositCreate, current_user: User = Depends(get_current_user)):
    bonus_amount = deposit_data.amount * 0.17  # 17% bonus
    
    deposit = Deposit(
        user_id=current_user.id,
        amount=deposit_data.amount,
        bonus_amount=bonus_amount,
        payment_method=deposit_data.payment_method,
        transaction_id=deposit_data.transaction_id,
        status="pending"
    )
    
    await db.deposits.insert_one(deposit.dict())
    
    # For demo purposes, auto-approve deposits
    total_amount = deposit_data.amount + bonus_amount
    await db.users.update_one(
        {"id": current_user.id},
        {"$inc": {"balance": deposit_data.amount, "bonus_balance": bonus_amount}}
    )
    
    await db.deposits.update_one(
        {"id": deposit.id},
        {"$set": {"status": "approved"}}
    )
    
    return {"message": "Deposit processed successfully", "bonus_amount": bonus_amount}

@api_router.get("/deposits/my")
async def get_my_deposits(current_user: User = Depends(get_current_user)):
    deposits = await db.deposits.find({"user_id": current_user.id}).to_list(length=None)
    return [Deposit(**deposit) for deposit in deposits]

# Game routes
@api_router.get("/game/status")
async def get_game_status(current_user: User = Depends(get_current_user)):
    user_game = await get_or_create_user_game(current_user.id)
    user_game = await update_energy(user_game)
    return user_game

@api_router.post("/game/click")
async def click_action(click_data: ClickAction, current_user: User = Depends(get_current_user)):
    user_game = await get_or_create_user_game(current_user.id)
    user_game = await update_energy(user_game)
    
    if user_game.energy < click_data.clicks:
        raise HTTPException(status_code=400, detail="Not enough energy")
    
    # Calculate earnings
    tokens_earned = click_data.clicks * user_game.click_power * 0.1  # 0.1 token per click
    
    # Update game stats
    user_game.energy -= click_data.clicks
    user_game.total_clicks += click_data.clicks
    user_game.game_balance += tokens_earned
    
    await db.user_games.update_one(
        {"user_id": current_user.id},
        {"$set": user_game.dict()}
    )
    
    return {
        "tokens_earned": tokens_earned,
        "energy_remaining": user_game.energy,
        "total_clicks": user_game.total_clicks
    }

@api_router.post("/game/transfer")
async def transfer_game_balance(current_user: User = Depends(get_current_user)):
    user_game = await get_or_create_user_game(current_user.id)
    
    if user_game.game_balance <= 0:
        raise HTTPException(status_code=400, detail="No balance to transfer")
    
    # Transfer game balance to main balance
    await db.users.update_one(
        {"id": current_user.id},
        {"$inc": {"balance": user_game.game_balance, "total_earned": user_game.game_balance}}
    )
    
    transferred_amount = user_game.game_balance
    user_game.game_balance = 0.0
    
    await db.user_games.update_one(
        {"user_id": current_user.id},
        {"$set": {"game_balance": 0.0}}
    )
    
    return {"transferred_amount": transferred_amount}

# Upgrades routes
@api_router.get("/upgrades")
async def get_upgrades():
    upgrades = await db.upgrades.find().to_list(length=None)
    return [Upgrade(**upgrade) for upgrade in upgrades]

@api_router.get("/upgrades/my")
async def get_my_upgrades(current_user: User = Depends(get_current_user)):
    user_upgrades = await db.user_upgrades.find({"user_id": current_user.id}).to_list(length=None)
    return [UserUpgrade(**upgrade) for upgrade in user_upgrades]

@api_router.post("/upgrades/{upgrade_id}/buy")
async def buy_upgrade(upgrade_id: str, current_user: User = Depends(get_current_user)):
    upgrade = await db.upgrades.find_one({"id": upgrade_id})
    if not upgrade:
        raise HTTPException(status_code=404, detail="Upgrade not found")
    
    upgrade_obj = Upgrade(**upgrade)
    
    # Get current level
    user_upgrade = await db.user_upgrades.find_one({"user_id": current_user.id, "upgrade_id": upgrade_id})
    current_level = user_upgrade["level"] if user_upgrade else 0
    
    if current_level >= upgrade_obj.max_level:
        raise HTTPException(status_code=400, detail="Upgrade at max level")
    
    # Calculate price
    price = upgrade_obj.base_price * (upgrade_obj.price_multiplier ** current_level)
    
    if current_user.balance < price:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    # Deduct balance
    await db.users.update_one(
        {"id": current_user.id},
        {"$inc": {"balance": -price}}
    )
    
    # Update upgrade level
    new_level = current_level + 1
    if user_upgrade:
        await db.user_upgrades.update_one(
            {"user_id": current_user.id, "upgrade_id": upgrade_id},
            {"$set": {"level": new_level}}
        )
    else:
        new_user_upgrade = UserUpgrade(
            user_id=current_user.id,
            upgrade_id=upgrade_id,
            level=new_level
        )
        await db.user_upgrades.insert_one(new_user_upgrade.dict())
    
    # Apply upgrade effects to user game
    user_game = await get_or_create_user_game(current_user.id)
    
    if upgrade_obj.upgrade_type == UpgradeType.ENERGY_REGEN:
        user_game.energy_regen_rate += upgrade_obj.effect_value
        user_game.max_energy += 10  # Bonus max energy
    elif upgrade_obj.upgrade_type == UpgradeType.DOUBLE_CLICK:
        user_game.click_power += upgrade_obj.effect_value
    elif upgrade_obj.upgrade_type == UpgradeType.AUTO_MINING:
        user_game.auto_mining_rate += upgrade_obj.effect_value
    elif upgrade_obj.upgrade_type == UpgradeType.MAX_ENERGY:
        user_game.max_energy += upgrade_obj.effect_value
        user_game.energy = min(user_game.energy + upgrade_obj.effect_value, user_game.max_energy)  # Also add current energy
    
    await db.user_games.update_one(
        {"user_id": current_user.id},
        {"$set": user_game.dict()}
    )
    
    return {"message": "Upgrade purchased successfully", "new_level": new_level, "price": price}

# Stats route
@api_router.get("/stats")
async def get_stats(current_user: User = Depends(get_current_user)):
    user_tasks_count = await db.user_tasks.count_documents({"user_id": current_user.id, "completed": True})
    total_deposits = await db.deposits.aggregate([
        {"$match": {"user_id": current_user.id, "status": "approved"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]).to_list(length=1)
    
    total_deposited = total_deposits[0]["total"] if total_deposits else 0
    
    # Get game stats
    user_game = await get_or_create_user_game(current_user.id)
    user_game = await update_energy(user_game)
    
    return {
        "balance": current_user.balance,
        "bonus_balance": current_user.bonus_balance,
        "total_earned": current_user.total_earned,
        "completed_tasks": user_tasks_count,
        "total_deposited": total_deposited,
        "referral_code": current_user.referral_code,
        "game_stats": {
            "energy": user_game.energy,
            "max_energy": user_game.max_energy,
            "click_power": user_game.click_power,
            "auto_mining_rate": user_game.auto_mining_rate,
            "total_clicks": user_game.total_clicks,
            "game_balance": user_game.game_balance
        }
    }

# Initialize sample data
@api_router.post("/init-data")
async def init_sample_data():
    # Clear existing data
    await db.products.delete_many({})
    await db.tasks.delete_many({})
    await db.upgrades.delete_many({})
    
    # Sample products - More affordable options
    products = [
        # Affordable Mining Equipment
        Product(
            name="USB ASIC Miner",
            description="Mini ASIC miner perfect for beginners - 330 MH/s",
            price=49.99,
            category=ProductCategory.EQUIPMENT,
            image_url="https://images.unsplash.com/photo-1695903213536-33162a52246d?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzh8MHwxfHNlYXJjaHwxfHxjcnlwdG9jdXJyZW5jeSUyMG1pbmluZ3xlbnwwfHx8fDE3NTY5Mjc1MDd8MA&ixlib=rb-4.1.0&q=85",
            features=["330 MH/s", "USB Powered", "Plug & Play", "Low Power"]
        ),
        Product(
            name="GTX 1660 Super",
            description="Budget-friendly GPU perfect for crypto mining",
            price=199.99,
            category=ProductCategory.EQUIPMENT,
            image_url="https://images.unsplash.com/photo-1634672350437-f9632adc9c3f?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzh8MHwxfHNlYXJjaHwzfHxjcnlwdG9jdXJyZW5jeSUyMG1pbmluZ3xlbnwwfHx8fDE3NTY5Mjc1MDd8MA&ixlib=rb-4.1.0&q=85",
            features=["6GB GDDR6", "125W TDP", "Ethereum Ready", "Great ROI"]
        ),
        Product(
            name="ASIC Miner S19 Pro",
            description="High-performance Bitcoin mining hardware with 110 TH/s hashrate",
            price=2500.0,
            category=ProductCategory.EQUIPMENT,
            image_url="https://images.unsplash.com/photo-1695903213536-33162a52246d?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzh8MHwxfHNlYXJjaHwxfHxjcnlwdG9jdXJyZW5jeSUyMG1pbmluZ3xlbnwwfHx8fDE3NTY5Mjc1MDd8MA&ixlib=rb-4.1.0&q=85",
            features=["110 TH/s", "3250W Power", "SHA-256 Algorithm", "Water Cooling"]
        ),
        Product(
            name="RTX 4090 Mining Rig",
            description="Professional GPU mining setup with 8x RTX 4090 cards",
            price=15000.0,
            category=ProductCategory.EQUIPMENT,
            image_url="https://images.unsplash.com/photo-1634672350437-f9632adc9c3f?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzh8MHwxfHNlYXJjaHwzfHxjcnlwdG9jdXJyZW5jeSUyMG1pbmluZ3xlbnwwfHx8fDE3NTY5Mjc1MDd8MA&ixlib=rb-4.1.0&q=85",
            features=["8x RTX 4090", "High Efficiency", "Multiple Algorithms", "Remote Management"]
        ),
        
        # Affordable Cloud Mining
        Product(
            name="Starter Cloud Mining 100 GH/s",
            description="Perfect for beginners - 30 days Bitcoin cloud mining",
            price=29.99,
            category=ProductCategory.CLOUD_MINING,
            image_url="https://images.unsplash.com/photo-1707075891545-41b982930351?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzh8MHwxfHNlYXJjaHwyfHxjcnlwdG9jdXJyZW5jeSUyMG1pbmluZ3xlbnwwfHx8fDE3NTY5Mjc1MDd8MA&ixlib=rb-4.1.0&q=85",
            features=["100 GH/s", "30 Days", "Daily Payouts", "No Maintenance"]
        ),
        Product(
            name="Basic Cloud Mining 500 GH/s",
            description="3 months Bitcoin cloud mining contract",
            price=99.99,
            category=ProductCategory.CLOUD_MINING,
            image_url="https://images.unsplash.com/photo-1707075891545-41b982930351?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzh8MHwxfHNlYXJjaHwyfHxjcnlwdG9jdXJyZW5jeSUyMG1pbmluZ3xlbnwwfHx8fDE3NTY5Mjc1MDd8MA&ixlib=rb-4.1.0&q=85",
            features=["500 GH/s", "3 Months", "Instant Start", "24/7 Support"]
        ),
        Product(
            name="Bitcoin Cloud Mining 1 TH/s",
            description="1 year Bitcoin cloud mining contract",
            price=500.0,
            category=ProductCategory.CLOUD_MINING,
            image_url="https://images.unsplash.com/photo-1707075891545-41b982930351?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzh8MHwxfHNlYXJjaHwyfHxjcnlwdG9jdXJyZW5jeSUyMG1pbmluZ3xlbnwwfHx8fDE3NTY5Mjc1MDd8MA&ixlib=rb-4.1.0&q=85",
            features=["1 TH/s Hashrate", "1 Year Contract", "Daily Payouts", "Zero Maintenance"]
        ),
        Product(
            name="Ethereum Cloud Mining 100 MH/s",
            description="6 months Ethereum cloud mining package",
            price=300.0,
            category=ProductCategory.CLOUD_MINING,
            image_url="https://images.unsplash.com/photo-1694219782948-afcab5c095d3?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzh8MHwxfHNlYXJjaHw0fHxjcnlwdG9jdXJyZW5jeSUyMG1pbmluZ3xlbnwwfHx8fDE3NTY5Mjc1MDd8MA&ixlib=rb-4.1.0&q=85",
            features=["100 MH/s Hashrate", "6 Months Contract", "Instant Activation", "24/7 Support"]
        ),
        
        # Mining Contracts
        Product(
            name="Mini Mining Contract",
            description="Small mining contract perfect for testing",
            price=99.99,
            category=ProductCategory.CONTRACTS,
            image_url="https://images.unsplash.com/photo-1645273603365-659e5622ea78?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1NzZ8MHwxfHNlYXJjaHw0fHxmdXR1cmlzdGljJTIwZGFya3xlbnwwfHx8fDE3NTY5Mjc1MTN8MA&ixlib=rb-4.1.0&q=85",
            features=["90 Days Duration", "Multiple Coins", "Easy Start", "Support Included"]
        ),
        Product(
            name="Premium Mining Contract",
            description="Exclusive mining contract with guaranteed returns",
            price=1000.0,
            category=ProductCategory.CONTRACTS,
            image_url="https://images.unsplash.com/photo-1645273603365-659e5622ea78?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1NzZ8MHwxfHNlYXJjaHw0fHxmdXR1cmlzdGljJTIwZGFya3xlbnwwfHx8fDE3NTY5Mjc1MTN8MA&ixlib=rb-4.1.0&q=85",
            features=["Guaranteed ROI", "Multi-Coin Mining", "Flexible Terms", "Priority Support"]
        )
    ]
    
    for product in products:
        await db.products.insert_one(product.dict())
    
    # Sample tasks
    tasks = [
        Task(
            title="Join Telegram Channel",
            description="Join our official Telegram channel and stay updated",
            reward=10.0,
            task_type=TaskType.TELEGRAM_JOIN,
            requirements="@mAInet_official"
        ),
        Task(
            title="Daily Login Bonus",
            description="Login daily to claim your bonus",
            reward=5.0,
            task_type=TaskType.DAILY_LOGIN,
            requirements="Login every day"
        ),
        Task(
            title="Follow Twitter",
            description="Follow our Twitter account for updates",
            reward=15.0,
            task_type=TaskType.SOCIAL_FOLLOW,
            requirements="@mAInet_crypto"
        ),
        Task(
            title="Refer a Friend",
            description="Invite friends and earn bonus",
            reward=50.0,
            task_type=TaskType.REFERRAL,
            requirements="Share referral link"
        )
    ]
    
    for task in tasks:
        await db.tasks.insert_one(task.dict())
    
    # Sample upgrades
    upgrades = [
        Upgrade(
            name="Energy Regeneration",
            description="Increase energy regeneration rate",
            upgrade_type=UpgradeType.ENERGY_REGEN,
            base_price=50.0,
            price_multiplier=1.5,
            effect_value=1.0,  # +1 energy per minute
            max_level=20
        ),
        Upgrade(
            name="Double Click Power",
            description="Increase tokens earned per click",
            upgrade_type=UpgradeType.DOUBLE_CLICK,
            base_price=100.0,
            price_multiplier=1.8,
            effect_value=1.0,  # +1 click power
            max_level=15
        ),
        Upgrade(
            name="Auto Mining Bot",
            description="Automatically earn tokens over time",
            upgrade_type=UpgradeType.AUTO_MINING,
            base_price=200.0,
            price_multiplier=2.0,
            effect_value=0.5,  # +0.5 tokens per minute
            max_level=10
        )
    ]
    
    for upgrade in upgrades:
        await db.upgrades.insert_one(upgrade.dict())
    
    return {"message": "Sample data initialized successfully"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()