import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Human vs Algo Market Simulator", layout="wide")

# -----------------------------
# SESSION STATE INIT
# -----------------------------
if "price" not in st.session_state:
    st.session_state.price = 100.0
    st.session_state.round = 1
    st.session_state.history = []
    st.session_state.traders = {}
    st.session_state.initialized = False

# -----------------------------
# TITLE
# -----------------------------
st.title("🤖📈 Human vs Algorithm Trading Simulator")
st.caption("Live classroom market microstructure experiment-Designed by Prof.Shalini Velappan")

# -----------------------------
# SETUP
# -----------------------------
st.sidebar.header("⚙️ Simulation Setup")

num_humans = st.sidebar.number_input("Number of Human Traders", 1, 100, 10)
num_algos = st.sidebar.number_input("Number of Algo Bots", 1, 100, 5)

start_button = st.sidebar.button("🚀 Initialize Market")

if start_button or not st.session_state.initialized:
    st.session_state.traders = {}

    # Create humans
    for i in range(num_humans):
        st.session_state.traders[f"Human_{i+1}"] = {
            "type": "human",
            "cash": 100000.0,
            "shares": 100,
            "pnl": 0.0
        }

    # Create algos
    algo_types = ["momentum", "meanrev", "panic"]
    for i in range(num_algos):
        st.session_state.traders[f"Algo_{i+1}"] = {
            "type": "algo",
            "algo_type": np.random.choice(algo_types),
            "cash": 100000.0,
            "shares": 100,
            "pnl": 0.0
        }

    st.session_state.price = 100.0
    st.session_state.round = 1
    st.session_state.history = []
    st.session_state.initialized = True

# -----------------------------
# MARKET STATUS
# -----------------------------
st.subheader("📊 Market Status")

col1, col2, col3 = st.columns(3)
col1.metric("Current Price", f"₹ {st.session_state.price:.2f}")
col2.metric("Round", st.session_state.round)
col3.metric("Total Traders", len(st.session_state.traders))

# -----------------------------
# HUMAN ORDER ENTRY
# -----------------------------
st.subheader("🧍 Human Traders — Enter Orders")

human_orders = {}

human_cols = st.columns(3)

i = 0
for name, t in st.session_state.traders.items():
    if t["type"] == "human":
        with human_cols[i % 3]:
            st.markdown(f"**{name}**")
            action = st.selectbox(f"{name} Action", ["HOLD", "BUY", "SELL"], key=f"{name}_action")
            qty = st.number_input(f"{name} Qty", 0, 1000, 0, key=f"{name}_qty")

            human_orders[name] = (action, qty)
        i += 1

# -----------------------------
# RUN ROUND
# -----------------------------
if st.button("▶️ Run Next Round"):

    buy_volume = 0
    sell_volume = 0

    last_price = st.session_state.price

    # -----------------------------
    # PROCESS HUMAN ORDERS
    # -----------------------------
    for name, (action, qty) in human_orders.items():
        trader = st.session_state.traders[name]

        if action == "BUY" and qty > 0:
            cost = qty * st.session_state.price
            if trader["cash"] >= cost:
                trader["cash"] -= cost
                trader["shares"] += qty
                buy_volume += qty

        if action == "SELL" and qty > 0:
            if trader["shares"] >= qty:
                trader["shares"] -= qty
                trader["cash"] += qty * st.session_state.price
                sell_volume += qty

    # -----------------------------
    # PROCESS ALGO ORDERS
    # -----------------------------
    for name, trader in st.session_state.traders.items():
        if trader["type"] == "algo":

            algo = trader["algo_type"]
            qty = 10

            # Momentum
            if algo == "momentum":
                if len(st.session_state.history) > 0:
                    if st.session_state.price > st.session_state.history[-1]["price"]:
                        # buy
                        if trader["cash"] >= qty * st.session_state.price:
                            trader["cash"] -= qty * st.session_state.price
                            trader["shares"] += qty
                            buy_volume += qty
                    else:
                        if trader["shares"] >= qty:
                            trader["shares"] -= qty
                            trader["cash"] += qty * st.session_state.price
                            sell_volume += qty

            # Mean Reversion
            elif algo == "meanrev":
                if st.session_state.price > 105:
                    if trader["shares"] >= qty:
                        trader["shares"] -= qty
                        trader["cash"] += qty * st.session_state.price
                        sell_volume += qty
                elif st.session_state.price < 95:
                    if trader["cash"] >= qty * st.session_state.price:
                        trader["cash"] -= qty * st.session_state.price
                        trader["shares"] += qty
                        buy_volume += qty

            # Panic Bot
            elif algo == "panic":
                if len(st.session_state.history) > 0:
                    if st.session_state.price < 0.95 * st.session_state.history[-1]["price"]:
                        panic_qty = 30
                        if trader["shares"] >= panic_qty:
                            trader["shares"] -= panic_qty
                            trader["cash"] += panic_qty * st.session_state.price
                            sell_volume += panic_qty

    # -----------------------------
    # PRICE UPDATE
    # -----------------------------
    imbalance = buy_volume - sell_volume

    price_change = imbalance / 50.0  # market depth rule
    st.session_state.price = max(1.0, st.session_state.price + price_change)

    # -----------------------------
    # UPDATE PnL
    # -----------------------------
    for trader in st.session_state.traders.values():
        trader["pnl"] = trader["cash"] + trader["shares"] * st.session_state.price - 100000 - 100 * 100

    # -----------------------------
    # SAVE HISTORY
    # -----------------------------
    st.session_state.history.append({
        "round": st.session_state.round,
        "price": st.session_state.price,
        "buy_volume": buy_volume,
        "sell_volume": sell_volume
    })

    st.session_state.round += 1

# -----------------------------
# PRICE CHART
# -----------------------------
if len(st.session_state.history) > 0:
    st.subheader("📈 Price Evolution")

    df_hist = pd.DataFrame(st.session_state.history)
    st.line_chart(df_hist.set_index("round")["price"])

# -----------------------------
# LEADERBOARD
# -----------------------------
st.subheader("🏆 Trader Leaderboard")

rows = []
for name, t in st.session_state.traders.items():
    rows.append({
        "Trader": name,
        "Type": t["type"] if t["type"] == "human" else t["algo_type"],
        "Cash": round(t["cash"], 2),
        "Shares": t["shares"],
        "PnL": round(t["pnl"], 2)
    })

df = pd.DataFrame(rows).sort_values("PnL", ascending=False)
st.dataframe(df, use_container_width=True)

# -----------------------------
# TEACHING PANEL
# -----------------------------
st.info("""
🎓 Teaching Tips:
- Let students run 3–4 calm rounds
- Then announce: "🚨 Bad results rumour!"
- Then announce: "✅ Clarification!"
- Watch momentum + panic bots create crashes and rebounds
- Ask: Who caused volatility? Did any single trader intend it?
""")
