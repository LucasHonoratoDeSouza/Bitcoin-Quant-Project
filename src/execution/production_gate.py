from __future__ import annotations

import json
import logging
from pathlib import Path

from src.utils.project_paths import SIGNALS_DIR


LOGGER = logging.getLogger(__name__)

DEFAULT_MODEL = "production_legacy_cooldown1"
GATE_FILE_PATH = SIGNALS_DIR / "production_gate.json"

SUPPORTED_MODELS = {
    "production_legacy_cooldown1": {
        "scorer_mode": "legacy",
        "manager": "portfolio",
        "cooldown_days": 1,
    },
    "legacy_cooldown3_baseline": {
        "scorer_mode": "legacy",
        "manager": "portfolio",
        "cooldown_days": 3,
    },
    "legacy_confidence_research": {
        "scorer_mode": "legacy",
        "manager": "confidence",
        "cooldown_days": 1,
    },
    "advanced_adaptive_research": {
        "scorer_mode": "advanced",
        "manager": "advanced",
        "cooldown_days": 1,
    },
}


def load_gate_payload(gate_file: Path | None = None) -> dict:
    target = Path(gate_file) if gate_file else GATE_FILE_PATH
    if not target.exists():
        return {}

    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        LOGGER.warning("Unable to read production gate file %s: %s", target, exc)
        return {}

    if not isinstance(payload, dict):
        LOGGER.warning("Invalid production gate payload in %s (expected object).", target)
        return {}

    return payload


def resolve_live_model(gate_file: Path | None = None) -> dict:
    payload = load_gate_payload(gate_file)
    selected_model = payload.get("selected_model", DEFAULT_MODEL)
    source = "objective_gate" if payload else "default_fallback"

    if selected_model not in SUPPORTED_MODELS:
        LOGGER.warning(
            "Gate selected unsupported model '%s'; falling back to %s.",
            selected_model,
            DEFAULT_MODEL,
        )
        selected_model = DEFAULT_MODEL
        source = "default_fallback"

    return {
        "model": selected_model,
        "config": SUPPORTED_MODELS[selected_model],
        "source": source,
        "payload": payload,
    }


def build_live_components(
    min_trade_usd: float = 20.0,
    gate_file: Path | None = None,
) -> dict:
    from src.execution.advanced_portfolio_manager import AdvancedPortfolioManager
    from src.execution.confidence_portfolio_manager import ConfidencePortfolioManager
    from src.execution.portfolio_manager import PortfolioManager
    from src.strategy.score import QuantScorer

    resolved = resolve_live_model(gate_file)
    model = resolved["model"]
    config = resolved["config"]

    scorer = QuantScorer(mode=config["scorer_mode"])

    manager_name = config["manager"]
    cooldown_days = config["cooldown_days"]

    if manager_name == "portfolio":
        manager = PortfolioManager(min_trade_usd=min_trade_usd, cooldown_days=cooldown_days)
    elif manager_name == "confidence":
        manager = ConfidencePortfolioManager(min_trade_usd=min_trade_usd, cooldown_days=cooldown_days)
    elif manager_name == "advanced":
        manager = AdvancedPortfolioManager(min_trade_usd=min_trade_usd, cooldown_days=cooldown_days)
    else:
        LOGGER.warning("Unknown manager '%s'; using default portfolio manager.", manager_name)
        manager = PortfolioManager(min_trade_usd=min_trade_usd, cooldown_days=1)

    return {
        "model": model,
        "source": resolved["source"],
        "gate_payload": resolved["payload"],
        "scorer": scorer,
        "manager": manager,
    }
