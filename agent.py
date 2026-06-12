import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import requests

print("Agent starter...")

# ✅ Aktieliste
aktier = [
"ALMB","BAVA","CARL B","COLO B","DANSKE","DEMANT","DSV","FLS",
"GENMAB","GN","ISS","JYSK","MAERSK A","MAERSK B","NKT",
"NOVO B","NOVOZ","ORSTED","PNDORA","RBREW","ROCK B","SYDB",
"TRYG","VWS","ZEAL","ALK B","BIOPOR","BO","CHEMM","DFDS",
"GREENM","HAFNI","MATAS","NETC","RING","SPNO","STG","TOP","TORM"
]

over_ema50 = []

print("Analyserer...")

# ✅ RSI funktion
def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# ✅ Nordnet scraping (FIXET)
def hent_data(navn):
    try:
        url = f"https://www.nordnet.dk/api/2/main_search?query={navn}"
        r = requests.get(url)
        if r.status_code != 200:
            return None

        data = r.json()

        if "results" not in data or not data["results"]:
            return None

        # ✅ Vælg KUN danske aktier (XCSE)
        instrument = None
        for res in data["results"]:
            if res.get("type") == "INSTRUMENT" and res.get("exchange") == "XCSE":
                instrument = res
                break

        if instrument is None:
            return None

        instrument_id = instrument["id"]

        hist_url = f"https://www.nordnet.dk/api/2/ins/price/chart/{instrument_id}?resolution=day&from=0&to=9999999999"
        r2 = requests.get(hist_url)
        if r2.status_code != 200:
            return None

        hist = r2.json()

        if "candles" not in hist:
            return None

        df = pd.DataFrame(hist["candles"])
        df.columns = ["timestamp", "Open", "High", "Low", "Close", "Volume"]

        return df

    except:
        return None

# ✅ LOOP
for aktie in aktier:
    try:
        data = hent_data(aktie)

        if data is None or data.empty or len(data) < 100:
            continue

        # ✅ EMA
        data['EMA50'] = data['Close'].ewm(span=50, adjust=False).mean()

        # ✅ RSI
        data['RSI'] = calculate_rsi(data)

        # ✅ MACD
        ema12 = data['Close'].ewm(span=12, adjust=False).mean()
        ema26 = data['Close'].ewm(span=26, adjust=False).mean()
        data['MACD'] = ema12 - ema26
        data['Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()

        last = data.tail(1)

        close_now = last['Close'].iloc[0]
        ema50_now = last['EMA50'].iloc[0]
        rsi_now = last['RSI'].iloc[0]
        macd_now = last['MACD'].iloc[0]
        signal_now = last['Signal'].iloc[0]

        if pd.isna(rsi_now):
            continue

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

        # ✅ FILTER
        if close_now > ema50_now:
            over_ema50.append(
                f"{aktie:<12} {round(close_now,1):>8}   RSI: {rsi_status:<10}   MACD: {macd_status}"
            )

    except Exception as e:
        print(f"Fejl ved {aktie}: {e}")

# ✅ EMAIL
MIN_EMAIL = "mgl@godtfredlarsen.com"
PASSWORD = os.environ.get("EMAIL_PASSWORD")

msg = MIMEMultipart()
msg['From'] = MIN_EMAIL
msg['To'] = MIN_EMAIL
msg['Subject'] = "📊 DK EMA50 Status (Nordnet)"

# ✅ HTML output
if over_ema50:
    html = "<h3>Aktier OVER EMA50</h3><pre>"
    for a in over_ema50:
        html += a + "\n"
    html += "</pre>"
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
