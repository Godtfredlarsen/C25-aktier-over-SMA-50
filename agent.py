import yfinance as yf
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

c25_aktier = [
    "ALK-B.CO", "AMBU-B.CO", "CARL-B.CO", "COLO-B.CO", "DNORD.CO",
    "DEMANT.CO", "DSV.CO", "FLS.CO", "GMAB.CO", "GN.CO", "ISS.CO",
    "MAERSK-A.CO", "MAERSK-B.CO", "NDA-DK.CO", "NOVO-B.CO",
    "NZYM-B.CO", "ORSTED.CO", "PNDORA.CO", "ROCK-B.CO", "RY.CO",
    "TRYG.CO", "VWS.CO", "ZEAL.CO"
]

fundne_aktier = []

print("Agenten analyserer C25 indekset...")

for aktie in c25_aktier:
    try:
        ticker = yf.Ticker(aktie)
        data = ticker.history(period="100d")

        if data.empty or len(data) < 55:
            continue

        data['SMA50'] = data['Close'].rolling(50).mean()

        last = data.tail(2)

        forrige_luk = last['Close'].iloc[0]
        aktuel_luk = last['Close'].iloc[1]
        forrige_sma = last['SMA50'].iloc[0]
        aktuel_sma = last['SMA50'].iloc[1]

        if pd.isna(forrige_sma) or pd.isna(aktuel_sma):
            continue

        if forrige_luk < forrige_sma and aktuel_luk > aktuel_sma:
            dato_str = last.index[1].strftime('%d-%m-%Y')

            fundne_aktier.append({
                "navn": aktie.replace(".CO", ""),
                "kurs": round(aktuel_luk, 2),
                "sma": round(aktuel_sma, 2),
                "dato": dato_str
            })

    except Exception as e:
        print(f"Fejl ved {aktie}: {e}")

# ✅ EMAIL
MIN_EMAIL = "mgl@godtfredlarsen.com"

# ✅ HENT PASSWORD FRA GITHUB
PASSWORD = os.environ.get("EMAIL_PASSWORD")

print("PASSWORD FUNDEN:", PASSWORD is not None)

SMTP_SERVER = "send.one.com"

msg = MIMEMultipart()
msg['From'] = MIN_EMAIL
msg['To'] = MIN_EMAIL
msg['Subject'] = "C25 SMA50 Rapport"

if fundne_aktier:
    html = "<h3>Signaler fundet</h3><ul>"
    for a in fundne_aktier:
        html += f"<li>{a['navn']} - {a['kurs']}</li>"
    html += "</ul>"
else:
    html = "<p>Ingen signaler</p>"

msg.attach(MIMEText(html, 'html'))

if PASSWORD:
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
    print("PASSWORD MANGLER")
