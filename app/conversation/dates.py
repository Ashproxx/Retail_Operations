"""Timezone-aware calendar periods. Date ranges are inclusive and bounded."""
import json
import re
from calendar import monthrange
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

CONFIG = Path(__file__).parent / 'config' / 'market_calendar.json'
PERIODS = ['Today', 'Yesterday', 'This week', 'Last week', 'Last 7 days', 'Last 30 days',
           'This month', 'Last month', 'This quarter', 'This year', 'Available data']


def config():
    return json.loads(CONFIG.read_text())


def today(timezone=None, now=None):
    return (now or datetime.now(ZoneInfo(timezone or config()['timezone']))).astimezone(
        ZoneInfo(timezone or config()['timezone'])).date()


def resolve(text, *, now=None, timezone=None, available=None):
    value = text.casefold().replace("today's", 'today')
    current = today(timezone, now)
    explicit = re.findall(r'\b\d{4}-\d{2}-\d{2}\b', value)
    if explicit:
        if len(explicit) > 2:
            raise ValueError('Please give one date or a start and end date.')
        start, end = date.fromisoformat(explicit[0]), date.fromisoformat(explicit[-1])
        label = start.isoformat() if start == end else f'{start} to {end}'
    elif re.search(r'available data|all available|latest available', value):
        if not available:
            raise ValueError('No observed dates are available for this selection.')
        start, end = map(date.fromisoformat, available)
        label = 'Available data'
    elif 'yesterday' in value:
        start = end = current - timedelta(days=1); label = 'Yesterday'
    elif re.search(r'\btoday\b', value):
        start = end = current; label = 'Today'
    elif 'last week' in value:
        end = current - timedelta(days=current.weekday()+1); start = end-timedelta(days=6); label = 'Last week'
    elif 'this week' in value:
        start, end = current-timedelta(days=current.weekday()), current; label = 'This week'
    elif 'last month' in value:
        end = current.replace(day=1)-timedelta(days=1); start = end.replace(day=1); label = 'Last month'
    elif 'this month' in value:
        start, end = current.replace(day=1), current; label = 'This month'
    elif 'this quarter' in value:
        start, end = current.replace(month=((current.month-1)//3)*3+1, day=1), current; label = 'This quarter'
    elif 'this year' in value:
        start, end = current.replace(month=1, day=1), current; label = 'This year'
    elif match := re.search(r'last\s+(\d+)\s+days?', value):
        n = int(match.group(1))
        if not 1 <= n <= 3660: raise ValueError('Choose a period between 1 and 3660 days.')
        start, end = current-timedelta(days=n-1), current; label = f'Last {n} days'
    else:
        return None
    if end < start: raise ValueError('The end date must be on or after the start date.')
    if (end-start).days > 3660: raise ValueError('Choose a date range of at most ten years.')
    return {'start': start.isoformat(), 'end': end.isoformat(), 'label': label,
            'timezone': timezone or config()['timezone']}


def comparison(period):
    start, end = date.fromisoformat(period['start']), date.fromisoformat(period['end'])
    days = (end-start).days+1
    return {'start': (start-timedelta(days=days)).isoformat(), 'end': (start-timedelta(days=1)).isoformat(),
            'label': 'Previous equal-length period', 'timezone': period['timezone']}


def season(day):
    settings = config(); when = date.fromisoformat(day)
    return {'country': settings['country'], 'timezone': settings['timezone'],
            'season': next((s['name'] for s in settings['seasons'] if when.month in s['months']), None),
            'events': [e for e in settings['events'] if e['start'] <= day <= e['end']],
            'limitation': settings['limitation']}
