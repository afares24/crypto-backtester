from pydantic import BaseModel
from datetime import datetime

class StockData(BaseModel):
    open: float
    high: float
    low: float
    close: float
    volume: float
    date: datetime