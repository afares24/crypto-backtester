from fastapi import APIRouter, Query, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from data.yf_data import stock_history
from pathlib import Path

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))

@router.get("/history", response_class=HTMLResponse)
def get_stock_hist(
    request: Request,
    symbol: str = Query(..., description="symbol of stock"),
    period: str | None = Query(None),
    interval: str = Query("1d"),
    start: str | None = Query(None),
    end: str | None = Query(None),
):
    if period and (start or end):
        return templates.TemplateResponse("partials/error_fragment.html", {
            "request": request,
            "message": "If 'Period' is selected, 'Start Date' and 'End Date' must be empty."
        })

    try:
        data = stock_history(symbol, period, interval, start, end)
        return templates.TemplateResponse("partials/history_fragment.html", {
            "request": request,
            "data": data,
            "symbol": symbol
        })
    except Exception as e:
        return templates.TemplateResponse("partials/error_fragment.html", {
            "request": request,
            "message": str(e)
        })