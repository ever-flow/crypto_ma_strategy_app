import pandas as pd
import numpy as np
import yfinance as yf
import warnings
import datetime
from dateutil.relativedelta import relativedelta
import json
import os

warnings.filterwarnings('ignore')

def fetch_crypto_data():
    """
    BTC-USD, ETH-USD의 종가 데이터를 수집하여 하나의 DataFrame으로 반환
    """
    try:
        # Download data
        btc = yf.download("BTC-USD", start="2016-01-01", progress=False)
        eth = yf.download("ETH-USD", start="2017-01-10", progress=False)

        # Extract Close prices
        btc_close = btc["Close"]
        eth_close = eth["Close"]

        # Create aligned DataFrame
        df = pd.DataFrame()
        df["BTC"] = btc_close
        df["ETH"] = eth_close

        return df.dropna()
    except Exception as e:
        print(f"데이터 수집 오류: {e}")
        return pd.DataFrame()

def calculate_cagr(cumulative_returns_factor, num_years):
    """
    누적 수익률 팩터(예: 최종자산/초기자산)와 투자 기간(년)을 이용하여 CAGR 계산
    """
    if cumulative_returns_factor is None or num_years == 0 or cumulative_returns_factor <= 0:
        return -1.0 if cumulative_returns_factor == 0 else 0.0
    return (cumulative_returns_factor ** (1 / num_years)) - 1

def calculate_sortino_ratio(net_returns, risk_free_rate=0.0):
    """
    하방 변동성을 고려한 Sortino Ratio 계산
    """
    negative_returns = net_returns[net_returns < risk_free_rate]
    if len(negative_returns) == 0:
        mean_annual_return = net_returns.mean() * 365
        if mean_annual_return > risk_free_rate:
            return np.inf
        return 0.0

    downside_deviation_annual = negative_returns.std() * np.sqrt(365)
    if downside_deviation_annual == 0:
        mean_annual_return = net_returns.mean() * 365
        if mean_annual_return > risk_free_rate:
             return np.inf
        return 0.0

    annualized_mean_return = net_returns.mean() * 365
    return (annualized_mean_return - risk_free_rate) / downside_deviation_annual

def calculate_mdd(cumulative_series):
    """주어진 누적 수익률 시리즈에 대한 최대 낙폭(MDD)을 계산합니다."""
    if cumulative_series.empty or len(cumulative_series) < 2:
        return 0.0
    cummax = cumulative_series.cummax()
    drawdown = (cumulative_series / cummax) - 1
    return drawdown.min()

def calculate_advanced_combined_sortino(net_returns):
    """
    개선된 Combined Sortino 계산:
    - 전체 기간: 30%
    - 최근 3년: 40% 
    - 최근 1년: 30%
    이렇게 하면 최근에 더 가중치를 두면서도 전체 기간의 안정성을 고려
    """
    if len(net_returns) < 100:  # 데이터가 너무 적으면 전체 기간만 사용
        return calculate_sortino_ratio(net_returns)
    
    # 전체 기간 Sortino
    overall_sortino = calculate_sortino_ratio(net_returns)
    
    # 최근 3년 (약 1095일)
    recent_3y_data = net_returns.iloc[-min(1095, len(net_returns)):]
    recent_3y_sortino = calculate_sortino_ratio(recent_3y_data) if len(recent_3y_data) >= 100 else overall_sortino
    
    # 최근 1년 (약 365일)
    recent_1y_data = net_returns.iloc[-min(365, len(net_returns)):]
    recent_1y_sortino = calculate_sortino_ratio(recent_1y_data) if len(recent_1y_data) >= 50 else overall_sortino
    
    # 가중 평균: 전체 30% + 최근3년 40% + 최근1년 30%
    weights = [0.3, 0.4, 0.3]
    sortinos = [overall_sortino, recent_3y_sortino, recent_1y_sortino]
    
    # NaN 처리
    valid_sortinos = []
    valid_weights = []
    for i, sortino in enumerate(sortinos):
        if not np.isnan(sortino) and not np.isinf(sortino):
            valid_sortinos.append(sortino)
            valid_weights.append(weights[i])
    
    if not valid_sortinos:
        return np.nan
    
    # 가중치 정규화
    total_weight = sum(valid_weights)
    normalized_weights = [w / total_weight for w in valid_weights]
    
    combined_sortino = sum(s * w for s, w in zip(valid_sortinos, normalized_weights))
    return combined_sortino

