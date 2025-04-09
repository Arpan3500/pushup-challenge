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
    st.title("Admin Panel")
    username = st.text_input("Username to Update")
    values = st.text_area("Enter 11-day pushup values (comma-separated)")
    if st.button("Feed 11 Days Data"):
        values = [int(v.strip()) for v in values.split(",") if v.strip().isdigit()]
        if len(values) != 11:
            st.error("Please enter exactly 11 numbers.")
            return
        data = load_data()
        if username not in data:
            data[username] = {"total_pushups": 0, "daily_log": {}, "streak": 0, "last_entry": ""}
        user = data[username]
        start_date = datetime.today() - timedelta(days=11)
        for i, count in enumerate(values):
            day = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
            user["daily_log"][day] = count
            user["total_pushups"] += count
        user["last_entry"] = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
        user["streak"] = sum(1 for i in range(10, -1, -1)
                             if user["daily_log"].get((datetime.today() - timedelta(days=i)).strftime('%Y-%m-%d'), 0) > 0)
        data[username] = user
        save_data(data)
        st.success("Data fed successfully!")

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
