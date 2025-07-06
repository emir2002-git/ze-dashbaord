# Z&E AutoAccountant Dashboard

## Overview
This Streamlit app provides micro-businesses with automated accounting and business suggestions. It tracks daily POS revenue, computes historical averages, and generates actionable recommendations.

## Real-Time Functionality
- **Auto-refresh** every 60 seconds via `st_autorefresh`.
- Pulls data from `firms_complex.csv` and `pos_complex.csv` in the repo root.

## How to Deploy
1. Clone this repository to your local machine or directly on GitHub.
2. Ensure the following files are in the repo root:
   - `app.py`
   - `firms_complex.csv`
   - `pos_complex.csv`
   - `requirements.txt`
3. Push to your GitHub repository.
4. On Streamlit Cloud:
   - Connect to your GitHub repo.
   - Set main file to `app.py`.
   - Deploy.
5. Access the live dashboard link provided by Streamlit.

## Monetization & Packages
Offer the service with tiered pricing:
- **Lite (20 KM/month)**: Basic dashboard & manual CSV uploads.
- **Smart (50 KM/month)**: Auto-updating via GitHub.
- **Pro (80 KM/month)**: Adds smart rule-based suggestions & PDF reports.

## Reports
- Generates a combined table showing daily vs. average revenue.
- Displays system-generated recommendations.
- Export the dashboard view to PDF using browser print for reports.

## Next Steps
- Add expense tracking and invoice generation.
- Integrate Google Sheets or POS API for live data.
- Expand to AI-driven suggestions once API quota is managed.
