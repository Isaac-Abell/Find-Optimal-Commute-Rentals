# Commute Rental Listings Pipeline

A serverless data pipeline for scraping, processing, and serving rental listings with commute-based filtering.

This project scrapes real estate listings, stores them in AWS S3, updates a SQL database via Lambda, and exposes the data via an API for a front-end UI.

---

## ⚠️ Important Note

The **scraper must be run locally**, not in AWS. Requests from AWS IP ranges are blocked by the data source. AWS credentials must be set as environment variables locally.

---

## Features

* **Data Scraping (Local) — `scraping`**

  * Designed to run locally because AWS IP addresses are blocked by the data source.
  * Collects recent rental listings from multiple cities.
  * Cleans and normalizes data (fills missing fields, removes incomplete entries).
  * Stores processed data in an S3 bucket for downstream processing.

* **Automated Database Updates (AWS Lambda) — `update_db`**

  * Triggered automatically whenever the S3 CSV is updated.
  * Reads the CSV and updates the SQL database in AWS.

* **API (AWS Lambda) — `lambda`**

  * Accepts POST requests with filtering options (e.g., price, beds, distance).
  * Returns filtered rental listings in JSON format for a front-end UI.

---

## Architecture Overview

```
Scraper (Local: scrape.py) → S3 (CSV) → Lambda Trigger (update_db.py) → SQL Database → API Lambda (lambda_api.py) → Front-end UI
```

---

## Technologies Used

* **Python** (pandas, boto3)
* **AWS S3, Lambda, RDS/SQL**
* **REST API** for data access
* **GitHub Actions** for automated workflow (optional CI/CD)