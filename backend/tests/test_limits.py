from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from typing import Any

import boto3
import pytest
from moto import mock_aws

from thirsty_tokens.limits import (
    LimitsRepository,
    RateLimited,
    SpendCapReached,
    usd_to_micro,
)


@pytest.fixture
def table() -> Iterator[Any]:
    with mock_aws():
        ddb = boto3.resource("dynamodb", region_name="eu-north-1")
        t = ddb.create_table(
            TableName="t",
            KeySchema=[
                {"AttributeName": "pk", "KeyType": "HASH"},
                {"AttributeName": "sk", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "pk", "AttributeType": "S"},
                {"AttributeName": "sk", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        yield t


def _clock(iso: str) -> Any:
    now = {"v": datetime.fromisoformat(iso).replace(tzinfo=UTC)}
    fn = lambda: now["v"]  # noqa: E731
    fn.now = now  # type: ignore[attr-defined]
    return fn


def test_usd_to_micro_rounding() -> None:
    assert usd_to_micro(0.0000016) == 2
    assert usd_to_micro(0.0000011, round_up=True) == 2
    assert usd_to_micro(2.0) == 2_000_000


def test_reserve_under_at_and_over_cap(table: Any) -> None:
    repo = LimitsRepository(table)
    repo.reserve_spend(400, cap_micro=1000)
    repo.reserve_spend(600, cap_micro=1000)  # exactly at the cap is allowed
    assert repo.spent_micro() == 1000
    with pytest.raises(SpendCapReached) as err:
        repo.reserve_spend(1, cap_micro=1000)
    assert err.value.retry_after > 0
    assert repo.spent_micro() == 1000  # rejected reservation changes nothing


def test_single_reservation_larger_than_cap_rejected(table: Any) -> None:
    with pytest.raises(SpendCapReached):
        LimitsRepository(table).reserve_spend(2000, cap_micro=1000)


def test_settle_refunds_difference(table: Any) -> None:
    repo = LimitsRepository(table)
    repo.reserve_spend(800, cap_micro=1000)
    repo.settle_spend(-700)  # actual was 100
    assert repo.spent_micro() == 100
    repo.reserve_spend(800, cap_micro=1000)  # room again


def test_settle_zero_is_noop_and_can_create_nothing(table: Any) -> None:
    repo = LimitsRepository(table)
    repo.settle_spend(0)
    assert repo.spent_micro() == 0


def test_concurrent_reservations_never_exceed_cap(table: Any) -> None:
    repo = LimitsRepository(table)

    def attempt(_: int) -> bool:
        try:
            repo.reserve_spend(100, cap_micro=1000)
        except SpendCapReached:
            return False
        return True

    with ThreadPoolExecutor(max_workers=16) as pool:
        results = list(pool.map(attempt, range(40)))
    assert sum(results) == 10
    assert repo.spent_micro() == 1000


def test_day_rollover_resets_spend_and_rate(table: Any) -> None:
    clock = _clock("2026-10-09T23:59:00")
    repo = LimitsRepository(table, clock)
    repo.reserve_spend(1000, cap_micro=1000)
    repo.hit_rate_limit("1.2.3.4", limit=1)
    with pytest.raises(SpendCapReached) as err:
        repo.reserve_spend(1, cap_micro=1000)
    assert err.value.retry_after == 61  # 60s to midnight, +1
    clock.now["v"] = datetime(2026, 10, 10, 0, 0, 1, tzinfo=UTC)
    repo.reserve_spend(1000, cap_micro=1000)
    repo.hit_rate_limit("1.2.3.4", limit=1)


def test_rate_limit_allows_n_then_blocks_per_ip(table: Any) -> None:
    repo = LimitsRepository(table)
    for _ in range(3):
        repo.hit_rate_limit("1.2.3.4", limit=3)
    with pytest.raises(RateLimited):
        repo.hit_rate_limit("1.2.3.4", limit=3)
    repo.hit_rate_limit("5.6.7.8", limit=3)  # other IPs unaffected


def test_items_have_ttl_and_no_raw_ip(table: Any) -> None:
    repo = LimitsRepository(table, _clock("2026-10-09T12:00:00"))
    repo.reserve_spend(10, cap_micro=1000)
    repo.hit_rate_limit("1.2.3.4", limit=3)
    items = table.scan()["Items"]
    assert len(items) == 2
    assert all(int(i["ttl"]) > int(datetime(2026, 10, 10, tzinfo=UTC).timestamp()) for i in items)
    assert "1.2.3.4" not in str(items)


def test_rate_limit_of_zero_blocks_first_request(table: Any) -> None:
    with pytest.raises(RateLimited):
        LimitsRepository(table).hit_rate_limit("1.2.3.4", limit=0)
