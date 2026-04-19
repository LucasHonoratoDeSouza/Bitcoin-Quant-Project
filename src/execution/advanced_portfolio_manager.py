from __future__ import annotations

from datetime import datetime
from typing import Optional

from src.execution.portfolio_manager import Order


class AdvancedPortfolioManager:
    """
    Continuous position sizing manager.

    Uses score-derived edge and confidence to produce a smooth target allocation,
    reducing regime-whipsaw and excessive all-in/all-out behavior.
    """

    def __init__(
        self,
        min_trade_usd: float = 20.0,
        cooldown_days: int = 1,
        base_allocation: float = 0.25,
        edge_gain: float = 1.15,
        max_leverage: float = 1.5,
    ):
        self.min_trade_usd = min_trade_usd
        self.cooldown_days = cooldown_days
        self.base_allocation = base_allocation
        self.edge_gain = edge_gain
        self.max_leverage = max_leverage

    def _clip(self, value, low, high):
        return max(low, min(high, value))

    def _normalize_score(self, score):
        return self._clip(score / 100.0, -1.0, 1.0)

    def _cooldown_active(self, last_trade_date, current_date):
        if not (last_trade_date and current_date):
            return False

        if isinstance(last_trade_date, str):
            last_trade_date = datetime.strptime(last_trade_date.split(" ")[0], "%Y-%m-%d")
        if isinstance(current_date, str):
            current_date = datetime.strptime(current_date.split(" ")[0], "%Y-%m-%d")

        return (current_date - last_trade_date).days < self.cooldown_days

    def _target_allocation(self, lt_score, mt_score, current_allocation):
        lt = self._normalize_score(lt_score)
        mt = self._normalize_score(mt_score)

        edge = (0.65 * lt) + (0.35 * mt)
        disagreement = abs(lt - mt)
        confidence = self._clip(1.0 - (0.5 * disagreement), 0.20, 1.0)

        kelly_like = edge * confidence * self.edge_gain
        target = self.base_allocation + kelly_like

        if lt > 0.55 and mt > 0.35:
            target += 0.20
        if lt < -0.55:
            target *= 0.35
        if lt < -0.80:
            target = 0.0
        if mt < -0.70:
            target = min(target, 0.20)

        if target < current_allocation and lt > 0.25 and mt > 0.25:
            # Avoid premature profit-taking in sustained bull regimes.
            target = max(target, current_allocation - 0.10)

        return self._clip(target, 0.0, self.max_leverage), edge, confidence

    def calculate_order(
        self,
        scores: dict,
        current_cash: float,
        current_btc_value: float,
        current_debt: float = 0.0,
        last_trade_date=None,
        current_date=None,
    ) -> Optional[Order]:
        total_assets = current_cash + current_btc_value
        net_equity = total_assets - current_debt

        if net_equity <= 0:
            return None

        current_allocation = current_btc_value / net_equity
        lt_score = scores["long_term"]["value"]
        mt_score = scores["medium_term"]["value"]

        target_allocation, edge, confidence = self._target_allocation(
            lt_score,
            mt_score,
            current_allocation,
        )

        target_btc_value = net_equity * target_allocation
        diff_usd = target_btc_value - current_btc_value

        dynamic_threshold = max(self.min_trade_usd, net_equity * 0.01)
        if abs(diff_usd) < dynamic_threshold:
            return None

        urgent = (abs(edge) > 0.70) or (lt_score < -80) or (lt_score > 80 and mt_score > 55)
        if not urgent and self._cooldown_active(last_trade_date, current_date):
            return None

        reason = (
            f"Adaptive Allocation edge={edge:+.2f} confidence={confidence:.2f} "
            f"target={target_allocation:.2f}"
        )

        if diff_usd > 0:
            return Order(side="BUY", amount_usd=diff_usd, reason=reason)

        amount = min(abs(diff_usd), current_btc_value)
        if amount < dynamic_threshold:
            return None
        return Order(side="SELL", amount_usd=amount, reason=reason)
