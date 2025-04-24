import streamlit as st
import json
import os
from datetime import datetime, timedelta
import pandas as pd


DATA_FILE = "pushup_data.json"

# ------------------ UTILITIES ------------------

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def log_pushups(username, count, date=None):
    data = load_data()
    user = data.get(username, {"daily_log": {}, "total_pushups": 0, "streak": 0})
    if not date:
        date = datetime.today().strftime('%Y-%m-%d')
    if date not in user["daily_log"]:
        user["daily_log"][date] = count
        user["total_pushups"] += count

    # Recalculate streak
    dates = sorted(user["daily_log"].keys())
    streak = 0
    for i in range(1, 100):
        check_date = (datetime.today() - timedelta(days=i)).strftime('%Y-%m-%d')
        if user["daily_log"].get(check_date, 0) > 0:
            streak += 1
        else:
            break
    user["streak"] = streak
    data[username] = user
    save_data(data)

# ------------------ MAIN APP ------------------

st.set_page_config(page_title="90-Day Pushup Challenge", layout="centered")
st.title("💪 90-Day Pushup Challenge")

menu = st.sidebar.radio("Menu", ["🏠 Leaderboard", "➕ Add Data", "📈 Stats"])

data = load_data()

# ------------------ LEADERBOARD ------------------

if menu == "🏠 Leaderboard":
    st.subheader("🏆 Leaderboard (Total Pushups)")
    if data:
        df = pd.DataFrame([
            {"User": user, "Total Pushups": info["total_pushups"], "Streak": info["streak"]}
            for user, info in data.items()
        ])
        st.dataframe(df.sort_values(by="Total Pushups", ascending=False), use_container_width=True)
    else:
        st.info("No data yet.")

# ------------------ ADD DATA ------------------

elif menu == "➕ Add Data":
    st.subheader("➕ Add Previous Pushup Data")

    username = st.text_input("Enter your name:")
    num_days = st.number_input("How many past days to enter?", min_value=1, max_value=90, step=1)

    values = st.text_area(f"Enter {num_days} pushup counts (comma-separated):")

    if st.button("Submit"):
        if not username or not values:
            st.error("Please fill all fields.")
        else:
            pushups = [int(x.strip()) for x in values.split(",") if x.strip().isdigit()]
            if len(pushups) != num_days:
                st.error(f"Enter exactly {num_days} values.")
            else:
                for i in range(num_days):
                    date = (datetime.today() - timedelta(days=num_days - i)).strftime('%Y-%m-%d')
                    log_pushups(username, pushups[i], date)
                st.success(f"✅ Added {num_days} days of data for {username}!")

# ------------------ STATS ------------------

elif menu == "📈 Stats":
    st.subheader("📊 User Progress & Stats")

    if data:
        selected_user = st.selectbox("Select a user", list(data.keys()))
        user_data = data[selected_user]

        total = user_data["total_pushups"]
        streak = user_data["streak"]
        log = user_data["daily_log"]

        st.markdown(f"**Total Pushups:** {total}")
        st.markdown(f"**Current Streak:** {streak} days")
        st.markdown(f"**Average/Day:** {round(total / len(log), 2)}")

        # Chart
        st.markdown("### 📈 Daily Pushup Progress")
        df = pd.DataFrame.from_dict(log, orient='index', columns=['Pushups'])
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()

        st.line_chart(df)

    else:
        st.info("No user data available.")
