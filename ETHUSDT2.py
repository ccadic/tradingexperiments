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
    since = exchange.parse8601(since)
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since, limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df

# Période de backtest
startdate = '2023-01-01T00:00:00Z'
enddate = '2024-04-14T00:00:00Z'
data = fetch_data('ETH/USDT', '1d', startdate)

# Calcul des indicateurs
ema_indicator = EMAIndicator(close=data['Close'], window=25)
data['EMA25'] = ema_indicator.ema_indicator()
rsi_indicator = RSIIndicator(close=data['Close'], window=3)
data['RSI3'] = rsi_indicator.rsi()

# Définir la logique de trading
data['Buy'] = (data['Close'] > data['EMA25']) & (data['RSI3'] > 82)
data['Sell'] = (data['RSI3'] < 20)

# Paramètres de trading
capital = 1000.0
capital_start = capital
positions = 0
peak = capital
drawdown = 0
entry_price = 0
stop_loss_pct = 0.032  # Stop loss de 3.2%
trailing_stop_pct = 0.001  # Trailing stop de 0.1%

# Simulation du trading
for index, row in data.iterrows():
    # Vérifier et mettre à jour le trailing stop
    if positions > 0:
        if row['High'] > entry_price * (1 + trailing_stop_pct):
            entry_price = row['High']
            stop_loss = entry_price * (1 - stop_loss_pct)
        
        if row['Low'] < stop_loss:
            capital = positions * stop_loss
            positions = 0
            entry_price = 0
            continue

    if row['Buy'] and capital > 0 and positions == 0:
        entry_price = row['Close']
        positions = capital / entry_price
        capital = 0
        stop_loss = entry_price * (1 - stop_loss_pct)
        trailing_stop = entry_price * (1 + trailing_stop_pct)

    if row['Sell'] and positions > 0:
        capital = positions * row['Close']
        positions = 0
        entry_price = 0

    # Calcul du drawdown
    current_value = positions * row['Close'] if positions > 0 else capital
    if current_value > peak:
        peak = current_value
    else:
        current_drawdown = (peak - current_value) / peak
        if current_drawdown > drawdown:
            drawdown = current_drawdown

# Calcul du capital final et du profit
capital_end = capital if positions == 0 else positions * data.iloc[-1]['Close']
profit = capital_end - capital_start
profit_percentage = (profit / capital_start) * 100

# Rapport de résultats
print("Rapport de Backtest")
print(f"Capital de départ: {capital_start:.2f} USDT")
print(f"Capital de fin: {capital_end:.2f} USDT")
print(f"Profit: {profit:.2f} USDT")
print(f"Rentabilité: {profit_percentage:.2f}%")
print(f"Drawdown maximal: {drawdown*100:.2f}%")
