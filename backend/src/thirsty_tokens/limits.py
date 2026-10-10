"""Daily spend cap and per-IP rate limit, backed by DynamoDB atomic counters.

Spend uses reserve-then-settle (ADR-0007): the worst-case cost is added to today's counter
in one conditional update, so concurrent requests cannot overshoot the cap. After the call,
`settle_spend` adds the difference between actual and reserved cost.
"""

import hashlib
import math
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from botocore.exceptions import ClientError

MICRO = 1_000_000
_TTL_DAYS = 2  # counters are keyed by UTC day; keep a little longer than a day, then expire


class LimitExceeded(Exception):
    """Base for limit errors; `retry_after` is seconds until the next UTC day."""

    reason = "limit"

    def __init__(self, retry_after: int) -> None:
        super().__init__(self.reason)
        self.retry_after = retry_after


class SpendCapReached(LimitExceeded):
    reason = "daily_budget"


class RateLimited(LimitExceeded):
    reason = "rate_limit"


def usd_to_micro(usd: float, *, round_up: bool = False) -> int:
    micro = usd * MICRO
    return math.ceil(micro) if round_up else round(micro)


def _utcnow() -> datetime:
    return datetime.now(UTC)


class LimitsRepository:
    def __init__(self, table: Any, clock: Callable[[], datetime] = _utcnow) -> None:
        self._table = table
        self._clock = clock

    def _day(self) -> tuple[str, int, int]:
        now = self._clock()
        next_midnight = datetime.combine(now.date() + timedelta(days=1), datetime.min.time(), UTC)
        ttl = int((now + timedelta(days=_TTL_DAYS)).timestamp())
        return now.date().isoformat(), int((next_midnight - now).total_seconds()) + 1, ttl

    def reserve_spend(self, amount_micro: int, cap_micro: int) -> None:
        """Atomically add `amount_micro` to today's spend unless it would pass the cap."""
        day, retry_after, ttl = self._day()
        if amount_micro > cap_micro:
            raise SpendCapReached(retry_after)
        try:
            self._table.update_item(
                Key={"pk": f"SPEND#{day}", "sk": "TOTAL"},
                UpdateExpression="ADD spent_micro :amt SET #ttl = :ttl",
                ConditionExpression="attribute_not_exists(spent_micro) OR spent_micro <= :room",
                ExpressionAttributeNames={"#ttl": "ttl"},
                ExpressionAttributeValues={
                    ":amt": amount_micro,
                    ":room": cap_micro - amount_micro,
                    ":ttl": ttl,
                },
            )
        except ClientError as exc:
            if _is_condition_failure(exc):
                raise SpendCapReached(retry_after) from exc
            raise

    def settle_spend(self, delta_micro: int) -> None:
        """Add `actual - reserved` (negative refunds) to today's spend. Never blocks."""
        if delta_micro == 0:
            return
        day, _, ttl = self._day()
        self._table.update_item(
            Key={"pk": f"SPEND#{day}", "sk": "TOTAL"},
            UpdateExpression="ADD spent_micro :d SET #ttl = :ttl",
            ExpressionAttributeNames={"#ttl": "ttl"},
            ExpressionAttributeValues={":d": delta_micro, ":ttl": ttl},
        )

    def spent_micro(self) -> int:
        day, _, _ = self._day()
        item = self._table.get_item(
            Key={"pk": f"SPEND#{day}", "sk": "TOTAL"}, ConsistentRead=True
        ).get("Item")
        return int(item["spent_micro"]) if item else 0

    def hit_rate_limit(self, ip: str, limit: int) -> None:
        """Count one request for `ip` today; raise RateLimited once `limit` is used up."""
        day, retry_after, ttl = self._day()
        if limit <= 0:
            raise RateLimited(retry_after)
        # Store a truncated hash, not the raw IP.
        ip_hash = hashlib.sha256(ip.encode()).hexdigest()[:16]
        try:
            self._table.update_item(
                Key={"pk": f"RL#{day}", "sk": f"IP#{ip_hash}"},
                UpdateExpression="ADD hits :one SET #ttl = :ttl",
                ConditionExpression="attribute_not_exists(hits) OR hits < :limit",
                ExpressionAttributeNames={"#ttl": "ttl"},
                ExpressionAttributeValues={":one": 1, ":limit": limit, ":ttl": ttl},
            )
        except ClientError as exc:
            if _is_condition_failure(exc):
                raise RateLimited(retry_after) from exc
            raise


def _is_condition_failure(exc: ClientError) -> bool:
    return bool(exc.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException")
