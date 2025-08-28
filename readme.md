# Commute Rental Listings Pipeline

A serverless data pipeline for scraping, processing, and serving rental listings with commute-based filtering. This project scrapes real estate listings, stores them in AWS S3, updates a SQL database via Lambda, and exposes the data via an API for a front-end UI.

[See full website here](https://isaac-abell.github.io/find-commute-rentals-fe/)

---

## ⚠️ Important Note

* The **scraper must be run locally or via a proxy**, not with cloud providers. Requests from cloud IP ranges are blocked by the data source.
* AWS credentials must be set as environment variables locally if you are updating the database.

## Supported Regions

* **Bay Area, CA** (San Francisco Bay Area, CA)
* **New York City Metro Area, NY** (New York, NY)
* **Seattle Metropolitan Area, WA** (Seattle, WA)
* **Austin Metropolitan Area, TX** (Austin, TX)
* **Greater Boston Area, MA** (Boston, MA)
* **Denver Metropolitan Area, CO** (Denver, CO)
* **Greater Los Angeles Area, CA** (Los Angeles, CA)
* **Miami, FL** (Miami, FL)
* **Chicago, IL** (Chicago, IL)
* **Washington, D.C.** (Washington, D.C.)
* **Phoenix, AZ** (Phoenix, AZ)
* **Philadelphia, PA** (Philadelphia, PA)
* **Atlanta, GA** (Atlanta, GA)
* **Salt Lake City, UT** (Salt Lake City, UT)

Expansion to additional cities is easy, but for now we limit the set to avoid an unnecessarily huge database.

---

## Features

* **Data Scraping (Local) — `scraping`**

  * Designed to run locally because AWS IP addresses are blocked by the data source.
  * Collects recent rental listings from the supported cities.
  * Cleans and normalizes data (fills missing fields, removes incomplete entries).
  * Stores processed data in an S3 bucket for downstream processing.

* **Automated Database Updates (AWS Lambda) — `update_db`**

  * Triggered automatically whenever the S3 CSV is updated.
  * Reads the CSV and updates the SQL database in AWS.

* **API (AWS Lambda) — `lambda`**

  * Accepts POST requests with filtering options (e.g., price, beds, distance).
  * Returns filtered rental listings in JSON format for a front-end UI.

---

## Running the Scraper Locally

1. **Set up a Python environment** (recommended: `venv` or `conda`):

```bash
python -m venv venv
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate         # Windows
```

2. **Install dependencies**:

```bash
pip install -e .
```

3. **Set required environment variables** (at minimum):

```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=your_region
```

*(Windows PowerShell syntax: `setx VAR_NAME "value"` or `set VAR_NAME=value` in the session.)*

4. **Run the scraper**:

```bash
python -m scraping.scrape_to_s3
```

* This will fetch listings, normalize the data, and upload it to the configured S3 bucket.
* The script supports **asynchronous requests**, so it fetches data concurrently for multiple cities to speed up scraping.

---

## Architecture Overview

```text
Scraper (Local: scrape) → S3 (CSV) → Lambda Trigger (update_db) → SQL Database → API Lambda (lambda) → Front-end UI
```

---

## Technologies Used

* **Python** (pandas, aiohttp, googlemaps, boto3)
* **AWS S3, Lambda, RDS/SQL**
* **REST API** for data access
* **GitHub Actions** for automated workflow (optional CI/CD)