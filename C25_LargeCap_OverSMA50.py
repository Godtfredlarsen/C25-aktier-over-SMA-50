import yfinance as yf
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

print("Agent starter...")

# ✅ Yahoo tickers
aktier = [
    "ALMB.CO","BAVA.CO","CARL-B.CO","COLO-B.CO","DANSKE.CO","DEMANT.CO",
    "DSV.CO","FLS.CO","GMAB.CO","GN.CO","ISS.CO",
    "MAERSK-A.CO","MAERSK-B.CO","NKT.CO","NOVO-B.CO",
    "NSIS-B.CO","ORSTED.CO","PNDORA.CO","RBREW.CO","ROCK-B.CO",
    "ALSYDB.CO","TRYG.CO","VWS.CO","ZEAL.CO",
    "ALK-B.CO","DFDS.CO","HAFNI.OL","MATAS.CO","NETC.CO",
    "RILBA.CO","STG.CO","TRMD-A.CO"
]

over_ema100 = []

print("Analyserer...")

# ✅ RSI funktion
def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# ✅ LOOP
for aktie in aktier:
    try:
        ticker = yf.Ticker(aktie)
        data = ticker.history(period="1y")

        if data.empty or len(data) < 100:
            print("Ingen data:", aktie)
            continue

        # ✅ EMA100
        data['EMA100'] = data['Close'].ewm(span=100, adjust=False).mean()

        # ✅ RSI
        data['RSI'] = calculate_rsi(data)

        # ✅ MACD
        ema12 = data['Close'].ewm(span=12, adjust=False).mean()
        ema26 = data['Close'].ewm(span=26, adjust=False).mean()
        data['MACD'] = ema12 - ema26
        data['Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()

        last = data.tail(1)

        close_now = last['Close'].iloc[0]
        ema100_now = last['EMA100'].iloc[0]
        rsi_now = last['RSI'].iloc[0]
        macd_now = last['MACD'].iloc[0]
        signal_now = last['Signal'].iloc[0]

        if pd.isna(rsi_now):
            continue

        navn = aktie.replace(".CO", "").replace(".OL", "")

        # ✅ RSI status
        if rsi_now < 30:
            rsi_status = "Oversolgt"
        elif rsi_now > 70:
            rsi_status = "Overkøbt"
        else:
            rsi_status = "Neutral"

        # ✅ MACD status
        if macd_now > signal_now:
            macd_status = "Bullish"
        else:
            macd_status = "Bearish"

        # ✅ FILTER (EMA100)
        if close_now > ema100_now:
            over_ema100.append(
                f"{navn:<12} {round(close_now,1):>8} DKK   RSI: {rsi_status:<10}   MACD: {macd_status}"
            )

    except Exception as e:
        print("Fejl ved", aktie, ":", e)

# ✅ EMAIL OPSÆTNING
MIN_EMAIL = "mgl@godtfredlarsen.com"
PASSWORD = os.environ.get("EMAIL_PASSWORD")

msg = MIMEMultipart()
msg['From'] = MIN_EMAIL
msg['To'] = MIN_EMAIL
msg['Subject'] = "📊 DK EMA100 Status (Yahoo)"

# ✅ HTML
if over_ema100:
    html = "<h3>Aktier OVER EMA100</h3><pre>"
    for a in over_ema100:
        html += a + "\n"
    html += "</pre>"
else:
    html = "<p>Ingen aktier er over EMA100.</p>"

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
