
import sys
from pathlib import Path
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from core.supabase_client import get_client
from app.tabs import finance

def test_finance_render():
    db = get_client()
    
    # 1. Get a company with data
    print("Fetching company...")
    company = db.client.table("company").select("*").eq("ticker", "ROIV").single().execute().data
    
    if not company:
        print("Company ROIV not found")
        return

    print(f"Testing render for {company['ticker']}...")
    
    # 2. Test Logic (mimic render function)
    company_id = company['id']
    
    # Fetch Price History
    history = db.client.table("stock_price_history").select("*").eq("company_id", company_id).order("date").execute().data
    print(f"Fetched {len(history)} price records")
    
    if not history:
        print("No history found")
        return

    df = pd.DataFrame(history)
    df['date'] = pd.to_datetime(df['date'])
    
    # Fetch Trials
    trials = db.client.table("trial").select("nct_id, title, phase, completion_date").eq("sponsor_company_id", company_id).execute().data
    print(f"Fetched {len(trials)} trials")
    
    # Create Chart
    try:
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True)
        fig.add_trace(go.Candlestick(x=df['date'], open=df['open'], high=df['high'], low=df['low'], close=df['close']), row=1, col=1)
        print("Chart created successfully")
    except Exception as e:
        print(f"Chart creation failed: {e}")

if __name__ == "__main__":
    test_finance_render()
