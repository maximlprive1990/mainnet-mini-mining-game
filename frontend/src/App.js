import React, { useState, useEffect, useCallback, useRef } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import axios from "axios";
import { Toaster } from "./components/ui/sonner";
import { toast } from "sonner";
import { 
  Zap, 
  Cpu, 
  ShoppingCart, 
  User, 
  LogOut, 
  Plus,
  Coins,
  Users,
  Gift,
  TrendingUp,
  Shield,
  Star,
  ExternalLink,
  Copy,
  ChevronRight,
  Hash,
  Wallet,
  Clock,
  CheckCircle,
  MousePointer,
  Bolt,
  Cog,
  ArrowUp,
  Play,
  Gauge,
  Sparkles,
  Target,
  Zap as ZapIcon
} from "lucide-react";
import { Button } from "./components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Input } from "./components/ui/input";
import { Label } from "./components/ui/label";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "./components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./components/ui/select";
import { Progress } from "./components/ui/progress";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = React.createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      fetchUser();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchUser = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch user:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { email, password });
      const { token: newToken } = response.data;
      localStorage.setItem('token', newToken);
      setToken(newToken);
      toast.success('Connexion réussie!');
      return true;
    } catch (error) {
      toast.error('Identifiants invalides');
      return false;
    }
  };

  const register = async (email, username, password, referralCode) => {
    try {
      const response = await axios.post(`${API}/auth/register`, {
        email,
        username,
        password,
        referral_code: referralCode || undefined
      });
      const { token: newToken } = response.data;
      localStorage.setItem('token', newToken);
      setToken(newToken);
      toast.success('Inscription réussie!');
      return true;
    } catch (error) {
      toast.error('Erreur lors de l\'inscription');
      return false;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    toast.success('Déconnexion réussie');
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading, token, fetchUser }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Components
const Header = () => {
  const { user, logout } = useAuth();

  return (
    <header className="cyber-header">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="cyber-logo">
              <Zap className="w-8 h-8 text-cyber-green" />
              <span className="text-2xl font-bold text-white">mAInet</span>
            </div>
            <Badge variant="outline" className="cyber-badge">
              Airdrop 2026
            </Badge>
          </div>
          
          {user && (
            <div className="flex items-center space-x-4">
              <div className="cyber-stats">
                <div className="flex items-center space-x-2">
                  <Coins className="w-4 h-4 text-cyber-green" />
                  <span className="text-cyber-green font-mono">{user.balance?.toFixed(2) || '0.00'}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Gift className="w-4 h-4 text-yellow-400" />
                  <span className="text-yellow-400 font-mono">{user.bonus_balance?.toFixed(2) || '0.00'}</span>
                </div>
              </div>
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={logout}
                className="cyber-button-ghost"
              >
                <LogOut className="w-4 h-4" />
              </Button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

const ClickGame = () => {
  const { token, fetchUser } = useAuth();
  const [gameStatus, setGameStatus] = useState(null);
  const [upgrades, setUpgrades] = useState([]);
  const [userUpgrades, setUserUpgrades] = useState([]);
  const [clickAnimation, setClickAnimation] = useState(null);
  const gameInterval = useRef(null);
  const autoMiningInterval = useRef(null);
  
  useEffect(() => {
    fetchGameData();
    
    // Update energy every 30 seconds
    gameInterval.current = setInterval(fetchGameStatus, 30000);
    
    return () => {
      if (gameInterval.current) clearInterval(gameInterval.current);
      if (autoMiningInterval.current) clearInterval(autoMiningInterval.current);
    };
  }, []);
  
  useEffect(() => {
    // Auto mining simulation
    if (gameStatus && gameStatus.auto_mining_rate > 0) {
      autoMiningInterval.current = setInterval(() => {
        setGameStatus(prev => ({
          ...prev,
          game_balance: prev.game_balance + (prev.auto_mining_rate / 60) // per second
        }));
      }, 1000);
    }
    
    return () => {
      if (autoMiningInterval.current) clearInterval(autoMiningInterval.current);
    };
  }, [gameStatus?.auto_mining_rate]);

  const fetchGameData = async () => {
    try {
      const [statusRes, upgradesRes, userUpgradesRes] = await Promise.all([
        axios.get(`${API}/game/status`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/upgrades`),
        axios.get(`${API}/upgrades/my`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      
      setGameStatus(statusRes.data);
      setUpgrades(upgradesRes.data);
      setUserUpgrades(userUpgradesRes.data);
    } catch (error) {
      console.error('Failed to fetch game data:', error);
    }
  };

  const fetchGameStatus = async () => {
    try {
      const response = await axios.get(`${API}/game/status`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setGameStatus(response.data);
    } catch (error) {
      console.error('Failed to fetch game status:', error);
    }
  };

  const handleClick = async (event) => {
    if (!gameStatus || gameStatus.energy < 1) return;
    
    const rect = event.currentTarget.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    
    // Show click animation
    setClickAnimation({ x, y, id: Date.now() });
    setTimeout(() => setClickAnimation(null), 1000);
    
    try {
      const response = await axios.post(`${API}/game/click`, 
        { clicks: 1 }, 
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      // Update local state immediately for better UX
      setGameStatus(prev => ({
        ...prev,
        energy: response.data.energy_remaining,
        total_clicks: response.data.total_clicks,
        game_balance: prev.game_balance + response.data.tokens_earned
      }));
      
    } catch (error) {
      toast.error('Erreur lors du clic');
    }
  };

  const buyUpgrade = async (upgradeId) => {
    try {
      await axios.post(`${API}/upgrades/${upgradeId}/buy`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success('Amélioration achetée!');
      await fetchGameData();
      await fetchUser(); // Update main balance
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erreur lors de l\'achat');
    }
  };

  const transferBalance = async () => {
    try {
      const response = await axios.post(`${API}/game/transfer`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success(`${response.data.transferred_amount.toFixed(2)} tokens transférés!`);
      await fetchGameStatus();
      await fetchUser();
    } catch (error) {
      toast.error('Erreur lors du transfert');
    }
  };

  const getUpgradeLevel = (upgradeId) => {
    const userUpgrade = userUpgrades.find(u => u.upgrade_id === upgradeId);
    return userUpgrade ? userUpgrade.level : 0;
  };

  const getUpgradePrice = (upgrade, level) => {
    return upgrade.base_price * Math.pow(upgrade.price_multiplier, level);
  };

  if (!gameStatus) return <div className="cyber-loading">Chargement du jeu...</div>;

  const energyPercentage = (gameStatus.energy / gameStatus.max_energy) * 100;

  return (
    <div className="click-game-container">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Game Area */}
        <div className="lg:col-span-2">
          <Card className="cyber-card click-game-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MousePointer className="w-5 h-5 text-cyber-green" />
                Jeu de Clic - Mining
              </CardTitle>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm text-gray-400">Solde du Jeu</Label>
                  <div className="flex items-center gap-2">
                    <Coins className="w-4 h-4 text-cyber-green" />
                    <span className="text-xl font-bold text-cyber-green">
                      {gameStatus.game_balance?.toFixed(3) || '0.000'}
                    </span>
                  </div>
                </div>
                <div>
                  <Label className="text-sm text-gray-400">Total Clics</Label>
                  <div className="flex items-center gap-2">
                    <Target className="w-4 h-4 text-blue-400" />
                    <span className="text-xl font-bold text-blue-400">
                      {gameStatus.total_clicks || 0}
                    </span>
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Energy Bar */}
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <Label className="flex items-center gap-2">
                    <Bolt className="w-4 h-4 text-yellow-400" />
                    Énergie
                  </Label>
                  <span className="text-sm font-mono">
                    {gameStatus.energy}/{gameStatus.max_energy}
                  </span>
                </div>
                <Progress 
                  value={energyPercentage} 
                  className="energy-bar"
                />
                <div className="text-xs text-gray-400">
                  Régénération: {gameStatus.energy_regen_rate}/min
                </div>
              </div>

              {/* Click Button */}
              <div className="click-area">
                <button
                  className="click-button"
                  onClick={handleClick}
                  disabled={gameStatus.energy < 1}
                >
                  <div className="click-button-content">
                    <ZapIcon className="w-16 h-16" />
                    <span className="click-text">CLIQUER</span>
                    <span className="click-power">+{gameStatus.click_power * 0.1} tokens</span>
                  </div>
                  
                  {/* Click Animation */}
                  {clickAnimation && (
                    <div 
                      className="click-animation"
                      style={{ left: clickAnimation.x, top: clickAnimation.y }}
                    >
                      +{(gameStatus.click_power * 0.1).toFixed(3)}
                    </div>
                  )}
                </button>
              </div>

              {/* Auto Mining Status */}
              {gameStatus.auto_mining_rate > 0 && (
                <div className="auto-mining-status">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Cog className="w-4 h-4 text-purple-400 animate-spin" />
                      <span className="text-purple-400">Auto Mining Actif</span>
                    </div>
                    <span className="text-purple-400 font-mono">
                      +{gameStatus.auto_mining_rate.toFixed(2)}/min
                    </span>
                  </div>
                </div>
              )}

              {/* Transfer Button */}
              {gameStatus.game_balance > 0 && (
                <Button 
                  onClick={transferBalance}
                  className="cyber-button w-full"
                >
                  <ArrowUp className="w-4 h-4 mr-2" />
                  Transférer vers le Solde Principal
                </Button>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Upgrades */}
        <div>
          <Card className="cyber-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-purple-400" />
                Améliorations
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {upgrades.map((upgrade) => {
                const level = getUpgradeLevel(upgrade.id);
                const price = getUpgradePrice(upgrade, level);
                const maxed = level >= upgrade.max_level;

                return (
                  <div key={upgrade.id} className="upgrade-card">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        {upgrade.upgrade_type === 'energy_regen' && <Bolt className="w-4 h-4 text-yellow-400" />}
                        {upgrade.upgrade_type === 'double_click' && <MousePointer className="w-4 h-4 text-blue-400" />}
                        {upgrade.upgrade_type === 'auto_mining' && <Cog className="w-4 h-4 text-purple-400" />}
                        {upgrade.upgrade_type === 'max_energy' && <Gauge className="w-4 h-4 text-orange-400" />}
                        <span className="font-semibold text-white text-sm">{upgrade.name}</span>
                      </div>
                      <Badge variant="outline" className="cyber-badge text-xs">
                        Niveau {level}
                      </Badge>
                    </div>
                    
                    <p className="text-xs text-gray-400 mb-3">{upgrade.description}</p>
                    
                    <div className="flex items-center justify-between">
                      <div className="text-xs">
                        <div className="text-cyber-green font-mono">
                          {maxed ? 'MAX' : `${price.toFixed(0)} tokens`}
                        </div>
                        <div className="text-gray-400">
                          +{upgrade.effect_value} {upgrade.upgrade_type === 'energy_regen' ? '/min' : 
                                                   upgrade.upgrade_type === 'double_click' ? 'puissance' : 
                                                   '/min auto'}
                        </div>
                      </div>
                      <Button
                        size="sm"
                        onClick={() => buyUpgrade(upgrade.id)}
                        disabled={maxed}
                        className="cyber-button text-xs"
                      >
                        {maxed ? 'MAX' : 'Acheter'}
                      </Button>
                    </div>
                  </div>
                );
              })}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

const Dashboard = () => {
  const { user, token, fetchUser } = useAuth();
  const [stats, setStats] = useState(null);
  const [products, setProducts] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [deposits, setDeposits] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [depositModal, setDepositModal] = useState(false);
  const [depositForm, setDepositForm] = useState({
    amount: '',
    payment_method: 'payeer',
    transaction_id: ''
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, productsRes, tasksRes, depositsRes] = await Promise.all([
        axios.get(`${API}/stats`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/products`),
        axios.get(`${API}/tasks`),
        axios.get(`${API}/deposits/my`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      
      setStats(statsRes.data);
      setProducts(productsRes.data);
      setTasks(tasksRes.data);
      setDeposits(depositsRes.data);
    } catch (error) {
      console.error('Failed to fetch data:', error);
    }
  };

  const completeTask = async (taskId) => {
    try {
      await axios.post(`${API}/tasks/${taskId}/complete`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Tâche complétée!');
      fetchData();
      fetchUser();
    } catch (error) {
      toast.error('Erreur lors de la completion de la tâche');
    }
  };

  const submitDeposit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/deposits`, depositForm, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Dépôt soumis avec succès! Bonus de 17% ajouté.');
      setDepositModal(false);
      setDepositForm({ amount: '', payment_method: 'payeer', transaction_id: '' });
      fetchData();
      fetchUser();
    } catch (error) {
      toast.error('Erreur lors du dépôt');
    }
  };

  const copyReferralCode = () => {
    navigator.clipboard.writeText(user.referral_code);
    toast.success('Code de parrainage copié!');
  };

  const filteredProducts = selectedCategory === 'all' 
    ? products 
    : products.filter(p => p.category === selectedCategory);

  if (!stats) return <div className="cyber-loading">Chargement...</div>;

  return (
    <div className="cyber-dashboard">
      {/* Hero Section */}
      <section className="cyber-hero">
        <div className="container mx-auto px-4 py-16">
          <div className="text-center">
            <h1 className="cyber-title">
              AIRDROP mAInet 2026
            </h1>
            <p className="cyber-subtitle">
              Rejoignez la révolution du mining et gagnez des tokens
            </p>
            <div className="cyber-countdown">
              <div className="countdown-item">
                <div className="countdown-number">126</div>
                <div className="countdown-label">JOURS</div>
              </div>
              <div className="countdown-item">
                <div className="countdown-number">15</div>
                <div className="countdown-label">HEURES</div>
              </div>
              <div className="countdown-item">
                <div className="countdown-number">42</div>
                <div className="countdown-label">MINUTES</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Grid */}
      <section className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card className="cyber-card">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Solde Principal</p>
                  <p className="text-2xl font-bold text-cyber-green">{stats.balance?.toFixed(2)}</p>
                </div>
                <Wallet className="w-8 h-8 text-cyber-green" />
              </div>
            </CardContent>
          </Card>

          <Card className="cyber-card">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Bonus (+17%)</p>
                  <p className="text-2xl font-bold text-yellow-400">{stats.bonus_balance?.toFixed(2)}</p>
                </div>
                <Gift className="w-8 h-8 text-yellow-400" />
              </div>
            </CardContent>
          </Card>

          <Card className="cyber-card">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Total Gagné</p>
                  <p className="text-2xl font-bold text-blue-400">{stats.total_earned?.toFixed(2)}</p>
                </div>
                <TrendingUp className="w-8 h-8 text-blue-400" />
              </div>
            </CardContent>
          </Card>

          <Card className="cyber-card">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Jeu - Solde</p>
                  <p className="text-2xl font-bold text-purple-400">{stats.game_stats?.game_balance?.toFixed(3) || '0.000'}</p>
                </div>
                <MousePointer className="w-8 h-8 text-purple-400" />
              </div>
            </CardContent>
          </Card>
        </div>

        <Tabs defaultValue="game" className="cyber-tabs">
          <TabsList className="cyber-tabs-list">
            <TabsTrigger value="game">Jeu de Clic</TabsTrigger>
            <TabsTrigger value="tasks">Tâches</TabsTrigger>
            <TabsTrigger value="shop">Boutique</TabsTrigger>
            <TabsTrigger value="deposits">Dépôts</TabsTrigger>
            <TabsTrigger value="referral">Parrainage</TabsTrigger>
          </TabsList>

          <TabsContent value="game">
            <ClickGame />
          </TabsContent>

          <TabsContent value="tasks" className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-bold text-white">Tâches Disponibles</h2>
              <Badge variant="outline" className="cyber-badge">
                {tasks.length} disponibles
              </Badge>
            </div>
            <div className="grid gap-4">
              {tasks.map((task) => (
                <Card key={task.id} className="cyber-card">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <h3 className="font-semibold text-white">{task.title}</h3>
                        <p className="text-gray-400 text-sm">{task.description}</p>
                        <div className="flex items-center mt-2 space-x-2">
                          <Coins className="w-4 h-4 text-cyber-green" />
                          <span className="text-cyber-green font-mono">+{task.reward}</span>
                        </div>
                      </div>
                      <Button 
                        onClick={() => completeTask(task.id)}
                        className="cyber-button"
                      >
                        Compléter
                        <ChevronRight className="w-4 h-4 ml-2" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="shop" className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-bold text-white">Boutique Mining</h2>
              <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                <SelectTrigger className="cyber-select w-48">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="cyber-select-content">
                  <SelectItem value="all">Toutes catégories</SelectItem>
                  <SelectItem value="equipment">Équipements</SelectItem>
                  <SelectItem value="cloud_mining">Cloud Mining</SelectItem>
                  <SelectItem value="contracts">Contrats</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredProducts.map((product) => (
                <Card key={product.id} className="cyber-card product-card">
                  <div className="product-image">
                    <img src={product.image_url} alt={product.name} />
                    <div className="product-overlay">
                      <Badge className="cyber-badge">{product.category}</Badge>
                      {product.price < 100 && (
                        <Badge className="cyber-badge-success mt-2">ABORDABLE</Badge>
                      )}
                    </div>
                  </div>
                  <CardContent className="p-6">
                    <h3 className="font-semibold text-white mb-2">{product.name}</h3>
                    <p className="text-gray-400 text-sm mb-4">{product.description}</p>
                    <div className="flex items-center justify-between">
                      <span className="text-2xl font-bold text-cyber-green">${product.price}</span>
                      <Button className="cyber-button">
                        <ShoppingCart className="w-4 h-4 mr-2" />
                        Acheter
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="deposits" className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-bold text-white">Dépôts & Bonus</h2>
              <Dialog open={depositModal} onOpenChange={setDepositModal}>
                <DialogTrigger asChild>
                  <Button className="cyber-button">
                    <Plus className="w-4 h-4 mr-2" />
                    Nouveau Dépôt
                  </Button>
                </DialogTrigger>
                <DialogContent className="cyber-dialog">
                  <DialogHeader>
                    <DialogTitle>Effectuer un Dépôt</DialogTitle>
                    <DialogDescription>
                      Recevez 17% de bonus sur chaque dépôt!
                    </DialogDescription>
                  </DialogHeader>
                  <form onSubmit={submitDeposit} className="space-y-4">
                    <div>
                      <Label>Méthode de Paiement</Label>
                      <Select 
                        value={depositForm.payment_method}
                        onValueChange={(value) => setDepositForm({...depositForm, payment_method: value})}
                      >
                        <SelectTrigger className="cyber-select">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="cyber-select-content">
                          <SelectItem value="payeer">Payeer (P1112145219)</SelectItem>
                          <SelectItem value="faucetpay">FaucetPay (maximlprive90@gmail.com)</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Montant</Label>
                      <Input 
                        type="number"
                        value={depositForm.amount}
                        onChange={(e) => setDepositForm({...depositForm, amount: e.target.value})}
                        className="cyber-input"
                        placeholder="100.00"
                        required
                      />
                    </div>
                    <div>
                      <Label>ID de Transaction</Label>
                      <Input 
                        value={depositForm.transaction_id}
                        onChange={(e) => setDepositForm({...depositForm, transaction_id: e.target.value})}
                        className="cyber-input"
                        placeholder="TXN123456789"
                        required
                      />
                    </div>
                    <div className="cyber-deposit-info">
                      <div className="flex items-center justify-between">
                        <span>Montant:</span>
                        <span>${depositForm.amount || '0.00'}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span>Bonus (17%):</span>
                        <span className="text-yellow-400">+${((parseFloat(depositForm.amount) || 0) * 0.17).toFixed(2)}</span>
                      </div>
                      <div className="flex items-center justify-between font-bold">
                        <span>Total reçu:</span>
                        <span className="text-cyber-green">${((parseFloat(depositForm.amount) || 0) * 1.17).toFixed(2)}</span>
                      </div>
                    </div>
                    <Button type="submit" className="cyber-button w-full">
                      Confirmer le Dépôt
                    </Button>
                  </form>
                </DialogContent>
              </Dialog>
            </div>

            <div className="grid gap-4">
              {deposits.map((deposit) => (
                <Card key={deposit.id} className="cyber-card">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="font-semibold text-white">${deposit.amount}</span>
                          <Badge variant="outline" className="cyber-badge">
                            {deposit.payment_method}
                          </Badge>
                          <Badge variant="outline" className="cyber-badge-success">
                            +${deposit.bonus_amount} bonus
                          </Badge>
                        </div>
                        <p className="text-gray-400 text-sm">TXN: {deposit.transaction_id}</p>
                      </div>
                      <div className="text-right">
                        <Badge className={deposit.status === 'approved' ? 'cyber-badge-success' : 'cyber-badge'}>
                          {deposit.status}
                        </Badge>
                        <p className="text-gray-400 text-sm mt-1">
                          {new Date(deposit.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="referral" className="space-y-4">
            <div className="text-center">
              <h2 className="text-xl font-bold text-white mb-4">Programme de Parrainage</h2>
              <p className="text-gray-400 mb-8">Invitez vos amis et gagnez 50 tokens par parrainage!</p>
              
              <Card className="cyber-card max-w-md mx-auto">
                <CardContent className="p-6">
                  <div className="space-y-4">
                    <div>
                      <Label>Votre Code de Parrainage</Label>
                      <div className="flex items-center space-x-2 mt-2">
                        <Input 
                          value={user.referral_code}
                          readOnly
                          className="cyber-input"
                        />
                        <Button 
                          onClick={copyReferralCode}
                          className="cyber-button"
                          size="sm"
                        >
                          <Copy className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                    <div className="cyber-referral-stats">
                      <div className="flex items-center justify-between">
                        <span>Total des gains de parrainage:</span>
                        <span className="text-cyber-green font-bold">0 tokens</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </section>
    </div>
  );
};

const AuthPage = () => {
  const { login, register } = useAuth();
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    referralCode: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (isLogin) {
      await login(formData.email, formData.password);
    } else {
      await register(formData.email, formData.username, formData.password, formData.referralCode);
    }
  };

  return (
    <div className="cyber-auth">
      <div className="container mx-auto px-4 py-16">
        <Card className="cyber-card max-w-md mx-auto">
          <CardHeader className="text-center">
            <div className="cyber-logo mx-auto mb-4">
              <Zap className="w-12 h-12 text-cyber-green" />
            </div>
            <CardTitle className="text-2xl text-white">
              {isLogin ? 'Connexion' : 'Inscription'}
            </CardTitle>
            <CardDescription>
              {isLogin ? 'Connectez-vous à votre compte' : 'Créez votre compte mAInet'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <Label>Email</Label>
                <Input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  className="cyber-input"
                  required
                />
              </div>
              
              {!isLogin && (
                <div>
                  <Label>Nom d'utilisateur</Label>
                  <Input
                    value={formData.username}
                    onChange={(e) => setFormData({...formData, username: e.target.value})}
                    className="cyber-input"
                    required
                  />
                </div>
              )}
              
              <div>
                <Label>Mot de passe</Label>
                <Input
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({...formData, password: e.target.value})}
                  className="cyber-input"
                  required
                />
              </div>
              
              {!isLogin && (
                <div>
                  <Label>Code de parrainage (optionnel)</Label>
                  <Input
                    value={formData.referralCode}
                    onChange={(e) => setFormData({...formData, referralCode: e.target.value})}
                    className="cyber-input"
                    placeholder="Code de votre parrain"
                  />
                </div>
              )}
              
              <Button type="submit" className="cyber-button w-full">
                {isLogin ? 'Se connecter' : 'S\'inscrire'}
              </Button>
            </form>
            
            <div className="text-center mt-4">
              <Button
                variant="ghost"
                onClick={() => setIsLogin(!isLogin)}
                className="cyber-button-ghost"
              >
                {isLogin ? 'Créer un compte' : 'Déjà inscrit ? Se connecter'}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

const App = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="cyber-loading">
        <Zap className="w-8 h-8 text-cyber-green animate-pulse" />
        <span>Chargement...</span>
      </div>
    );
  }

  return (
    <div className="App">
      <Header />
      <main>
        {user ? <Dashboard /> : <AuthPage />}
      </main>
      <Toaster />
    </div>
  );
};

const AppWithAuth = () => (
  <AuthProvider>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </AuthProvider>
);

export default AppWithAuth;