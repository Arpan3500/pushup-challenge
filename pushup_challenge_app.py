import streamlit as st
import json
import os
from datetime import datetime, timedelta

DATA_FILE = 'pushup_data.json'

# Load data
def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w') as f:
            json.dump({}, f)
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

# Save data
def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# Update user for today
def update_user(username, pushups):
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
    last_entry = user.get("last_entry", "")
    yesterday = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')

    if last_entry == today:
        return False, "Already submitted today."

    if last_entry == yesterday:
        user["streak"] += 1
    else:
        user["streak"] = 1

    user["daily_log"][today] = pushups
    user["total_pushups"] += pushups
    user["last_entry"] = today

    data[username] = user
    save_data(data)
    return True, "Pushups submitted!"

# Leaderboard
def get_leaderboard():
    data = load_data()
    return sorted(data.items(), key=lambda x: x[1]['total_pushups'], reverse=True)

# Admin historical data entry
def admin_add_history():
    st.subheader("Admin: Add Past Pushup Data")
    admin_code = st.text_input("Enter Admin Code", type="password")

    if admin_code == "admin123":  # You can change this to a private code
        username = st.text_input("User Name (lowercase)")
        past_data = st.text_area("Enter 11-day pushup data (comma-separated)", placeholder="50,60,55,70,...")

        if st.button("Add History"):
            try:
                pushup_list = [int(x.strip()) for x in past_data.split(",")]
                if len(pushup_list) != 11:
                    st.error("Please enter exactly 11 days of data.")
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
                start_day = datetime.today() - timedelta(days=len(pushup_list))
                for i, count in enumerate(pushup_list):
                    day = (start_day + timedelta(days=i)).strftime('%Y-%m-%d')
                    user["daily_log"][day] = count
                    user["total_pushups"] += count

                # Recalculate streak
                streak = 0
                for i in range(11):
                    day = (datetime.today() - timedelta(days=i)).strftime('%Y-%m-%d')
                    if user["daily_log"].get(day, 0) > 0:
                        streak += 1
                    else:
                        break

                user["streak"] = streak
                user["last_entry"] = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
                data[username] = user
                save_data(data)
                st.success(f"Updated history for {username}.")
            except Exception as e:
                st.error(f"Error processing data: {e}")

# Main app
def main():
    st.title("90 Days Pushup Challenge")
    st.markdown("Track your daily pushups. Don't skip or your streak resets!")

    username = st.text_input("Enter your name (no spaces)", max_chars=20)
    pushups = st.number_input("Enter today's pushup count", min_value=1, step=1)

    if st.button("Submit"):
        if not username:
            st.warning("Please enter your name.")
        else:
            success, message = update_user(username.lower(), int(pushups))
            if success:
                st.success(message)
            else:
                st.error(message)

    st.subheader("Leaderboard")
    leaderboard = get_leaderboard()
    for idx, (name, info) in enumerate(leaderboard, 1):
        st.write(f"**{idx}. {name.capitalize()}** - {info['total_pushups']} pushups | Streak: {info['streak']}")

    # Call admin section
    admin_add_history()

if __name__ == "__main__":
    main()