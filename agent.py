import yfinance as yf
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

c25_aktier = [
    "ALK-B.CO", "AMBU-B.CO", "CARL-B.CO", "COLO-B.CO", "DNORD.CO", "DEMANT.CO", 
    "DSV.CO", "FLS.CO", "GMAB.CO", "GN.CO", "ISS.CO", "JYSK.CO", "MAERSK-A.CO", 
    "MAERSK-B.CO", "NDA-DK.CO", "NOVO-B.CO", "NZYM-B.CO", "ORSTED.CO", "PNDORA.CO", 
    "ROCK-B.CO", "RY.CO", "TRYG.CO", "VWS.CO", "ZEAL.CO"
]

fundne_aktier = []

print("Agenten analyserer C25 indekset for seneste gennembrud...")

for aktie in c25_aktier:
    try:
        ticker = yf.Ticker(aktie)
        data = ticker.history(period="100d")
        
        if data.empty or len(data) < 55:
            continue
            
        data['SMA50'] = data['Close'].rolling(window=50).mean()
        
        for i in range(-1, 0):
            if len(data) + (i-1) < 0:
                continue
                
            forrige_luk = data['Close'].iloc[i-1]
            forrige_sma = data['SMA50'].iloc[i-1]
            aktuel_luk = data['Close'].iloc[i]
            aktuel_sma = data['SMA50'].iloc[i]
            
            if pd.isna(forrige_luk) or pd.isna(forrige_sma) or pd.isna(aktuel_luk) or pd.isna(aktuel_sma):
                continue
            
            if forrige_luk < forrige_sma and aktuel_luk > aktuel_sma:
                dato_str = data.index[i].strftime('%d-%m-%Y')
                fundne_aktier.append({
                    "navn": aktie.replace(".CO", ""), 
                    "kurs": round(aktuel_luk, 2), 
                    "sma": round(aktuel_sma, 2),
                    "dato": dato_str
                })
                break 
    except Exception as e:
        print(f"Fejl ved behandling af {aktie}: {e}")

# TILPASSET TIL MGL@GODTFREDLARSEN.COM (ONE.COM)
MIN_EMAIL = "mgl@godtfredlarsen.com"
PASSWORD = os.environ.get("GMAIL_PASSWORD") 
SMTP_SERVER = "send.one.com"  # Tilbage til One.com serveren

msg = MIMEMultipart()
msg['From'] = MIN_EMAIL
msg['To'] = MIN_EMAIL
msg['Subject'] = "📊 C25 Agent: Daglig SMA 50 Rapport"

if fundne_aktier:
    html = f"<h3>Daglig Aktie Rapport for mgl@godtfredlarsen.com</h3>"
    html += "<p>Følgende aktie(r) lukkede <b>op over</b> SMA 50 på seneste handelsdag:</p>"
    html += "<table border='1' cellpadding='5' style='border-collapse: collapse;'>"
    html += "<tr style='background-color: #eee;'><th>Aktie</th><th>Lukkeskurs</th><th>SMA 50</th><th>Dato</th></tr>"
    for aktie in fundne_aktier:
        html += f"<tr><td><b>{aktie['navn']}</b></td><td>{aktie['kurs']} DKK</td><td>{aktie['sma']} DKK</td><td>{aktie['dato']}</td></tr>"
    html += "</table><br><p>Mvh,<br>Din automatiske C25 AI-Agent 🤖</p>"
else:
    html = f"<h3>Daglig Aktie Rapport</h3><p>Ingen nye C25-aktier brød over SMA 50 på seneste tilgængelige handelsdag.</p>"

msg.attach(MIMEText(html, 'html'))

if PASSWORD:
    try:
        server = smtplib.SMTP(SMTP_SERVER, 587)
        server.starttls()
        server.login(MIN_EMAIL, PASSWORD)
        server.sendmail(MIN_EMAIL, MIN_EMAIL, msg.as_string())
        server.quit()
        print("Daglig mail sendt til mgl@godtfredlarsen.com med succes!")
    except Exception as e:
        print(f"Kunne ikke sende mail via One.com SMTP: {e}")
else:
    print("Fejl: Password blev ikke fundet i GitHub Secrets.")
