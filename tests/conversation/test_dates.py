from datetime import datetime, timezone
import pytest
from app.conversation.dates import resolve, season

NOW = datetime(2026, 9, 27, 20, 0, tzinfo=timezone.utc)


def test_market_midnight_and_week_boundaries():
    assert resolve('today', now=NOW)['start'] == '2026-09-28'
    assert resolve('last week', now=NOW)['start'] == '2026-09-21'
    assert resolve('last week', now=NOW)['end'] == '2026-09-27'
    assert resolve('last month', now=NOW)['end'] == '2026-08-31'
    assert resolve('this quarter', now=NOW)['start'] == '2026-07-01'
    assert resolve('last 7 days', now=NOW)['start'] == '2026-09-22'


def test_ranges_are_explicit_and_calendar_does_not_invent_events():
    assert resolve('2026-02-01 to 2026-02-28')['end'] == '2026-02-28'
    with pytest.raises(ValueError): resolve('2026-02-30')
    with pytest.raises(ValueError): resolve('2026-09-30 to 2026-09-01')
    assert season('2026-09-28')['events'] == []
    assert resolve('available data', available=('2025-01-01','2025-01-31'))['end'] == '2025-01-31'
