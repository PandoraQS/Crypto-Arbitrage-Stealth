import streamlit as st
import redis
import json
import pandas as pd
import altair as alt
import time
from datetime import datetime

st.set_page_config(page_title="Crypto Arbitrage Stealth Engine", layout="wide")

r = redis.Redis(host='redis-cache', port=6379, db=0, decode_responses=True)
SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT']

if 'master_history' not in st.session_state:
    st.session_state.master_history = pd.DataFrame({
        'time': pd.Series(dtype='datetime64[ns]'),
        'symbol': pd.Series(dtype='str'),
        'spread': pd.Series(dtype='float'),
        'liquidity': pd.Series(dtype='float'),
        'latency': pd.Series(dtype='float'),
        'imbalance': pd.Series(dtype='float'),
        'profit_pct': pd.Series(dtype='float'),
        'net_profit': pd.Series(dtype='float')
    })

if 'alert_log' not in st.session_state:
    st.session_state.alert_log = pd.DataFrame({
        'Time': pd.Series(dtype='str'),
        'Symbol': pd.Series(dtype='str'),
        'Spread %': pd.Series(dtype='str'),
        'Net Profit $': pd.Series(dtype='str')
    })

st.title("Crypto Arbitrage Stealth Engine")
st.markdown("""
This platform monitors real-time price discrepancies between **Binance** and **Kraken**. 
The system analyzes **spread**, **order book liquidity**, and **network latency** to determine 
the actual feasibility of arbitrage operations.
""")

with st.sidebar:
    st.header("Settings")
    fees_threshold = st.slider("Fees Threshold %", 0.0, 1.0, 0.2, 0.05)
    investment = st.number_input("Investment (USDT)", 1000)
    st.divider()
    if st.button("Clear Alert Log"):
        st.session_state.alert_log = pd.DataFrame(columns=['Time', 'Symbol', 'Spread %', 'Net Profit $'])

dashboard_container = st.empty()

