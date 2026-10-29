"""Read-only answers from frozen evidence and authorized live observations."""
import re
from fastapi import HTTPException
from app.api.schemas import Role

QUESTIONS = (
    'Which forecasting model is most accurate for this store and by how much?',
    "How does tomorrow's rain forecast change expected sales?",
    'Show sales in the last hour compared with the same hour last week.',
    'Is the weather feed fresh, and when did the last sales event arrive?',
    'Which deliveries are most likely to miss their promised date?',
    "Why is this forecast higher than last week's?",
)


def question_index(message):
    text = message.lower().replace('’', "'")
    patterns = (r'forecast.*model.*most accurate', r'rain.*forecast.*sales',
                r'last hour.*same hour last week', r'weather.*fresh.*sales event',
                r'deliveries.*miss.*promised', r'why.*forecast.*higher.*last week')
    return next((i for i, pattern in enumerate(patterns) if re.search(pattern, text)), None)


def answer(api, ctx, index):
    # Permission is checked even for an answer that contains only limitations.
    if ctx.role not in {Role.ADMIN, Role.ANALYST, Role.STORE_MANAGER}:
        raise HTTPException(403, 'This role cannot view retail model results.')
    from app.ml_dashboard.routes import evidence, scoped_report
    try:
        report = scoped_report(evidence(api.state.ml_reports, 'forecast.json'), ctx)
    except (OSError, ValueError, KeyError, TypeError):
        raise HTTPException(503, 'Verified research reports are unavailable.') from None
    model = 'No promoted model'
    source = report['source_label']
    interval = 'Not available for this question; no new prediction is issued.'
    warnings = ['Frozen research results do not establish real-world accuracy.']
    payload = {}
    if index == 0:
        rows = [row for row in report['decisions'] if row.get('horizon') == 28
                and row.get('series', [None])[0] == 'store']
        payload = {'horizon_days': 28, 'store_comparisons': rows}
        summary = ('Choose an authorized store and horizon in Model review to inspect the frozen comparison. '
                   'There is no single most accurate model across stores or horizons. '
                   'Level averages are not this store’s accuracy; test rankings must not be reused for tuning.')
        if len(rows) == 1:
            row = rows[0]
            candidate, baseline = row.get('test_wape'), row.get('baseline_test_wape')
            if isinstance(candidate, (int, float)) and isinstance(baseline, (int, float)):
                model = f"{row['candidate']} versus {row['baseline']}"
                summary = (f"For {row['series'][1]}, frozen 28-day-horizon test WAPE is "
                           f"{100*candidate:.4f}% for {row['candidate']} and {100*baseline:.4f}% "
                           f"for {row['baseline']} (candidate minus baseline: {100*(candidate-baseline):+.4f} "
                           'percentage points; lower is better). This is a recorded comparison, '
                           'not a universal winner or model promotion.')
    elif index == 1:
        summary = ('A rain-driven sales change cannot be estimated: no validated weather-conditioned '
                   'model or time-appropriate forecast-vintage comparison is available. '
                   'Observed weather is context, not a measured causal sales adjustment.')
    elif index in (2, 3):
        model = 'Observed event aggregation; no predictive model'
        interval = 'Not applicable to observed counts; coverage may be incomplete.'
        service = getattr(api.state, 'realtime', None)
        if service is None:
            source = 'No connected real-time event/weather service'
            summary = ('Live evidence is unavailable in this launcher. Historical imported sales and '
                       'the separate seasonal simulation do not establish last-hour coverage or weather freshness.')
        else:
            status = service.status(ctx)
            source = ', '.join(status['source_labels']) or 'No sales-event observations'
            payload = status
            if index == 2:
                features = status['features']
                show = lambda value: 'unknown' if value is None else str(value)
                summary = (f"Last-hour observed units: {show(features['units_1hour'])}; "
                           f"same hour last week: {show(features['units_same_hour_last_week'])}. "
                           'Both windows are bounded by event time and receipt time; missing events are not zero sales.')
            else:
                weather = status['weather']
                source += '; Open-Meteo weather observations (when available)'
                summary = (f"Weather fetch: {weather['fetch_status']}; reading freshness: "
                           f"{weather['reading_freshness']['status']}. Latest authorized sales event: "
                           f"{status['latest_event'] or 'unknown'}. Sales freshness: {status['sales']['status']}.")
            warnings.append('Live status is a request-time snapshot; simulator events remain synthetic.')
    elif index == 4:
        summary = ('No validated per-delivery risk ranking is available. The measured delivery candidates '
                   'did not beat the prevalence baseline on Brier score. Their research evaluation '
                   'does not justify ranking current orders or inventing promised-date risk scores.')
    else:
        summary = ('There is insufficient paired forecast evidence to explain a week-to-week increase. '
                   'The exploratory feature-importance report describes predictive associations on a '
                   'small development window, not causal explanations of this forecast. Choose a '
                   'series and horizon to inspect its dated prediction and uncertainty table.')
    return {'question': QUESTIONS[index], 'status': 'evidence_limited',
            'summary': f'{summary} Model: {model}. Source: {source}. Interval: {interval}',
            'model': model, 'source_label': source, 'interval': interval,
            'warnings': warnings, 'evidence': payload, 'agents': ['model-review'],
            'actions': [], 'operational_write_performed': False}
