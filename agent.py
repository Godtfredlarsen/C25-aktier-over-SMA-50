import yfinance as yf
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

print("Agent starter...")

# ✅ C25 liste
c25_aktier = [
    "ALK-B.CO", "AMBU-B.CO", "CARL-B.CO", "COLO-B.CO", "DNORD.CO",
    "DEMANT.CO", "DSV.CO", "FLS.CO", "GMAB.CO", "GN.CO", "ISS.CO",
    "MAERSK-A.CO", "MAERSK-B.CO", "NDA-DK.CO", "NOVO-B.CO",
    "NZYM-B.CO", "ORSTED.CO", "PNDORA.CO", "ROCK-B.CO",
    "TRYG.CO", "VWS.CO", "ZEAL.CO"
]

fundne_aktier = []

print("Analyserer C25...")

for aktie in c25_aktier:
    try:
        ticker = yf.Ticker(aktie)
        data = ticker.history(period="1y")  # ✅ 1 år

        if data.empty or len(data) < 55:
            continue

        # ✅ Beregn SMA50
        data['SMA50'] = data['Close'].rolling(50).mean()

        # ✅ Kun sidste 2 dage (seneste afsluttede dag)
        last = data.tail(2)

        forrige_luk = last['Close'].iloc[0]
        aktuel_luk = last['Close'].iloc[1]
        forrige_sma = last['SMA50'].iloc[0]
        aktuel_sma = last['SMA50'].iloc[1]

        if pd.isna(forrige_sma) or pd.isna(aktuel_sma):
            continue

        # ✅ KUN breakout på sidste dag
        if forrige_luk < forrige_sma and aktuel_luk > aktuel_sma:
            dato = last.index[1].strftime('%d-%m-%Y')

            fundne_aktier.append({
                "navn": aktie.replace(".CO", ""),
                "kurs": round(aktuel_luk, 2),
                "dato": dato
            })

    except Exception as e:
        print(f"Fejl ved {aktie}: {e}")

# ✅ EMAIL OPSÆTNING
MIN_EMAIL = "mgl@godtfredlarsen.com"
PASSWORD = os.environ.get("EMAIL_PASSWORD")

print("PASSWORD:", repr(PASSWORD))

msg = MIMEMultipart()
msg['From'] = MIN_EMAIL
msg['To'] = MIN_EMAIL
msg['Subject'] = "📊 C25 SMA50 Signal"

# ✅ Email indhold
if fundne_aktier:
    html = "<h3>Aktier der brød over SMA50 i dag:</h3><ul>"
    for aktie in fundne_aktier:
        html += f"<li>{aktie['navn']} - {aktie['kurs']} DKK ({aktie['dato']})</li>"
    html += "</ul>"
else:
    html = "<p>Ingen aktier brød over SMA50 på seneste handelsdag.</p>"

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
