import yfinance as yf
import pandas as pd
import numpy as np
from datetime import timedelta

def backtest_otm_calls(ticker, start_date='2018-01-01', end_date='2025-05-21'):
    # 1) Fetch price history
    data = yf.download(ticker, start=start_date, end=end_date)
    data['Pct_Change'] = data['Close'].pct_change() * 100

    trades = []
    pullbacks = data[data['Pct_Change'] <= -2]  # ≥2% down days

    for date, row in pullbacks.iterrows():
        buy_price = row['Close']
        expiry = date + timedelta(days=30)
        opt = yf.Ticker(ticker)
        # 2) Load option chain for that expiry
        if expiry.strftime('%Y-%m-%d') not in opt.options:
            continue
        calls = opt.option_chain(expiry.strftime('%Y-%m-%d')).calls
        # 3) Find nearest OTM strike
        otm = calls[calls.strike > buy_price]
        if otm.empty:
            continue
        choice = otm.iloc[(otm.strike - buy_price).abs().argsort()[0]]
        premium = choice.lastPrice
        strike   = choice.strike

        # 4) Fetch actual closing price on expiry
        fut = yf.download(ticker,
                          start=expiry,
                          end=expiry + timedelta(days=1))
        if fut.empty:
            continue
        exp_price = fut['Close'].iloc[0]

        payoff = max(exp_price - strike, 0) * 100   # per contract
        cost   = premium * 100
        rtn    = (payoff - cost) / cost * 100       # % return

        trades.append({
            'Buy Date':        date.date(),
            'Expiry Date':     expiry.date(),
            'Buy Price':       buy_price,
            'Strike':          strike,
            'Premium Paid':    premium,
            'Expiry Price':    exp_price,
            'Return (%)':      rtn
        })

    df = pd.DataFrame(trades)
    summary = {
        'Ticker':          ticker,
        'Total Trades':    len(df),
        'Profitable Trades': int((df['Return (%)'] > 0).sum()),
        'Win Rate (%)':    float((df['Return (%)'] > 0).mean() * 100) if len(df) else np.nan,
        'Avg Return (%)':  float(df['Return (%)].mean())          if len(df) else np.nan
    }
    return df, summary

# Run for AAPL and GOOG
df_aapl, sum_aapl = backtest_otm_calls('AAPL')
df_goog, sum_goog = backtest_otm_calls('GOOG')

# Show detailed trades
print("AAPL Trades:\n", df_aapl)
print("\nGOOG Trades:\n", df_goog)

# Show summary
print("\nSummary:")
print(pd.DataFrame([sum_aapl, sum_goog]))