import yfinance as yf
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

print("Agent starter...")

# ✅ C25 liste (korrekt tickers)
aktier = [
    "ALK-B.CO", "AMBU-B.CO", "CARL-B.CO", "COLO-B.CO", "DNORD.CO",
    "DEMANT.CO", "DSV.CO", "FLS.CO", "GMAB.CO", "GN.CO", "ISS.CO",
    "MAERSK-A.CO", "MAERSK-B.CO", "NDA-DK.CO", "NOVO-B.CO",
    "NZYM-B.CO", "ORSTED.CO", "PNDORA.CO", "ROCK-B.CO",
    "TRYG.CO", "VWS.CO", "ZEAL.CO"
]

over_ema50 = []

print("Analyserer...")

for aktie in aktier:
    try:
        ticker = yf.Ticker(aktie)
        data = ticker.history(period="1y")

        if data.empty or len(data) < 100:
            continue

        # ✅ EMA50
        data['EMA50'] = data['Close'].ewm(span=50).mean()

        # ✅ Brug KUN sidste afsluttede dag
        last = data.tail(1)

        close_now = last['Close'].iloc[0]
        ema50_now = last['EMA50'].iloc[0]

        navn = aktie.replace(".CO", "")

        # ✅ Køb = kurs over EMA50
        if close_now > ema50_now:
            over_ema50.append(f"{navn} - {round(close_now, 2)} DKK")

    except Exception as e:
        print(f"Fejl ved {aktie}: {e}")

# ✅ EMAIL
MIN_EMAIL = "mgl@godtfredlarsen.com"
PASSWORD = os.environ.get("EMAIL_PASSWORD")

msg = MIMEMultipart()
msg['From'] = MIN_EMAIL
msg['To'] = MIN_EMAIL
msg['Subject'] = "📊 C25 EMA50 Status"

# ✅ Email indhold (ALTID sendt)
if over_ema50:
    html = "<h3>Aktier OVER EMA50</h3><ul>"
    for a in over_ema50:
        html += f"<li>{a}</li>"
    html += "</ul>"
else:
    html = "<p>Ingen aktier er over EMA50.</p>"

msg.attach(MIMEText(html, 'html'))

# ✅ SEND MAIL
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
