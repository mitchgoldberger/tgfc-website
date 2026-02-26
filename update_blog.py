#!/usr/bin/env python3
"""Fetch BLS retail food price data and write blog cards directly into blog.html."""

import json
import os
import re
import requests
from datetime import datetime

SERIES = {
    "APU0000FF1101": "Eggs (Grade A, Large), per dozen",
    "APU0000FC1101": "Chicken (whole), per lb",
    "APU0000FD2101": "Ground Beef (100%), per lb",
    "APU0000FJ1101": "Bacon (sliced), per lb",
    "APU0000FL2101": "Milk (whole), per gallon",
    "APU0000FD3101": "Ground Chuck (100%), per lb",
}

BLS_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BLOG_PATH = os.path.join(SCRIPT_DIR, "blog.html")
JSON_PATH = os.path.join(SCRIPT_DIR, "blog-data.json")


def fetch_bls_prices():
    payload = {
        "seriesid": list(SERIES.keys()),
        "startyear": str(datetime.now().year - 1),
        "endyear": str(datetime.now().year),
    }
    resp = requests.post(BLS_URL, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if data.get("status") != "REQUEST_SUCCEEDED":
        print(f"BLS API error: {data.get('message', 'Unknown error')}")
        return None

    prices = []
    for series in data["Results"]["series"]:
        sid = series["seriesID"]
        name = SERIES.get(sid, sid)
        if series["data"]:
            latest = series["data"][0]
            prev = series["data"][1] if len(series["data"]) > 1 else None
            price = float(latest["value"])
            change = None
            if prev:
                change = round(price - float(prev["value"]), 2)
            prices.append({"item": name, "price": price, "change": change})
    return prices


def build_price_table(prices):
    rows = ""
    for p in prices:
        arrow = ""
        cls = ""
        if p["change"] is not None and p["change"] != 0:
            arrow = "&#9650;" if p["change"] > 0 else "&#9660;"
            cls = "up" if p["change"] > 0 else "down"
            arrow += f" ${abs(p['change']):.2f}"
        rows += f'              <tr><td>{p["item"]}</td><td>${p["price"]:.2f}</td><td class="{cls}">{arrow}</td></tr>\n'

    return f"""            <table class="price-table">
              <tr><th>Item</th><th>Price</th><th>Change</th></tr>
{rows}            </table>"""


def update_json(prices, now, week_of):
    ups = sum(1 for p in prices if p["change"] and p["change"] > 0)
    downs = sum(1 for p in prices if p["change"] and p["change"] < 0)
    if ups > downs:
        trend = "Prices trending upward across most protein categories."
    elif downs > ups:
        trend = "Prices easing across several key categories."
    else:
        trend = "Mixed signals across protein and dairy categories."

    summary_parts = []
    for p in prices[:4]:
        arrow = "\u25b2" if p["change"] and p["change"] > 0 else "\u25bc"
        summary_parts.append(f'{p["item"]}: ${p["price"]:.2f} {arrow} ${abs(p["change"] or 0):.2f}')

    json_data = [
        {
            "id": 1,
            "title": f"Retail Grocery Report \u2014 {now}",
            "meta": f"{now} \u2022 Market Data",
            "summary": " | ".join(summary_parts),
            "image": "https://images.unsplash.com/photo-1604719312566-8912e9227c6a?w=700&h=400&fit=crop",
            "prices": [
                {"item": p["item"], "price": f'${p["price"]:.2f}', "month": now, "change": p["change"]}
                for p in prices
            ],
            "updated": week_of,
        },
        {
            "id": 2,
            "title": f"USDA Market Outlook \u2014 {now}",
            "meta": f"{now} \u2022 Industry",
            "summary": trend,
            "image": "images/usda-market-news.png",
            "updated": week_of,
        },
        {
            "id": 3,
            "title": "New Co-Packing Partnership with St. Croix Meats",
            "meta": "January 2026 \u2022 Company News",
            "summary": "TGFC is proud to announce a new co-packing partnership with St. Croix Meats.",
            "image": "images/stcroix-logo.png",
            "updated": "January 15, 2026",
        },
    ]

    with open(JSON_PATH, "w") as f:
        json.dump(json_data, f, indent=2)


def build_blog_cards():
    prices = fetch_bls_prices()
    now = datetime.now().strftime("%B %Y")
    week_of = datetime.now().strftime("%B %d, %Y")

    # Trend text for Box 2
    if prices:
        ups = sum(1 for p in prices if p["change"] and p["change"] > 0)
        downs = sum(1 for p in prices if p["change"] and p["change"] < 0)
        if ups > downs:
            trend = "Prices trending upward across most protein categories this month. Beef and eggs lead increases while dairy shows some relief."
        elif downs > ups:
            trend = "Prices easing across several key categories. Buyers may find favorable conditions in dairy and ground beef."
        else:
            trend = "Mixed signals across protein and dairy categories. Some items rising while others pull back."
    else:
        trend = "Check back for updated market analysis."

    price_table = build_price_table(prices) if prices else "<p>Data temporarily unavailable.</p>"

    cards = f"""        <div class="blog-card">
          <div class="blog-card-img">
            <img src="https://images.unsplash.com/photo-1604719312566-8912e9227c6a?w=700&h=400&fit=crop" alt="Retail grocery report">
          </div>
          <div class="blog-card-body">
            <div class="blog-meta">{now} &bull; Market Data</div>
            <h3>Retail Grocery Report &mdash; {now}</h3>
            <p>Latest average U.S. retail prices from the Bureau of Labor Statistics.</p>
{price_table}
            <div class="blog-updated">Updated: {week_of}</div>
          </div>
        </div>
        <div class="blog-card">
          <div class="blog-card-img usda-logo-bg">
            <img src="images/usda-market-news.png" alt="USDA Market News">
          </div>
          <div class="blog-card-body">
            <div class="blog-meta">{now} &bull; Industry</div>
            <h3>USDA Market Outlook &mdash; {now}</h3>
            <p>{trend}</p>
            <div class="report-links">
              <h4>National Weekly Retail Activity Reports</h4>
              <a href="https://www.ams.usda.gov/mnreports/ams_3228.pdf" target="_blank" class="report-link">Beef (pdf)</a>
              <a href="https://www.ams.usda.gov/mnreports/ams_2756.pdf" target="_blank" class="report-link">Chicken (pdf)</a>
              <a href="https://www.ams.usda.gov/mnreports/dybretail.pdf" target="_blank" class="report-link">Dairy (pdf)</a>
              <a href="https://www.ams.usda.gov/mnreports/ams_2757.pdf" target="_blank" class="report-link">Eggs (pdf)</a>
              <a href="https://www.ams.usda.gov/mnreports/ams_2868.pdf" target="_blank" class="report-link">Pork (pdf)</a>
              <a href="https://www.ams.usda.gov/mnreports/ams_2867.pdf" target="_blank" class="report-link">Turkey (pdf)</a>
            </div>
            <div class="blog-updated">Updated: {week_of}</div>
          </div>
        </div>
        <div class="blog-card">
          <div class="blog-card-img stcroix-logo-bg">
            <img src="images/stcroix-logo.png" alt="St. Croix Meats">
          </div>
          <div class="blog-card-body">
            <div class="blog-meta">January 2026 &bull; Company News</div>
            <h3>New Co-Packing Partnership with St. Croix Meats</h3>
            <p>TGFC is proud to announce a new co-packing partnership with St. Croix Meats, a trusted meat processing partner with decades of industry experience. SCM offers premium quality products and flexible solutions across food service, institutional, government, and military sectors. This partnership expands our proprietary product capabilities with custom grinding, portioning, slicing, and dicing services.</p>
            <div class="blog-updated">Updated: January 15, 2026</div>
          </div>
        </div>"""

    # Read blog.html and replace the blog-grid contents
    with open(BLOG_PATH, "r") as f:
        html = f.read()

    pattern = r'(<div class="blog-grid"[^>]*>).*?(</div>\s*</div>\s*</section>)'
    replacement = rf'\1\n{cards}\n      \2'
    new_html = re.sub(pattern, replacement, html, flags=re.DOTALL)

    with open(BLOG_PATH, "w") as f:
        f.write(new_html)

    # Update JSON snapshot
    if prices:
        update_json(prices, now, week_of)

    print(f"Updated {BLOG_PATH}")
    print(f"  Box 1: Retail Grocery Report — {now}")
    print(f"  Box 2: USDA Market Outlook — {now}")
    print(f"  Box 3: St. Croix Meats Partnership")


if __name__ == "__main__":
    build_blog_cards()
