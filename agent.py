import yfinance as yf
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

print("Agent starter...")

c25_aktier = [
    "ALK-B.CO", "AMBU-B.CO", "CARL-B.CO", "COLO-B.CO", "DNORD.CO",
    "DEMANT.CO", "DSV.CO", "FLS.CO", "GMAB.CO", "GN.CO", "ISS.CO",
    "MAERSK-A.CO", "MAERSK-B.CO", "NDA-DK.CO", "NOVO-B.CO",
    "NZYM-B.CO", "ORSTED.CO", "PNDORA.CO", "ROCK-B.CO",
    "TRYG.CO", "VWS.CO", "ZEAL.CO"
]

over_ema50 = []
købssignaler = []
salgssignaler = []

def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

print("Analyserer...")

for aktie in c25_aktier:
    try:
        ticker = yf.Ticker(aktie)
        data = ticker.history(period="1y")

        if data.empty or len(data) < 100:
            continue

        # EMA
        data['EMA50'] = data['Close'].ewm(span=50).mean()
        data['EMA100'] = data['Close'].ewm(span=100).mean()

        # RSI
        data['RSI'] = calculate_rsi(data)

        # MACD
        ema12 = data['Close'].ewm(span=12).mean()
        ema26 = data['Close'].ewm(span=26).mean()
        data['MACD'] = ema12 - ema26
        data['Signal'] = data['MACD'].ewm(span=9).mean()

        last = data.tail(2)

        close_now = last['Close'].iloc[1]
        ema50_now = last['EMA50'].iloc[1]
        ema100_now = last['EMA100'].iloc[1]

        ema50_prev = last['EMA50'].iloc[0]
        ema100_prev = last['EMA100'].iloc[0]

        rsi = round(last['RSI'].iloc[1], 2)

        macd_now = last['MACD'].iloc[1]
        signal_now = last['Signal'].iloc[1]

        macd_status = "Bullish" if macd_now > signal_now else "Bearish"

        pe = ticker.info.get("trailingPE", "N/A")

        navn = aktie.replace(".CO", "")

        # ✅ OVER EMA50
        if close_now > ema50_now:
            over_ema50.append({
                "navn": navn,
                "kurs": round(close_now, 2),
                "rsi": rsi,
                "macd": macd_status,
                "pe": pe
            })

        # ✅ KØBSSIGNAL (EMA50 krydser op)
        if ema50_prev < ema100_prev and ema50_now > ema100_now and close_now > ema50_now:
            købssignaler.append(navn)

        # ✅ SALGSSIGNAL (EMA50 krydser ned)
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
msg['Subject'] = "📊 C25 Trading Signal"

html = ""

# 🔹 Over EMA50
html += "<h3>Aktier OVER EMA50</h3><ul>"
for a in over_ema50:
    html += f"<li>{a['navn']} - {a['kurs']} DKK | RSI: {a['rsi']} | MACD: {a['macd']} | P/E: {a['pe']}</li>"
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
