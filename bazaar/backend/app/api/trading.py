"""Trading endpoints — account, positions, and orders via the PyPSX SDK.

All routes require valid PyPSX credentials in .env. When the client is not
connected they return HTTP 503 rather than silently faking data, because a
fake order confirmation is far worse than an error.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Literal, Optional

from ..core.config import settings
from ..data.market_feed import pypsx_feed

router = APIRouter(prefix="/api/trading", tags=["Trading"])


class OrderRequest(BaseModel):
    symbol: str = Field(..., description="PSX ticker symbol, e.g. ENGRO")
    side: Literal["buy", "sell"]
    qty: int = Field(..., gt=0, description="Number of shares")
    order_type: Literal["market", "limit", "stop", "stop_limit"] = "market"
    limit_price: Optional[float] = Field(None, gt=0)
    stop_price: Optional[float] = Field(None, gt=0)


def _require_client():
    if not pypsx_feed.is_connected:
        raise HTTPException(
            status_code=503,
            detail="PyPSX trading client not connected. Check PYPSX_API_KEY_ID "
                   "and PYPSX_API_SECRET_KEY in your .env file.",
        )


@router.get("/status")
async def trading_status():
    return {
        "connected": pypsx_feed.is_connected,
        "paper_mode": pypsx_feed.paper,
        "live_trading_allowed": settings.ALLOW_LIVE_TRADING,
    }


@router.get("/account")
async def get_account():
    _require_client()
    account = pypsx_feed.get_account()
    if not account:
        raise HTTPException(status_code=502, detail="Could not fetch account from PyPSX")
    return account


@router.get("/portfolio")
async def get_portfolio():
    _require_client()
    return pypsx_feed.get_portfolio()


@router.get("/positions")
async def get_positions():
    _require_client()
    return {"positions": pypsx_feed.get_positions()}


@router.get("/orders")
async def get_orders(status: Optional[str] = Query(None, description="Filter by order status")):
    _require_client()
    orders = pypsx_feed.get_orders()
    if status:
        orders = [o for o in orders if str(o.get("status", "")).lower() == status.lower()]
    return {"orders": orders, "count": len(orders)}


@router.post("/orders")
async def submit_order(order: OrderRequest):
    _require_client()

    # Safety gate: real-money orders need an explicit opt-in.
    if not pypsx_feed.paper and not settings.ALLOW_LIVE_TRADING:
        raise HTTPException(
            status_code=403,
            detail="Live trading is disabled. Set PYPSX_PAPER=True for paper "
                   "trading, or ALLOW_LIVE_TRADING=True to trade real money.",
        )

    if order.order_type in ("limit", "stop_limit") and order.limit_price is None:
        raise HTTPException(status_code=422, detail="limit_price is required for this order type")
    if order.order_type in ("stop", "stop_limit") and order.stop_price is None:
        raise HTTPException(status_code=422, detail="stop_price is required for this order type")

    result = pypsx_feed.submit_order(
        symbol=order.symbol,
        side=order.side,
        qty=order.qty,
        order_type=order.order_type,
        limit_price=order.limit_price,
        stop_price=order.stop_price,
    )
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message", "Order rejected"))
    return result


@router.delete("/orders/{order_id}")
async def cancel_order(order_id: str):
    _require_client()
    result = pypsx_feed.cancel_order(order_id)
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message", "Cancel failed"))
    return result