while True:
    current_time_dt = datetime.now()
    current_time_str = current_time_dt.strftime("%H:%M:%S")
    new_data_list = []

    for s in SYMBOLS:
        rb, rk = r.get(f"ticker:binance:{s}"), r.get(f"ticker:kraken:{s}")
        if rb and rk:
            b, k = json.loads(rb), json.loads(rk)
            spread_val = float(k['bid'] - b['ask'])
            profit_pct = (spread_val / b['ask']) * 100
            net_profit_val = investment * ((profit_pct / 100) - (fees_threshold / 100))
            total_depth = float(b.get('bid_depth', 0) + b.get('ask_depth', 0))
            imbalance = b.get('bid_depth', 0) / total_depth if total_depth > 0 else 0.5
            lat = float((b.get('latency', 0) + k.get('latency', 0)) / 2)
            
            new_data_list.append({
                'time': current_time_dt, 
                'symbol': s, 
                'spread': spread_val, 
                'liquidity': total_depth, 
                'latency': lat,
                'imbalance': imbalance,
                'profit_pct': profit_pct,
                'net_profit': net_profit_val
            })
            
            if net_profit_val > 0:
                alert_entry = pd.DataFrame([{
                    'Time': current_time_str,
                    'Symbol': s,
                    'Spread %': f"{profit_pct:.3f}%",
                    'Net Profit $': f"{net_profit_val:.2f}"
                }])
                st.session_state.alert_log = pd.concat([alert_entry, st.session_state.alert_log]).head(20)

    if new_data_list:
        st.session_state.master_history = pd.concat([
            st.session_state.master_history.dropna(how='all'), 
            pd.DataFrame(new_data_list)
        ]).tail(500)

    with dashboard_container.container():
        st.subheader("Market Intelligence Insights")
        if not st.session_state.master_history.empty:
            latest_all = st.session_state.master_history.groupby('symbol').last()
            
            insight_cols = st.columns(3)
            with insight_cols[0]:
                max_profit_row = latest_all.sort_values('net_profit', ascending=False).iloc[0]
                if max_profit_row['net_profit'] > 0:
                    st.success(f"**Active Opportunity:** {max_profit_row.name} shows a net profit of ${max_profit_row['net_profit']:.2f}.")
                else:
                    st.info(f"**Status:** No profitable arbitrage. {max_profit_row.name} is closest to break-even.")
            
            with insight_cols[1]:
                high_latency = latest_all[latest_all['latency'] > 150]
                if not high_latency.empty:
                    st.warning(f"**Execution Risk:** High latency on {', '.join(high_latency.index.tolist())}. Possible slippage.")
                else:
                    st.success("**Network:** Stable connection. Optimal latency for HFT.")
            
            with insight_cols[2]:
                buying_pressure = latest_all[latest_all['imbalance'] > 0.7]
                if not buying_pressure.empty:
                    st.info(f"**Pressure:** Strong accumulation (Bid pressure) on {', '.join(buying_pressure.index.tolist())}.")
                else:
                    st.write("**Order Book:** Relative balance between Bid and Ask.")

        st.divider()

        col_top1, col_top2 = st.columns([1, 2])
        
        with col_top1:
            st.subheader("Average Spread Indicator")
            if not st.session_state.master_history.empty:
                avg_spreads = st.session_state.master_history.groupby('symbol')['spread'].mean().reset_index()
                st.dataframe(avg_spreads.rename(columns={'spread': 'Avg Spread ($)'}), width='stretch')
            
        with col_top2:
            st.subheader("Correlation Heatmap")
            if len(st.session_state.master_history) > len(SYMBOLS) * 2:
                corr_df = st.session_state.master_history.pivot_table(index='time', columns='symbol', values='spread').corr()
                corr_df.index.name = 'asset_x'
                corr_df.columns.name = 'asset_y'
                corr_data = corr_df.stack().reset_index(name='correlation')
                
                heatmap = alt.Chart(corr_data).mark_rect().encode(
                    x=alt.X('asset_x:N', title=None),
                    y=alt.Y('asset_y:N', title=None),
                    color=alt.Color('correlation:Q', scale=alt.Scale(scheme='blueorange', domain=[-1, 1])),
                    tooltip=['asset_x', 'asset_y', 'correlation']
                ).properties(height=250)
                st.altair_chart(heatmap, width='stretch')

        st.divider()

        col_mid1, col_mid2 = st.columns([2, 1])
        with col_mid1:
            st.subheader("Market Liquidity Flow")
            history_valid = st.session_state.master_history.dropna(subset=['time', 'liquidity'])
            
            if len(history_valid) > 2: 
                selection = alt.selection_point(fields=['symbol'], bind='legend')
                liq_chart = alt.Chart(history_valid).mark_line(point=True).encode(
                    x=alt.X('time:T', axis=alt.Axis(title='Time', format='%H:%M:%S')),
                    y=alt.Y('liquidity:Q', title='Total Depth (Units)', scale=alt.Scale(zero=False)),
                    color='symbol:N',
                    opacity=alt.condition(selection, alt.value(1.0), alt.value(0.1))
                ).add_params(selection).properties(height=300)
                st.altair_chart(liq_chart, width='stretch')
            else:
                st.info("Collecting more data points for liquidity flow...")

        with col_mid2:
            st.subheader("Order Book Imbalance")
            if not st.session_state.master_history.empty:
                latest_imb = st.session_state.master_history.dropna(subset=['imbalance']).groupby('symbol').last().reset_index()
                
                if not latest_imb.empty:
                    imb_chart = alt.Chart(latest_imb).mark_bar().encode(
                        x=alt.X('imbalance:Q', scale=alt.Scale(domain=[0, 1]), title="Bids <--- Pressure ---> Asks"),
                        y=alt.Y('symbol:N', sort='-x'),
                        color=alt.condition(alt.datum.imbalance > 0.5, alt.value("#2ecc71"), alt.value("#e74c3c"))
                    ).properties(height=250)
                    st.altair_chart(imb_chart, width='stretch')
            else:
                st.info("Waiting for order book data...")
        st.divider()

        col_bot1, col_bot2 = st.columns([1, 1])
        with col_bot1:
            st.subheader("Alert Log (Net Profit > 0)")
            st.dataframe(st.session_state.alert_log, width='stretch', height=300)
            
        with col_bot2:
            st.subheader("Real-Time Summary & Trends")
            if len(st.session_state.master_history) > len(SYMBOLS):
                latest = st.session_state.master_history.groupby('symbol').tail(1)
                previous = st.session_state.master_history.groupby('symbol').nth(-2)
                summary = latest[['symbol', 'spread', 'liquidity', 'latency', 'net_profit']].copy()
                trends = []
                for s in SYMBOLS:
                    try:
                        curr = latest[latest['symbol'] == s]['spread'].values[0]
                        prev = previous[previous['symbol'] == s]['spread'].values[0]
                        trends.append("▲" if curr > prev else "▼" if curr < prev else "〓")
                    except:
                        trends.append("〓")
                summary['Trend'] = trends
                st.dataframe(summary, width='stretch', height=300)

    time.sleep(1)