def get_current_signal(price_series, ma_window):
    """
    현재 매수/매도 신호를 반환
    """
    if len(price_series) < ma_window + 1:
        return "데이터 부족", "gray"
    
    current_price = price_series.iloc[-1]
    ma = price_series.rolling(window=ma_window).mean()
    current_ma = ma.iloc[-1]
    
    if pd.isna(current_ma):
        return "데이터 부족", "gray"
    
    if current_price > current_ma:
        return "매수", "#28a745"  # 초록색
    else:
        return "매도/현금보유", "#dc3545"  # 빨간색

def evaluate_strategy(price_series, ma_window, fee=0.0025):
    """
    이동평균(ma_window) 대비 가격 위치를 이용한 트렌드 추종 전략 평가
    """
    if len(price_series) < ma_window:
        return {
            "window": ma_window, "sharpe": 0.0, "sortino": np.nan, "combined_sortino": np.nan,
            "cagr": 0.0, "final_value": 1.0, "drawdown": 0.0, "volatility": 0.0,
            "cumulative_series": pd.Series([1.0], index=[price_series.index[0] if not price_series.empty else pd.Timestamp('1970-01-01')]),
            "signal": "데이터 부족", "signal_color": "gray"
        }

    ma = price_series.rolling(window=ma_window, min_periods=ma_window).mean()
    valid_indices = ma.dropna().index
    if len(valid_indices) < 2:
        return {
            "window": ma_window, "sharpe": 0.0, "sortino": np.nan, "combined_sortino": np.nan, "cagr": 0.0,
            "final_value": 1.0, "drawdown": 0.0, "volatility": 0.0,
            "cumulative_series": pd.Series([1.0], index=[price_series.index[0] if not price_series.empty else pd.Timestamp('1970-01-01')]),
            "signal": "데이터 부족", "signal_color": "gray"
        }

    price_series_eval = price_series.loc[valid_indices]
    ma_eval = ma.loc[valid_indices]

    signal = (price_series_eval > ma_eval).astype(int)
    position = signal.shift(1).fillna(0)
    returns = price_series_eval.pct_change().fillna(0)
    trades = position.diff().fillna(0).abs()
    net_returns = position * returns - trades * fee
    cumulative = (1 + net_returns).cumprod()

    # 현재 신호 계산
    current_signal, signal_color = get_current_signal(price_series, ma_window)

    if cumulative.empty or cumulative.iloc[-1] <= 0:
        final_value = cumulative.iloc[-1] if not cumulative.empty else 0.0
        cagr_val = -1.0 if final_value == 0 else calculate_cagr(final_value, 1/365.25)
        mdd_val = calculate_mdd(cumulative) if not cumulative.empty else (-1.0 if final_value == 0 else 0.0)

        return {
            "window": ma_window, "sharpe": 0.0, "sortino": np.nan, "combined_sortino": np.nan,
            "cagr": cagr_val,
            "final_value": final_value,
            "drawdown": mdd_val,
            "volatility": net_returns.std() * np.sqrt(365) if len(net_returns) > 1 else 0.0,
            "cumulative_series": cumulative if not cumulative.empty else pd.Series([final_value if final_value > 0 else 1.0], index=[price_series_eval.index[0] if not price_series_eval.empty else pd.Timestamp('1970-01-01')]),
            "signal": current_signal, "signal_color": signal_color
        }

    num_years = max((price_series_eval.index[-1] - price_series_eval.index[0]).days / 365.25, 1/365.25)
    cagr = calculate_cagr(cumulative.iloc[-1], num_years)
    std_dev = net_returns.std()
    overall_sharpe = (net_returns.mean() * 365) / (std_dev * np.sqrt(365)) if std_dev > 0 else 0.0
    overall_sortino = calculate_sortino_ratio(net_returns)

    # 개선된 Combined Sortino 계산
    combined_sortino = calculate_advanced_combined_sortino(net_returns)

    max_dd = calculate_mdd(cumulative)
    vol = std_dev * np.sqrt(365) if std_dev > 0 else 0.0

    return {
        "window": ma_window, "sharpe": overall_sharpe, "sortino": overall_sortino,
        "combined_sortino": combined_sortino, "cagr": cagr,
        "final_value": cumulative.iloc[-1], "drawdown": max_dd, "volatility": vol,
        "cumulative_series": cumulative, "signal": current_signal, "signal_color": signal_color
    }

