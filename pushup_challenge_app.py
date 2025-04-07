import streamlit as st
import json
import os
from datetime import datetime, timedelta

DATA_FILE = 'pushup_data.json'

# Load or initialize data
def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w') as f:
            json.dump({}, f)
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# Update today's pushup entry
def update_today(username, pushups):
    today = datetime.today().strftime('%Y-%m-%d')
    data = load_data()

    if username not in data:
        data[username] = {
            "total_pushups": 0,
            "daily_log": {},
            "streak": 0,
            "last_entry": ""
        }

    user = data[username]
    if user["last_entry"] == today:
        return False, "You've already submitted today."

    # Streak check
    yesterday = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    if user["last_entry"] == yesterday:
        user["streak"] += 1
    else:
        user["streak"] = 1

    # Update info
    user["daily_log"][today] = pushups
    user["total_pushups"] += pushups
    user["last_entry"] = today

    data[username] = user
    save_data(data)
    return True, "Submission successful!"

# Leaderboard logic
def get_leaderboard():
    data = load_data()
    return sorted(data.items(), key=lambda x: x[1]["total_pushups"], reverse=True)

# Admin feature
def admin_section():
    st.subheader("Admin: Add 11-Day History")
    code = st.text_input("Enter Admin Code", type="password")
    if code != "admin123":  # change this code for security
        return

    username = st.text_input("Enter username")
    pushup_input = st.text_area("Enter 11 pushup counts (comma-separated)", placeholder="50,60,40,...")

    if st.button("Submit History"):
        try:
            pushup_list = [int(x.strip()) for x in pushup_input.split(",")]
            if len(pushup_list) != 11:
                st.error("Please enter exactly 11 values.")
                return

            data = load_data()
            if username not in data:
                data[username] = {
                    "total_pushups": 0,
                    "daily_log": {},
                    "streak": 0,
                    "last_entry": ""
                }

            user = data[username]
            start_day = datetime.today() - timedelta(days=11)
            for i, val in enumerate(pushup_list):
                date_str = (start_day + timedelta(days=i)).strftime('%Y-%m-%d')
                user["daily_log"][date_str] = val
                user["total_pushups"] += val

            # Recalculate streak
            streak = 0
            for i in range(10, -1, -1):
                check_day = (datetime.today() - timedelta(days=i)).strftime('%Y-%m-%d')
                if user["daily_log"].get(check_day, 0) > 0:
                    streak += 1
                else:
                    break

            user["streak"] = streak
            user["last_entry"] = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
            data[username] = user
            save_data(data)
            st.success(f"11-day history added for {username}.")
        except Exception as e:
            st.error(f"Error: {e}")

# Main app layout
def main():
    st.title("90 Days Pushup Challenge")
    st.markdown("Log your pushups daily. Keep your streak alive!")

    username = st.text_input("Enter your name").strip().lower()
    pushups = st.number_input("Pushups today", min_value=1, step=1)

    if st.button("Submit"):
        if not username:
            st.warning("Please enter your name.")
        else:
            success, msg = update_today(username, int(pushups))
            st.success(msg) if success else st.error(msg)

    st.subheader("Leaderboard")
    leaderboard = get_leaderboard()
    for idx, (user, info) in enumerate(leaderboard, 1):
        st.write(f"{idx}. **{user}** — {info['total_pushups']} pushups | Streak: {info['streak']}")

    # Admin section at the bottom
    admin_section()

if __name__ == "__main__":
    main()