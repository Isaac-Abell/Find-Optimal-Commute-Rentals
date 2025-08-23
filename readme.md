# Commute Rental Listings Pipeline

A serverless data pipeline for scraping, processing, and serving rental listings with commute-based filtering. This project scrapes real estate listings, stores them in AWS S3, updates a SQL database via Lambda, and exposes the data via an API for a front-end UI.

---

## ⚠️ Important Note

* The **scraper must be run locally**, not in AWS. Requests from AWS IP ranges are blocked by the data source.
* AWS credentials must be set as environment variables locally.
* **Currently supported cities:**

  ```python
  "San Francisco Bay Area, CA": (37.7749, -122.4194),
  "New York, NY": (40.7128, -74.0060),
  "Seattle, WA": (47.6062, -122.3321),
  "Austin, TX": (30.2672, -97.7431),
  "Boston, MA": (42.3601, -71.0589),
  "Denver, CO": (39.7392, -104.9903),
  "Los Angeles, CA": (34.0522, -118.2437)
  ```

  Expansion to additional cities is easy, but for now we keep it limited to avoid an unnecessarily huge database.

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

## Architecture Overview

```text
Scraper (Local: scrape) → S3 (CSV) → Lambda Trigger (update_db) → SQL Database → API Lambda (lambda) → Front-end UI
```

---

## Technologies Used

* **Python** (pandas, boto3)
* **AWS S3, Lambda, RDS/SQL**
* **REST API** for data access
* **GitHub Actions** for automated workflow (optional CI/CD)

---
