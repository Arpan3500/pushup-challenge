import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime, timedelta

# Files
DATA_FILE = "pushup_data.json"
USER_FILE = "user_credentials.json"

# Loaders and Savers
def load_data():
    if not os.path.exists(DATA_FILE):
        json.dump({}, open(DATA_FILE, 'w'))
    return json.load(open(DATA_FILE, 'r'))

def save_data(data):
    json.dump(data, open(DATA_FILE, 'w'), indent=4)

def load_users():
    if not os.path.exists(USER_FILE):
        json.dump({"admin": "0000"}, open(USER_FILE, 'w'))
    return json.load(open(USER_FILE, 'r'))

def save_users(users):
    json.dump(users, open(USER_FILE, 'w'), indent=4)

# Public Leaderboard
def show_leaderboard():
    st.title("📊 Pushup Challenge Leaderboard")
    data = load_data()
    if not data:
        st.info("No participants yet.")
        return
    leaderboard = sorted(data.items(), key=lambda x: x[1]['total_pushups'], reverse=True)
    for i, (user, info) in enumerate(leaderboard, 1):
        st.write(f"{i}. **{user}** — {info['total_pushups']} pushups | Streak: {info['streak']} days")

# Login and Register
def login():
    users = load_users()
    st.subheader("Login")
    username = st.text_input("Username")
    pin = st.text_input("PIN", type="password")
    if st.button("Login"):
        if username in users and users[username] == pin:
            st.session_state['user'] = username
            st.success(f"Logged in as {username}")
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")

def register():
    users = load_users()
    st.subheader("Register")
    new_user = st.text_input("New Username")
    new_pin = st.text_input("New PIN", type="password")
    if st.button("Register"):
        if new_user in users:
            st.warning("User already exists")
        else:
            users[new_user] = new_pin
            save_users(users)
            data = load_data()
            data[new_user] = {"total_pushups": 0, "daily_log": {}, "streak": 0, "last_entry": ""}
            save_data(data)
            st.success("User registered! Please login.")

# User Dashboard
def user_dashboard():
    username = st.session_state['user']
    st.title(f"Welcome, {username}")
    data = load_data()
    user = data[username]

    today = datetime.today().strftime('%Y-%m-%d')
    if user["last_entry"] == today:
        st.info("Today's pushups already logged.")
    else:
        pushups = st.number_input("Pushups Today", min_value=1, step=1)
        if st.button("Submit"):
            yesterday = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
            user["streak"] = user["streak"] + 1 if user["last_entry"] == yesterday else 1
            user["daily_log"][today] = pushups
            user["total_pushups"] += pushups
            user["last_entry"] = today
            data[username] = user
            save_data(data)
            st.success("Pushups logged successfully!")
            st.experimental_rerun()

    st.subheader("Your Stats")
    st.write(f"**Total Pushups**: {user['total_pushups']}")
    st.write(f"**Current Streak**: {user['streak']} days")

    if user['daily_log']:
        df = pd.DataFrame.from_dict(user['daily_log'], orient='index', columns=['Pushups'])
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        st.line_chart(df[-7:])
        st.dataframe(df[::-1])

# Admin Panel to feed data
def admin_panel():
    st.title("🛠️ Admin Panel – Feed Previous Data")
    
    data = load_data()
    usernames = list(data.keys())
    if not usernames:
        st.warning("No users found.")
        return
    
    username = st.selectbox("Select a user", usernames)
    num_days = st.number_input("How many days of data to add?", min_value=1, max_value=90, step=1)

    values = st.text_area(f"Enter {num_days} pushup values (comma-separated)")
    
    if st.button("Submit Data"):
        pushup_values = [int(v.strip()) for v in values.split(",") if v.strip().isdigit()]
        if len(pushup_values) != num_days:
            st.error(f"Please enter exactly {num_days} pushup values.")
            return
        
        user = data[username]
        start_date = datetime.today() - timedelta(days=num_days)
        
        for i, count in enumerate(pushup_values):
            day = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
            if day not in user["daily_log"]:
                user["daily_log"][day] = count
                user["total_pushups"] += count

        # Update last_entry and streak
        user["last_entry"] = max(user["daily_log"].keys())
        # Count consecutive streak ending at yesterday
        streak = 0
        for i in range(1, 100):  # max 100 day backtrack
            day = (datetime.today() - timedelta(days=i)).strftime('%Y-%m-%d')
            if user["daily_log"].get(day, 0) > 0:
                streak += 1
            else:
                break
        user["streak"] = streak

        data[username] = user
        save_data(data)
        st.success(f"✅ {num_days} days of pushup data added for {username}!")

# Main App
st.set_page_config(page_title="Pushup Challenge", layout="centered")

menu = st.sidebar.radio("Navigate", ["Leaderboard", "Login", "Register"])

if "user" not in st.session_state:
    st.session_state['user'] = None

if st.session_state['user']:
    if st.session_state['user'] == "admin":
        admin_panel()
    else:
        user_dashboard()
else:
    if menu == "Leaderboard":
        show_leaderboard()
    elif menu == "Login":
        login()
    elif menu == "Register":
        register()
