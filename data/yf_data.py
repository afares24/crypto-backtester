import yfinance as yf
from pydantic import BaseModel
from util.log import logger
from models.model import StockData

def stock_history(
        symbol: str, 
        period: str, 
        interval: str, 
        start: str | None = None, 
        end: str | None = None,
    ) -> list[StockData]:
    
    if period and (start or end):
        raise ValueError(f"Period, start or end params were passed in. Either pass a period or start and end range.")
    
    try:
        ticker = yf.Ticker(symbol)
        history = ticker.history(
            period = period, 
            interval = interval,
            start = start,
            end = end,
            )
        if history.empty:
            raise ValueError(f"No history data returned for {symbol}.")
        
        history.reset_index(inplace=True) # makes date a column
        return history
    
    except Exception:
        logger.exception(f"There was an error fetching {symbol} data from yf.")
