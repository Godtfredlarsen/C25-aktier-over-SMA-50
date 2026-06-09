import yfinance as yf
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

print("Agent starter...")

def hent_aktier():
    try:
        url = "https://www.investing.com/indices/omx-copenhagen-25-components"
        tables = pd.read_html(url)
        df = tables[0]

        tickers = []

        for navn in df['Name']:
            navn = navn.upper()
            navn = navn.replace(" ", "-")
            navn = navn.replace(".", "")
            ticker = f"{navn}.CO"

            tickers.append(ticker)

        return list(set(tickers))

    except Exception as e:
        print("Fejl ved hentning:", e)
        return []

over_ema50 = []
købssignaler = []
salgssignaler = []

print("Henter aktier...")
aktier = hent_aktier()

print("Analyserer...")

for aktie in aktier:
    try:
        ticker = yf.Ticker(aktie)
        data = ticker.history(period="1y")

        if data.empty or len(data) < 100:
            continue

        # EMA
        data['EMA50'] = data['Close'].ewm(span=50).mean()
        data['EMA100'] = data['Close'].ewm(span=100).mean()

        last = data.tail(2)

        close_now = last['Close'].iloc[1]
        ema50_now = last['EMA50'].iloc[1]
        ema100_now = last['EMA100'].iloc[1]

        ema50_prev = last['EMA50'].iloc[0]
        ema100_prev = last['EMA100'].iloc[0]

        navn = aktie.replace(".CO", "")

        # ✅ Over EMA50
        if close_now > ema50_now:
            over_ema50.append(f"{navn} - {round(close_now,2)} DKK")

        # ✅ Købssignal
        if ema50_prev < ema100_prev and ema50_now > ema100_now and close_now > ema50_now:
            købssignaler.append(navn)

        # ✅ Salgssignal
        if ema50_prev > ema100_prev and ema50_now < ema100_now:
            salgssignaler.append(navn)

    except Exception as e:
        print(f"Fejl ved {aktie}: {e}")

# ✅ EMAIL
MIN_EMAIL = "mgl@godtfredlarsen.com"
PASSWORD = os.environ.get("EMAIL_PASSWORD")

msg = MIMEMultipart()
msg['From'] = MIN_EMAIL
msg['To'] = MIN_EMAIL
msg['Subject'] = "📊 C25 + Large Cap Signals"

html = ""

# 🔹 Over EMA50
html += "<h3>Aktier OVER EMA50</h3><ul>"
for a in over_ema50:
    html += f"<li>{a}</li>"
html += "</ul>"

# 🔹 Køb
html += "<h3>📈 Købssignaler</h3><ul>"
for a in købssignaler:
    html += f"<li>{a}</li>"
html += "</ul>"

# 🔹 Salg
html += "<h3>📉 Salgssignaler</h3><ul>"
for a in salgssignaler:
    html += f"<li>{a}</li>"
html += "</ul>"

msg.attach(MIMEText(html, 'html'))

# ✅ Send mail
if PASSWORD and PASSWORD.strip():
    try:
        server = smtplib.SMTP("send.one.com", 587)
        server.starttls()
        server.login(MIN_EMAIL, PASSWORD)
        server.sendmail(MIN_EMAIL, MIN_EMAIL, msg.as_string())
        server.quit()
        print("MAIL SENDT ✅")
    except Exception as e:
        print("MAIL FEJL:", e)
else:
    print("PASSWORD PROBLEM")
``
