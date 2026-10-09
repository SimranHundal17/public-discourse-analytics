import requests
import pandas as pd

indicators = {
    "health": "SH.XPD.CHEX.GD.ZS",
    "education": "SE.XPD.TOTL.GD.ZS",
    "defense": "MS.MIL.XPND.GD.ZS",
    "co2": "EN.ATM.CO2E.PC"
}

all_data = []

for topic, code in indicators.items():
    url = f"https://api.worldbank.org/v2/country/all/indicator/{code}?format=json&per_page=20000"
    
    response = requests.get(url)
    
    try:
        json_data = response.json()
        
        if len(json_data) < 2:
            continue
        
        data = json_data[1]
        
        for item in data:
            if item["value"] is not None:
                all_data.append({
                    "country": item["country"]["value"],
                    "year": int(item["date"]),
                    "topic": topic,
                    "value": item["value"]
                })
    
    except:
        continue

df = pd.DataFrame(all_data)

df = df[df["year"] >= 2020]

df = df.sort_values(by=["country", "year"])

df.to_csv("institutional_api_topics.csv", index=False)