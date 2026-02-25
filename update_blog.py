#!/usr/bin/env python3
"""Fetch BLS retail food price data and write blog cards directly into blog.html."""

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
BLOG_PATH = "/Users/mitchellgoldberger/tgfc-website/blog.html"


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


def build_blog_cards():
    prices = fetch_bls_prices()
    now = datetime.now().strftime("%B %Y")
    week_of = datetime.now().strftime("%B %d, %Y")

    # Trend for box 2
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
          <div class="blog-card-img">
            <img src="images/usda-market-news.png" alt="USDA Market News">
          </div>
          <div class="blog-card-body">
            <div class="blog-meta">{now} &bull; Industry</div>
            <h3>USDA Market Outlook &mdash; {now}</h3>
            <p>{trend}</p>
            <div class="blog-updated">Updated: {week_of}</div>
          </div>
        </div>
        <div class="blog-card">
          <div class="blog-card-img">
            <img src="https://images.unsplash.com/photo-1560179707-f14e90ef3623?w=700&h=400&fit=crop" alt="Company news">
          </div>
          <div class="blog-card-body">
            <div class="blog-meta">January 2026 &bull; Company News</div>
            <h3>New Co-Packing Partnership Announced</h3>
            <p>We're excited to announce a new partnership expanding our proprietary product capabilities.</p>
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

    print(f"Updated {BLOG_PATH}")
    print(f"  Box 1: Retail Grocery Report — {now}")
    print(f"  Box 2: USDA Market Outlook — {now}")
    print(f"  Box 3: Company News")


if __name__ == "__main__":
    build_blog_cards()
