from __future__ import annotations

from datetime import datetime
from typing import Optional

from src.execution.portfolio_manager import Order, PortfolioManager


class ConfidencePortfolioManager(PortfolioManager):
    """
    Yield-oriented allocator with uncertainty penalty.

    It starts from the same target allocation map used by PortfolioManager and
    scales rebalance aggressiveness by a confidence score derived from LT/MT
    magnitude and agreement. This keeps upside participation while reducing
    noisy reallocations in unstable regimes.
    """

    def __init__(
        self,
        min_trade_usd: float = 20.0,
        cooldown_days: int = 1,
        max_leverage: float = 2.0,
    ):
        super().__init__(min_trade_usd=min_trade_usd, cooldown_days=cooldown_days)
        self.max_leverage = max_leverage

    def _clip(self, value: float, low: float, high: float) -> float:
        return max(low, min(high, value))

    def _signal_confidence(self, lt_score: float, mt_score: float) -> float:
        lt_strength = self._clip(abs(lt_score) / 100.0, 0.0, 1.0)
        mt_strength = self._clip(abs(mt_score) / 100.0, 0.0, 1.0)
        agreement = 1.0 - self._clip(abs(lt_score - mt_score) / 200.0, 0.0, 1.0)
        same_direction = 1.0 if (lt_score * mt_score) >= 0 else 0.75

        confidence = ((0.45 * lt_strength) + (0.35 * mt_strength) + (0.20 * agreement)) * same_direction
        return self._clip(confidence, 0.10, 1.0)

    def _adjust_target(
        self,
        target_allocation: float,
        current_allocation: float,
        lt_score: float,
        mt_score: float,
        confidence: float,
    ) -> float:
        delta = target_allocation - current_allocation
        dynamic_max_leverage = 1.0 + ((self.max_leverage - 1.0) * confidence)

        # Keep full downside defense regardless of confidence.
        if lt_score < -60:
            return 0.0

        # Preserve upside when both horizons strongly agree (yield objective).
        if lt_score > 75 and mt_score > 50:
            return self._clip(max(target_allocation, current_allocation), 0.0, dynamic_max_leverage)

        if delta >= 0:
            aggressiveness = 0.50 + (0.85 * confidence)
        else:
            aggressiveness = 0.65 + (0.65 * confidence)

        adjusted = current_allocation + (delta * aggressiveness)
        return self._clip(adjusted, 0.0, dynamic_max_leverage)

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
        lt_score = float(scores["long_term"]["value"])
        mt_score = float(scores["medium_term"]["value"])

        raw_target = self._get_target_allocation(lt_score, mt_score, current_allocation)
        confidence = self._signal_confidence(lt_score, mt_score)
        target_allocation = self._adjust_target(
            raw_target,
            current_allocation,
            lt_score,
            mt_score,
            confidence,
        )

        target_btc_value = net_equity * target_allocation
        diff_usd = target_btc_value - current_btc_value

        # In high-confidence setups, reduce threshold to capture trends earlier.
        threshold_ratio = 0.025 - (0.012 * confidence)
        dynamic_threshold = max(self.min_trade_usd, net_equity * threshold_ratio)
        if abs(diff_usd) < dynamic_threshold:
            return None

        reason = f"{self._get_reason(lt_score, mt_score)} | Confidence {confidence:.2f}"
        is_urgent = (
            (lt_score > 75 and mt_score > 50)
            or (lt_score > 40 and mt_score > 0)
            or (lt_score < -60)
        )

        if not is_urgent and last_trade_date and current_date:
            if isinstance(last_trade_date, str):
                last_trade_date = datetime.strptime(last_trade_date.split(" ")[0], "%Y-%m-%d")
            if isinstance(current_date, str):
                current_date = datetime.strptime(current_date.split(" ")[0], "%Y-%m-%d")

            effective_cooldown = max(0, int(round(self.cooldown_days * (1.15 - confidence))))
            days_since = (current_date - last_trade_date).days
            if days_since < effective_cooldown:
                return None

        if diff_usd > 0:
            return Order(side="BUY", amount_usd=diff_usd, reason=reason)

        amount = min(abs(diff_usd), current_btc_value)
        if amount < dynamic_threshold:
            return None
        return Order(side="SELL", amount_usd=amount, reason=reason)
