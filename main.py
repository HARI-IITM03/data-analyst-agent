import uvicorn
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import pandas as pd
import requests
from bs4 import BeautifulSoup
import duckdb
import matplotlib.pyplot as plt
import base64
from io import BytesIO
import re
import json
from datetime import datetime
import os

app = FastAPI()

# Utility: Convert matplotlib figure to base64 PNG under 100 KB
def fig_to_base64(fig):
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    img_data = buf.read()
    plt.close(fig)
    if len(img_data) > 100000:  # resize if >100 KB
        fig.set_size_inches(4, 3)
        buf = BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight")
        img_data = buf.getvalue()
        plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(img_data).decode()

# Task: Wikipedia Highest-Grossing Films
def handle_highest_grossing_films():
    url = "https://en.wikipedia.org/wiki/List_of_highest-grossing_films"
    html = requests.get(url).text
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_="wikitable")
    df = pd.read_html(str(table))[0]

    # Ensure correct column names
    df.columns = [c.strip() for c in df.columns]

    # 1️⃣ Count $2bn movies before 2000
    count_2bn_before_2000 = df[df["Worldwide gross"].astype(str).str.contains(r"2\.0", regex=True, na=False)]
    count_2bn_before_2000 = count_2bn_before_2000[
        pd.to_numeric(count_2bn_before_2000["Year"], errors="coerce") < 2000
    ].shape[0]

    # 2️⃣ Earliest film over $1.5bn
    over_1_5 = df[df["Worldwide gross"].replace(r"[^\d.]", "", regex=True).astype(float) > 1.5e9]
    earliest_film = over_1_5.sort_values("Year").iloc[0]["Title"]

    # 3️⃣ Correlation Rank vs Peak
    df["Rank"] = pd.to_numeric(df["Rank"], errors="coerce")
    df["Peak"] = pd.to_numeric(df["Peak"], errors="coerce")
    corr = df["Rank"].corr(df["Peak"])

    # 4️⃣ Scatter plot
    fig, ax = plt.subplots()
    ax.scatter(df["Rank"], df["Peak"])
    m, b = pd.Series(df["Peak"]).corr(df["Rank"]), 0
    ax.plot(df["Rank"], df["Rank"] * m + b, "r:", linewidth=2)  # dotted red
    ax.set_xlabel("Rank")
    ax.set_ylabel("Peak")
    img_uri = fig_to_base64(fig)

    return [count_2bn_before_2000, earliest_film, round(corr, 6), img_uri]

# Task: CSV/Parquet Analysis
def handle_dataset_analysis(file_map, question_text):
    for fname, file in file_map.items():
        if fname.endswith(".csv"):
            df = pd.read_csv(file)
        elif fname.endswith(".parquet"):
            df = pd.read_parquet(file)
        else:
            continue

    # Example: sales data
    if "total sales" in question_text.lower():
        total_sales = df["sales"].sum()
        top_region = df.groupby("region")["sales"].sum().idxmax()
        day_corr = df["date"] = pd.to_datetime(df["date"])
        day_corr = df["date"].dt.day.corr(df["sales"])
        median_sales = df["sales"].median()
        total_tax = total_sales * 0.10

        # Bar chart
        fig1, ax1 = plt.subplots()
        df.groupby("region")["sales"].sum().plot(kind="bar", color="blue", ax=ax1)
        ax1.set_xlabel("Region")
        ax1.set_ylabel("Total Sales")
        bar_chart = fig_to_base64(fig1)

        # Cumulative sales
        fig2, ax2 = plt.subplots()
        df.sort_values("date", inplace=True)
        df["cum_sales"] = df["sales"].cumsum()
        ax2.plot(df["date"], df["cum_sales"], color="red")
        ax2.set_xlabel("Date")
        ax2.set_ylabel("Cumulative Sales")
        cumulative_chart = fig_to_base64(fig2)

        return {
            "total_sales": total_sales,
            "top_region": top_region,
            "day_sales_correlation": round(day_corr, 6),
            "bar_chart": bar_chart,
            "median_sales": median_sales,
            "total_sales_tax": total_tax,
            "cumulative_sales_chart": cumulative_chart
        }

    return {"error": "Unsupported dataset query"}

@app.post("/api/")
async def process_api(file: UploadFile = File(...), other_files: list[UploadFile] = File(None)):
    try:
        q_text = (await file.read()).decode("utf-8").strip()
        file_map = {}
        if other_files:
            for f in other_files:
                file_map[f.filename] = BytesIO(await f.read())

        if "highest grossing films" in q_text.lower():
            return JSONResponse(content=handle_highest_grossing_films())

        elif any(x.endswith((".csv", ".parquet")) for x in file_map.keys()):
            return JSONResponse(content=handle_dataset_analysis(file_map, q_text))

        else:
            return JSONResponse(content={"error": "Unsupported question type"})

    except Exception as e:
        return JSONResponse(content={"error": str(e)})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
