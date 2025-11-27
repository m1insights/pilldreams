
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.supabase_client import get_client

def render(company):
    """
    Render Finance tab for a company.
    
    Args:
        company: Company dictionary from database
    """
    db = get_client()
    company_id = company['id']
    ticker = company['ticker']
    
    st.markdown(f"### {ticker} Financial Intelligence")
    
    # 1. Cash Runway Analysis
    st.subheader("Cash Runway")
    
    cash = company.get('cash_balance') or 0
    burn = company.get('monthly_burn_rate') or 0
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.metric("Cash on Hand", f"${cash/1e6:.1f}M")
        st.metric("Est. Monthly Burn", f"${burn/1e6:.1f}M" if burn else "N/A")
        
    with col2:
        if burn > 0:
            runway_months = cash / burn
            
            # Gauge Chart
            fig = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = runway_months,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Runway (Months)"},
                delta = {'reference': 12, 'increasing': {'color': "green"}},
                gauge = {
                    'axis': {'range': [None, 36], 'tickwidth': 1, 'tickcolor': "white"},
                    'bar': {'color': "white"},
                    'bgcolor': "rgba(0,0,0,0)",
                    'borderwidth': 2,
                    'bordercolor': "gray",
                    'steps': [
                        {'range': [0, 6], 'color': 'rgba(255, 0, 0, 0.3)'},
                        {'range': [6, 12], 'color': 'rgba(255, 165, 0, 0.3)'},
                        {'range': [12, 36], 'color': 'rgba(0, 255, 0, 0.3)'}],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 6}}))
            
            fig.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig, use_container_width=True)
            
            if runway_months < 6:
                st.error("⚠️ CRITICAL: Less than 6 months of cash remaining.")
            elif runway_months < 12:
                st.warning("⚠️ WARNING: Less than 12 months of cash remaining.")
        else:
            st.info("Insufficient data to calculate burn rate (Positive Cash Flow or Missing Data).")

    st.markdown("---")

    # 2. Catalyst Chart
    st.subheader("Price Action & Catalysts")
    
    # Fetch Price History
    history = db.client.table("stock_price_history").select("*").eq("company_id", company_id).order("date").execute().data
    
    if not history:
        st.info("No price history available.")
        return

    df = pd.DataFrame(history)
    df['date'] = pd.to_datetime(df['date'])
    
    # Fetch Trials (Catalysts)
    trials = db.client.table("trial").select("nct_id, title, phase, completion_date").eq("sponsor_company_id", company_id).execute().data
    
    # Create Chart
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.03, subplot_titles=(f'{ticker} Price', 'Volume'), 
                        row_width=[0.2, 0.7])

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df['date'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='Price'
    ), row=1, col=1)

    # Volume
    fig.add_trace(go.Bar(x=df['date'], y=df['volume'], name='Volume', marker_color='rgba(100, 100, 100, 0.5)'), row=2, col=1)

    # Add Catalysts (Vertical Lines)
    for trial in trials:
        date_str = trial.get('completion_date')
        if date_str:
            try:
                date = pd.to_datetime(date_str)
                # Only show if within range
                if date >= df['date'].min() and date <= df['date'].max():
                    fig.add_vline(x=date, line_width=1, line_dash="dash", line_color="cyan")
                    fig.add_annotation(x=date, y=df['high'].max(), text=f"Phase {trial['phase']}", 
                                       showarrow=True, arrowhead=1, ax=0, ay=-40, bordercolor="#c7c7c7")
            except:
                pass

    fig.update_layout(
        xaxis_rangeslider_visible=False,
        height=600,
        template="plotly_dark",
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
