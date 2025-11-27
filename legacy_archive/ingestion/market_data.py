
import sys
import time
import yfinance as yf
from datetime import datetime
import pandas as pd
from pathlib import Path
import structlog
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from core.supabase_client import get_client

load_dotenv()
logger = structlog.get_logger()

class MarketDataIngestion:
    def __init__(self):
        self.db = get_client()
        
    def get_companies(self):
        """Fetch companies with tickers."""
        return self.db.client.table("company").select("id, ticker, name").not_.is_("ticker", "null").execute().data

    def process_company(self, company):
        ticker_symbol = company["ticker"]
        company_id = company["id"]
        
        logger.info(f"Processing {ticker_symbol}...")
        
        try:
            ticker = yf.Ticker(ticker_symbol)
            
            # 1. Get Fundamentals (Snapshot)
            info = ticker.info
            
            # Extract key metrics
            market_cap = info.get("marketCap")
            total_cash = info.get("totalCash")
            total_revenue = info.get("totalRevenue")
            net_income = info.get("netIncomeToCommon")
            
            # Calculate Burn Rate (Estimate)
            # Burn Rate = (Cash Flow from Operations - Capex) / 12? 
            # Or simplified: Net Income / 12 if negative?
            # Let's use Operating Cash Flow if available, else Net Income
            operating_cashflow = info.get("operatingCashflow")
            burn_rate = 0
            
            if operating_cashflow and operating_cashflow < 0:
                burn_rate = abs(operating_cashflow) / 12
            elif net_income and net_income < 0:
                burn_rate = abs(net_income) / 12
                
            # Update Company Table
            update_data = {
                "market_cap": market_cap,
                "cash_balance": total_cash,
                "total_revenue": total_revenue,
                "net_income": net_income,
                "monthly_burn_rate": burn_rate,
                "last_updated_financials": datetime.now().isoformat()
            }
            
            # Add latest price/volume if available
            fast_info = ticker.fast_info
            if fast_info:
                update_data["last_price"] = fast_info.last_price
                update_data["last_volume"] = fast_info.last_volume
            
            self.db.client.table("company").update(update_data).eq("id", company_id).execute()
            logger.info(f"Updated financials for {ticker_symbol}")
            
            # 2. Get Price History (1 Year)
            history = ticker.history(period="1y")
            
            if not history.empty:
                prices = []
                for date, row in history.iterrows():
                    prices.append({
                        "company_id": company_id,
                        "date": date.strftime("%Y-%m-%d"),
                        "open": row["Open"],
                        "high": row["High"],
                        "low": row["Low"],
                        "close": row["Close"],
                        "volume": int(row["Volume"])
                    })
                
                # Batch insert (upsert)
                # Supabase upsert requires unique constraint on (company_id, date)
                try:
                    self.db.client.table("stock_price_history").upsert(prices, on_conflict="company_id, date").execute()
                    logger.info(f"Upserted {len(prices)} price records for {ticker_symbol}")
                except Exception as e:
                    logger.error(f"Failed to insert price history for {ticker_symbol}", error=str(e))
                    
        except Exception as e:
            logger.error(f"Failed to process {ticker_symbol}", error=str(e))

    def run(self):
        companies = self.get_companies()
        logger.info(f"Found {len(companies)} companies to process.")
        
        for i, company in enumerate(companies):
            self.process_company(company)
            time.sleep(1.0) # Be nice to Yahoo

if __name__ == "__main__":
    ingestion = MarketDataIngestion()
    ingestion.run()
