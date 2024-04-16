import ccxt
import pandas as pd
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator

# Configuration de l'API Binance
exchange = ccxt.binance({
    'rateLimit': 1200,  # limite de requêtes par minute
    'enableRateLimit': True,
})

# Fonction pour télécharger les données historiques
def fetch_data(symbol, timeframe, since, limit=1000):
    # Convertir la date en timestamp millisecondes
    since = exchange.parse8601(since)
    
    # Récupérer les données OHLCV
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since, limit)
    # Créer un DataFrame
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df

# Exemple de période de backtest
startdate = '2023-01-01T00:00:00Z'
enddate = '2024-04-15T00:00:00Z'
data = fetch_data('ETH/USDT', '1d', startdate)

# Calcul des indicateurs
ema_indicator = EMAIndicator(close=data['Close'], window=25)
data['EMA25'] = ema_indicator.ema_indicator()
rsi_indicator = RSIIndicator(close=data['Close'], window=3)
data['RSI3'] = rsi_indicator.rsi()

# Définir la logique de trading
data['Buy'] = (data['Close'] > data['EMA25']) & (data['RSI3'] > 82)
data['Sell'] = (data['RSI3'] < 20)

# Initialiser les paramètres de trading
capital = 1000.0
capital_start = capital
positions = 0
peak = capital
drawdown = 0
entry_price = 0

# Exécution du backtest
for index, row in data.iterrows():
    if row['Buy'] and capital > 0:
        positions = capital / row['Close']
        entry_price = row['Close']
        capital = 0  # Tout le capital est investi
    elif row['Sell'] and positions > 0:
        capital = positions * row['Close']
        positions = 0
        # Calcul du drawdown
        if capital > peak:
            peak = capital
        else:
            current_drawdown = (peak - capital) / peak
            if current_drawdown > drawdown:
                drawdown = current_drawdown

# Calcul du capital final et du profit
capital_end = capital if capital > 0 else positions * data.iloc[-1]['Close']
profit = capital_end - capital_start
profit_percentage = (profit / capital_start) * 100

# Rapport de résultats
print("Rapport de Backtest")
print(f"Capital de départ: {capital_start:.2f} USDT")
print(f"Capital de fin: {capital_end:.2f} USDT")
print(f"Profit: {profit:.2f} USDT")
print(f"Rentabilité: {profit_percentage:.2f}%")
print(f"Drawdown maximal: {drawdown*100:.2f}%")