def get_portfolio_signal(portfolio_series, ma_window):
    """
    포트폴리오 전체의 매수/매도 신호를 반환
    """
    if len(portfolio_series) < ma_window + 1:
        return "데이터 부족", "gray"
    
    current_value = portfolio_series.iloc[-1]
    ma = portfolio_series.rolling(window=ma_window).mean()
    current_ma = ma.iloc[-1]
    
    if pd.isna(current_ma):
        return "데이터 부족", "gray"
    
    if current_value > current_ma:
        return "매수", "#28a745"  # 초록색
    else:
        return "매도/현금보유", "#dc3545"  # 빨간색

def evaluate_rebalancing_strategy(data, ma_window, rebalance_freq='M', weight_btc=0.5, weight_eth=0.5, fee=0.0025):
    if data.empty or len(data) < ma_window:
        start_index_for_default = data.index[0] if not data.empty else pd.Timestamp('1970-01-01')
        return {
            "window": ma_window, "sharpe": 0.0, "sortino": np.nan, "combined_sortino": np.nan, "cagr": 0.0,
            "final_value": 1.0, "drawdown": 0.0, "volatility": 0.0,
            "cumulative_series": pd.Series([1.0], index=[start_index_for_default]),
            "signal": "데이터 부족", "signal_color": "gray"
        }

    btc_ma = data['BTC'].rolling(window=ma_window, min_periods=ma_window).mean()
    eth_ma = data['ETH'].rolling(window=ma_window, min_periods=ma_window).mean()

    valid_btc_idx = btc_ma.dropna().index
    valid_eth_idx = eth_ma.dropna().index

    if valid_btc_idx.empty or valid_eth_idx.empty:
        return {
            "window": ma_window, "sharpe": 0.0, "sortino": np.nan, "combined_sortino": np.nan, "cagr": 0.0,
            "final_value": 1.0, "drawdown": 0.0, "volatility": 0.0,
            "cumulative_series": pd.Series([1.0], index=[data.index[0] if not data.empty else pd.Timestamp('1970-01-01')]),
            "signal": "데이터 부족", "signal_color": "gray"
        }
    start_idx = max(valid_btc_idx[0], valid_eth_idx[0])

    if len(data.loc[start_idx:]) < 2:
         return {
            "window": ma_window, "sharpe": 0.0, "sortino": np.nan, "combined_sortino": np.nan, "cagr": 0.0,
            "final_value": 1.0, "drawdown": 0.0, "volatility": 0.0,
            "cumulative_series": pd.Series([1.0], index=[data.index[0] if not data.empty else pd.Timestamp('1970-01-01')]),
            "signal": "데이터 부족", "signal_color": "gray"
        }

    eval_data = data.loc[start_idx:].copy()
    btc_ma_eval = btc_ma.loc[start_idx:]
    eth_ma_eval = eth_ma.loc[start_idx:]

    btc_signal = (eval_data['BTC'] > btc_ma_eval).astype(int)
    eth_signal = (eval_data['ETH'] > eth_ma_eval).astype(int)
    btc_position = btc_signal.shift(1).fillna(0)
    eth_position = eth_signal.shift(1).fillna(0)

    btc_returns_daily = eval_data['BTC'].pct_change().fillna(0)
    eth_returns_daily = eval_data['ETH'].pct_change().fillna(0)

    btc_trades = btc_position.diff().fillna(0).abs()
    eth_trades = eth_position.diff().fillna(0).abs()

    btc_strategy_returns = btc_position * btc_returns_daily - btc_trades * fee
    eth_strategy_returns = eth_position * eth_returns_daily - eth_trades * fee

    eval_data['month'] = eval_data.index.to_period(rebalance_freq)
    eval_data['rebalance_signal'] = eval_data['month'].ne(eval_data['month'].shift(1)).astype(int)
    if not eval_data.empty:
        eval_data.iloc[0, eval_data.columns.get_loc('rebalance_signal')] = 0

    portfolio_value = pd.Series(index=eval_data.index, dtype=float)
    if eval_data.empty:
        return {
            "window": ma_window, "sharpe": 0.0, "sortino": np.nan, "combined_sortino": np.nan, "cagr": 0.0,
            "final_value": 1.0, "drawdown": 0.0, "volatility": 0.0,
            "cumulative_series": pd.Series([1.0], index=[data.index[0] if not data.empty else pd.Timestamp('1970-01-01')]),
            "signal": "데이터 부족", "signal_color": "gray"
        }
    portfolio_value.iloc[0] = 1.0

    current_btc_weight = weight_btc
    current_eth_weight = weight_eth

    for i in range(1, len(eval_data)):
        prev_total_value = portfolio_value.iloc[i-1]
        if prev_total_value <= 0:
            portfolio_value.iloc[i:] = prev_total_value
            break

        btc_value_after_growth = prev_total_value * current_btc_weight * (1 + btc_strategy_returns.iloc[i])
        eth_value_after_growth = prev_total_value * current_eth_weight * (1 + eth_strategy_returns.iloc[i])
        current_total_value_before_rebalance = btc_value_after_growth + eth_value_after_growth

        if current_total_value_before_rebalance <= 0:
            portfolio_value.iloc[i:] = current_total_value_before_rebalance
            break

        if eval_data['rebalance_signal'].iloc[i] == 1:
            temp_btc_weight = btc_value_after_growth / current_total_value_before_rebalance
            temp_eth_weight = eth_value_after_growth / current_total_value_before_rebalance
            rebalancing_cost = (abs(temp_btc_weight - weight_btc) + abs(temp_eth_weight - weight_eth)) * fee * current_total_value_before_rebalance

            portfolio_value.iloc[i] = current_total_value_before_rebalance - rebalancing_cost
            current_btc_weight = weight_btc
            current_eth_weight = weight_eth
        else:
            portfolio_value.iloc[i] = current_total_value_before_rebalance
            current_btc_weight = btc_value_after_growth / current_total_value_before_rebalance
            current_eth_weight = eth_value_after_growth / current_total_value_before_rebalance

    portfolio_value = portfolio_value.fillna(method='ffill').fillna(0)

    # 포트폴리오 전체의 현재 신호 계산
    portfolio_signal, portfolio_signal_color = get_portfolio_signal(portfolio_value, ma_window)

    net_returns_portfolio = portfolio_value.pct_change().fillna(0)
    cumulative_portfolio = portfolio_value

    if cumulative_portfolio.empty or cumulative_portfolio.iloc[-1] <= 0:
        final_value = cumulative_portfolio.iloc[-1] if not cumulative_portfolio.empty else 0.0
        cagr_val = -1.0 if final_value == 0 else calculate_cagr(final_value, 1/365.25)
        mdd_val = calculate_mdd(cumulative_portfolio) if not cumulative_portfolio.empty else (-1.0 if final_value == 0 else 0.0)
        return {
            "window": ma_window, "sharpe": 0.0, "sortino": np.nan, "combined_sortino": np.nan,
            "cagr": cagr_val, "final_value": final_value, "drawdown": mdd_val,
            "volatility": net_returns_portfolio.std() * np.sqrt(365) if len(net_returns_portfolio) > 1 else 0.0,
            "cumulative_series": cumulative_portfolio if not cumulative_portfolio.empty else pd.Series([final_value if final_value > 0 else 1.0], index=[eval_data.index[0] if not eval_data.empty else pd.Timestamp('1970-01-01')]),
            "signal": portfolio_signal, "signal_color": portfolio_signal_color
        }

    num_years = max((eval_data.index[-1] - eval_data.index[0]).days / 365.25, 1/365.25)
    cagr = calculate_cagr(cumulative_portfolio.iloc[-1], num_years)
    std_dev = net_returns_portfolio.std()
    overall_sharpe = (net_returns_portfolio.mean() * 365) / (std_dev * np.sqrt(365)) if std_dev > 0 else 0.0
    overall_sortino = calculate_sortino_ratio(net_returns_portfolio)

    # 개선된 Combined Sortino 계산
    combined_sortino = calculate_advanced_combined_sortino(net_returns_portfolio)

    max_dd = calculate_mdd(cumulative_portfolio)
    vol = std_dev * np.sqrt(365) if std_dev > 0 else 0.0

    return {
        "window": ma_window, "sharpe": overall_sharpe, "sortino": overall_sortino,
        "combined_sortino": combined_sortino, "cagr": cagr,
        "final_value": cumulative_portfolio.iloc[-1], "drawdown": max_dd, "volatility": vol,
        "cumulative_series": cumulative_portfolio,
        "signal": portfolio_signal, "signal_color": portfolio_signal_color
    }

