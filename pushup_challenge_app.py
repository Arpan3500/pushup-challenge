import streamlit as st
import json
import os
from datetime import datetime, timedelta
import pandas as pd

DATA_FILE = "pushup_data.json"

# ------------------- Data Handling -------------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def log_pushups(username, count, date_str):
    data = load_data()
    user = data.get(username, {"daily_log": {}, "total_pushups": 0, "streak": 0})

    if date_str in user["daily_log"]:
        return False, "Already logged for this date."

    user["daily_log"][date_str] = count
    user["total_pushups"] = sum(user["daily_log"].values())

    # Update streak
    sorted_dates = sorted(user["daily_log"].keys())
    streak = 0
    today = datetime.today().strftime('%Y-%m-%d')
    for offset in range(len(sorted_dates)):
        check_date = (datetime.today() - timedelta(days=offset)).strftime('%Y-%m-%d')
        if check_date in user["daily_log"]:
            streak += 1
        else:
            break
    user["streak"] = streak

    data[username] = user
    save_data(data)
    return True, f"{count} pushups logged for {username} on {date_str}."

# ------------------- UI Sections -------------------
st.set_page_config(page_title="Pushup Challenge Tracker", layout="wide")
st.title("💪 90-Day Pushup Challenge Dashboard")

menu = st.sidebar.radio("Navigate", ["📊 Leaderboard", "🏋️ Log Today", "📅 Add Previous Data", "📈 My Stats"])

# ------------------- Leaderboard -------------------
if menu == "📊 Leaderboard":
    st.subheader("🏆 Leaderboard")
    data = load_data()
    if data:
        leaderboard = sorted([(u, info["total_pushups"], info["streak"]) for u, info in data.items()],
                             key=lambda x: (-x[1], -x[2]))
        df = pd.DataFrame(leaderboard, columns=["Name", "Total Pushups", "Streak"])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No data available yet.")

# ------------------- Log Today's Pushups -------------------
elif menu == "🏋️ Log Today":
    st.subheader("🏋️ Log Today's Pushups")
    username = st.text_input("Enter your name")
    count = st.number_input("Pushups today", min_value=1, step=1)
    if st.button("Log Pushups"):
        today = datetime.today().strftime('%Y-%m-%d')
        success, message = log_pushups(username.strip(), int(count), today)
        st.success(message) if success else st.warning(message)

# ------------------- Add Previous Data -------------------
elif menu == "📅 Add Previous Data":
    st.subheader("🕓 Add Pushups for a Previous Date")
    username = st.text_input("User name")
    date = st.date_input("Date")
    count = st.number_input("Pushups", min_value=1, step=1)
    if st.button("Add Entry"):
        date_str = date.strftime('%Y-%m-%d')
        success, message = log_pushups(username.strip(), int(count), date_str)
        st.success(message) if success else st.warning(message)

# ------------------- My Stats -------------------
elif menu == "📈 My Stats":
    st.subheader("📈 Personal Stats")
    username = st.text_input("Enter your name")
    if st.button("Show Stats"):
        data = load_data()
        user = data.get(username)
        if not user:
            st.warning("User not found.")
        else:
            st.markdown(f"**Total Pushups:** {user['total_pushups']}")
            st.markdown(f"**Current Streak:** {user['streak']}")

            daily = user["daily_log"]
            dates = list(daily.keys())
            values = list(daily.values())

            df = pd.DataFrame({"Date": pd.to_datetime(dates), "Pushups": values}).sort_values("Date")
            st.line_chart(df.set_index("Date"))
            st.bar_chart(df.set_index("Date"))
