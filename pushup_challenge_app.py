import streamlit as st
import json, os
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.message import EmailMessage

DATA_FILE = "pushup_data.json"
USER_FILE = "user_credentials.json"
CONFIG_FILE = "config.json"

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

def load_config():
    return json.load(open(CONFIG_FILE, 'r'))

# Login
def login():
    st.title("90 Days Pushup Challenge")
    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        username = st.text_input("Username")
        pin = st.text_input("PIN", type="password")
        if st.button("Login"):
            users = load_users()
            if username in users and users[username] == pin:
                st.success(f"Welcome, {username}!")
                return username
            else:
                st.error("Invalid credentials")
                return None

    with tab2:
        new_user = st.text_input("New Username")
        new_pin = st.text_input("New PIN", type="password")
        email = st.text_input("Email")
        if st.button("Register"):
            users = load_users()
            if new_user in users:
                st.warning("User already exists")
            else:
                users[new_user] = new_pin
                save_users(users)
                data = load_data()
                data[new_user] = {
                    "total_pushups": 0,
                    "daily_log": {},
                    "streak": 0,
                    "last_entry": "",
                    "email": email
                }
                save_data(data)
                st.success("User registered!")
    return None

# User Dashboard
def user_dashboard(username):
    st.header(f"Welcome, {username}")
    data = load_data()
    user = data.get(username)

    today = datetime.today().strftime('%Y-%m-%d')
    if user["last_entry"] == today:
        st.info("You already submitted today.")
    else:
        pushups = st.number_input("Pushups today", min_value=1, step=1)
        if st.button("Submit Pushups"):
            yesterday = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
            user["streak"] = user["streak"] + 1 if user["last_entry"] == yesterday else 1
            user["daily_log"][today] = pushups
            user["total_pushups"] += pushups
            user["last_entry"] = today
            data[username] = user
            save_data(data)
            st.success("Logged successfully!")

    # Stats
    st.subheader("Stats")
    st.write(f"**Total Pushups**: {user['total_pushups']}")
    st.write(f"**Streak**: {user['streak']} days")

    # Weekly Summary
    st.subheader("Weekly Progress")
    df = pd.DataFrame.from_dict(user["daily_log"], orient="index", columns=["Pushups"])
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    last_7 = df.last('7D')
    if not last_7.empty:
        st.line_chart(last_7)
        avg = last_7["Pushups"].mean()
        st.metric("Avg Pushups (last 7 days)", f"{avg:.1f}")
    else:
        st.info("No pushups in last 7 days")

    st.subheader("Daily Log")
    st.dataframe(df[::-1])

# Admin Dashboard
def admin_dashboard():
    st.header("Admin Panel")

    username = st.text_input("Username to update")
    csv_data = st.text_area("Enter 11 values (comma-separated)")
    if st.button("Add 11-Day History"):
        values = [int(x) for x in csv_data.split(",")]
        if len(values) != 11:
            st.error("Need 11 values.")
            return
        data = load_data()
        if username not in data:
            data[username] = {"total_pushups": 0, "daily_log": {}, "streak": 0, "last_entry": "", "email": ""}
        user = data[username]
        start_day = datetime.today() - timedelta(days=11)
        for i, val in enumerate(values):
            day = (start_day + timedelta(days=i)).strftime('%Y-%m-%d')
            user["daily_log"][day] = val
            user["total_pushups"] += val
        user["streak"] = sum(1 for i in range(10, -1, -1)
                             if user["daily_log"].get((datetime.today() - timedelta(days=i)).strftime('%Y-%m-%d'), 0) > 0)
        user["last_entry"] = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
        data[username] = user
        save_data(data)
        st.success("History added!")

    # Leaderboard
    st.subheader("Leaderboard")
    data = load_data()
    lb = sorted(data.items(), key=lambda x: x[1]["total_pushups"], reverse=True)
    for i, (u, info) in enumerate(lb, 1):
        st.write(f"{i}. **{u}** — {info['total_pushups']} pushups | Streak: {info['streak']}")

    # Send Weekly Email
    st.subheader("Send Weekly Emails")
    if st.button("Send"):
        send_weekly_emails()
        st.success("Emails sent!")

# Email
def send_weekly_emails():
    config = load_config()
    data = load_data()
    sender = config["sender_email"]
    app_pass = config["app_password"]

    for user, info in data.items():
        email = info.get("email", "")
        if not email:
            continue
        df = pd.DataFrame.from_dict(info["daily_log"], orient="index", columns=["Pushups"])
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        last_7 = df.last('7D')
        if last_7.empty:
            continue
        avg = last_7["Pushups"].mean()
        msg = EmailMessage()
        msg["Subject"] = "Your Weekly Pushup Progress"
        msg["From"] = sender
        msg["To"] = email
        msg.set_content(f"Hey {user},\n\nHere's your last 7 days summary:\n\n" +
                        last_7.to_string() + f"\n\nAverage: {avg:.1f} pushups/day\n\nKeep going!")
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(sender, app_pass)
                smtp.send_message(msg)
        except Exception as e:
            print(f"Failed to email {user}: {e}")

# Main
def main():
    user = login()
    if user:
        if user == "admin":
            admin_dashboard()
        else:
            user_dashboard(user)

if __name__ == "__main__":
    main()