def run_optimization_and_save():
    """
    최적화를 실행하고 결과를 JSON 파일로 저장
    """
    print("🕒 암호화폐 데이터 수집 중...")
    data = fetch_crypto_data()
    
    if data.empty:
        print("❌ 데이터 수집 실패")
        return
    
    print(f"✅ 데이터 수집 완료: {data.index[0].date()} ~ {data.index[-1].date()}")
    
    windows = list(range(10, 201, 10))
    results = {}
    
    # BTC 전략 평가
    print("\n📈 BTC 전략 평가 중...")
    if 'BTC' in data and not data['BTC'].empty:
        btc_results = []
        for w in windows:
            btc_results.append(evaluate_strategy(data["BTC"].copy(), w))
        btc_df = pd.DataFrame(btc_results).sort_values("combined_sortino", ascending=False).reset_index(drop=True)
        if not btc_df.empty:
            best_btc = btc_df.iloc[0]
            results['BTC'] = {
                'optimal_ma': int(best_btc['window']),
                'combined_sortino': float(best_btc['combined_sortino']) if not np.isnan(best_btc['combined_sortino']) else 0.0,
                'cagr': float(best_btc['cagr']),
                'sharpe': float(best_btc['sharpe']),
                'sortino': float(best_btc['sortino']) if not np.isnan(best_btc['sortino']) else 0.0,
                'drawdown': float(best_btc['drawdown']),
                'volatility': float(best_btc['volatility']),
                'final_value': float(best_btc['final_value']),
                'signal': best_btc['signal'],
                'signal_color': best_btc['signal_color'],
                'cumulative_series': {str(k): v for k, v in best_btc['cumulative_series'].to_dict().items()}
            }
    
    # ETH 전략 평가
    print("📈 ETH 전략 평가 중...")
    if 'ETH' in data and not data['ETH'].empty:
        eth_results = []
        for w in windows:
            eth_results.append(evaluate_strategy(data["ETH"].copy(), w))
        eth_df = pd.DataFrame(eth_results).sort_values("combined_sortino", ascending=False).reset_index(drop=True)
        if not eth_df.empty:
            best_eth = eth_df.iloc[0]
            results['ETH'] = {
                'optimal_ma': int(best_eth['window']),
                'combined_sortino': float(best_eth['combined_sortino']) if not np.isnan(best_eth['combined_sortino']) else 0.0,
                'cagr': float(best_eth['cagr']),
                'sharpe': float(best_eth['sharpe']),
                'sortino': float(best_eth['sortino']) if not np.isnan(best_eth['sortino']) else 0.0,
                'drawdown': float(best_eth['drawdown']),
                'volatility': float(best_eth['volatility']),
                'final_value': float(best_eth['final_value']),
                'signal': best_eth['signal'],
                'signal_color': best_eth['signal_color'],
                'cumulative_series': {str(k): v for k, v in best_eth['cumulative_series'].to_dict().items()}
            }
    
    # 50:50 리밸런싱 전략 평가
    print("📈 50:50 리밸런싱 전략 평가 중...")
    rebal_5050 = []
    for w in windows:
        rebal_5050.append(evaluate_rebalancing_strategy(data.copy(), w, rebalance_freq='M', weight_btc=0.5, weight_eth=0.5))
    rebal_5050_df = pd.DataFrame(rebal_5050).sort_values("combined_sortino", ascending=False).reset_index(drop=True)
    if not rebal_5050_df.empty:
        best_5050 = rebal_5050_df.iloc[0]
        results['Rebal_50_50'] = {
            'optimal_ma': int(best_5050['window']),
            'combined_sortino': float(best_5050['combined_sortino']) if not np.isnan(best_5050['combined_sortino']) else 0.0,
            'cagr': float(best_5050['cagr']),
            'sharpe': float(best_5050['sharpe']),
            'sortino': float(best_5050['sortino']) if not np.isnan(best_5050['sortino']) else 0.0,
            'drawdown': float(best_5050['drawdown']),
            'volatility': float(best_5050['volatility']),
            'final_value': float(best_5050['final_value']),
            'signal': best_5050['signal'],
            'signal_color': best_5050['signal_color'],
            'cumulative_series': {str(k): v for k, v in best_5050['cumulative_series'].to_dict().items()}
        }
    
    # 60:40 리밸런싱 전략 평가
    print("📈 60:40 리밸런싱 전략 평가 중...")
    rebal_6040 = []
    for w in windows:
        rebal_6040.append(evaluate_rebalancing_strategy(data.copy(), w, rebalance_freq='M', weight_btc=0.6, weight_eth=0.4))
    rebal_6040_df = pd.DataFrame(rebal_6040).sort_values("combined_sortino", ascending=False).reset_index(drop=True)
    if not rebal_6040_df.empty:
        best_6040 = rebal_6040_df.iloc[0]
        results['Rebal_60_40'] = {
            'optimal_ma': int(best_6040['window']),
            'combined_sortino': float(best_6040['combined_sortino']) if not np.isnan(best_6040['combined_sortino']) else 0.0,
            'cagr': float(best_6040['cagr']),
            'sharpe': float(best_6040['sharpe']),
            'sortino': float(best_6040['sortino']) if not np.isnan(best_6040['sortino']) else 0.0,
            'drawdown': float(best_6040['drawdown']),
            'volatility': float(best_6040['volatility']),
            'final_value': float(best_6040['final_value']),
            'signal': best_6040['signal'],
            'signal_color': best_6040['signal_color'],
            'cumulative_series': {str(k): v for k, v in best_6040['cumulative_series'].to_dict().items()}
        }
    
    # 결과 저장
    results['last_updated'] = datetime.datetime.now().isoformat()
    results['data_period'] = {
        'start': data.index[0].isoformat(),
        'end': data.index[-1].isoformat()
    }
    
    # 결과 파일은 data 폴더에 저장
    output_path = os.path.join('data', 'strategy_results.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 최적화 완료 및 결과 저장: {output_path}")
    return results

if __name__ == "__main__":
    run_optimization_and_save()

