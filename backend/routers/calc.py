"""Cost-of-Capital / WACC calculator endpoint."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.db import db
from core.security import get_current_user

router = APIRouter(prefix="/calculator", tags=["calculator"])


class DebtTranche(BaseModel):
    name: str
    amount: float
    rate: float


class CalcIn(BaseModel):
    equity_amount: float
    cost_of_equity: float
    tax_rate: float = 25.17
    debt: List[DebtTranche]
    reit_symbol: Optional[str] = None
    spread_over_reit: float = 4.0


@router.post("/wacc")
async def compute_wacc(payload: CalcIn, user: dict = Depends(get_current_user)):
    total_debt = sum(t.amount for t in payload.debt)
    weighted_kd = sum(t.amount * t.rate for t in payload.debt) / total_debt if total_debt > 0 else 0.0
    total_capital = total_debt + payload.equity_amount
    if total_capital <= 0:
        raise HTTPException(status_code=400, detail="Capital must be positive")

    we = payload.equity_amount / total_capital
    wd = total_debt / total_capital
    after_tax_kd = weighted_kd * (1 - payload.tax_rate / 100.0)

    ke_from_reit = None
    if payload.reit_symbol:
        reit = await db.reits.find_one({"symbol": payload.reit_symbol})
        if reit:
            ke_from_reit = reit["dividend_yield"] + payload.spread_over_reit
    ke = ke_from_reit if ke_from_reit is not None else payload.cost_of_equity

    wacc = we * ke + wd * after_tax_kd
    return {
        "weights": {"equity": we, "debt": wd},
        "weighted_cost_of_debt": weighted_kd,
        "after_tax_cost_of_debt": after_tax_kd,
        "cost_of_equity": ke,
        "cost_of_equity_source": "reit" if ke_from_reit is not None else "manual",
        "wacc": wacc,
        "discount_rate": wacc,
        "total_capital_inr_cr": total_capital,
    }
