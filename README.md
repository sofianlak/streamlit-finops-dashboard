# FinOps Teams Dashboard

Simple Streamlit dashboard to track monthly cloud spend by team across:
- Azure
- Snowflake
- MongoDB
- Confluent

Current phase uses simulated data.

## Run

```bash
cd /Users/sofian/dev/poc-finops
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Phase 2 (planned)

- Plug a PostgreSQL database as the main data source
- Use an automation-as-code tool to collect costs from each platform
- Format and store data in FinOps FOCUS structure for aligned reporting
