from bs4 import BeautifulSoup
import requests
import smtplib
from email.mime.text import MIMEText
import os
import pandas as pd

EMAIL_FROM = os.environ.get("EMAIL_FROM")
EMAIL_TO = os.environ.get("EMAIL_TO")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

URLS = {
    "bettingguru": "https://www.spilxperten.com/ekspert/bettingguru/",
    "loso": "https://www.spilxperten.com/ekspert/loso/",
    "frank-pilantra": "https://www.spilxperten.com/ekspert/frank-pilantra/"
}

EXCEL_FILE = "betting_tips.xlsx"

def fetch_active_suggestions(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.content, "html.parser")

    target_titles = [
        "Aktive spilforslag fra BettingGuru",
        "Aktive spilforslag fra Loso",
        "Aktive spilforslag fra Frank Pilantra"
    ]

    results = []
    containers = soup.select("div.bg-white.bc-text-container")
    for container in containers:
        h3 = container.find("h3")
        if h3:
            title = h3.get_text(strip=True)
            if title in target_titles:
                tip_items = container.select("div.bc-tips-loop-item")
                for item in tip_items:
                    text = item.get_text(strip=True)
                    results.append(text)
    return set(results)

def load_previous_data():
    if os.path.exists(EXCEL_FILE):
        df = pd.read_excel(EXCEL_FILE, engine='openpyxl')
        prev_data = {}
        for name in URLS:
            tips = df[df['Source'] == name]['Tip'].tolist()
            prev_data[name] = set(tips)
        return prev_data
    else:
        return {name: set() for name in URLS}

def save_current_data(data_dict):
    all_data = []
    for name, tips in data_dict.items():
        for tip in tips:
            all_data.append({'Source': name, 'Tip': tip})
    df = pd.DataFrame(all_data)
    df.to_excel(EXCEL_FILE, index=False, engine='openpyxl')

def send_email_alert(new_data):
    subject = "New Active Betting Suggestion Alert"
    body = "New betting suggestions found:\n\n"
    for name, items in new_data.items():
        body += f"\n🧠 {name.upper()}:\n" + "\n".join(items) + "\n"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.send_message(msg)

def monitor():
    print("Monitoring started...")

    last_seen = load_previous_data()
    new_data = {}
    current_data = {}

    for name, url in URLS.items():
        current = fetch_active_suggestions(url)
        current_data[name] = current
        new_tips = current - last_seen.get(name, set())
        if new_tips:
            new_data[name] = new_tips

    if new_data:
        send_email_alert(new_data)
        save_current_data(current_data)
        print("Email sent with new tips.")
    else:
        print("No new tips found.")

monitor()
