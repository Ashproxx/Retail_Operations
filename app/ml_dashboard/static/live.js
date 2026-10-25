'use strict';
let stopLive = () => {};

function parseSales(text) {
  const events = [];
  for (const block of text.replaceAll('\r\n', '\n').split('\n\n')) {
    const lines = block.split('\n');
    if (lines.includes('event: authentication-required')) throw new Error('Access token expired or invalid.');
    const payload = lines.filter(line => line.startsWith('data:')).map(line => line.slice(5).trim()).join('\n');
    if (payload) events.push(JSON.parse(payload));
  }
  return events;
}

function startLive(token, unauthorized) {
  stopLive();
  let stopped = false, timer, cursor = 0, rows = [];
  const controller = new AbortController();
  stopLive = () => { stopped = true; token = ''; rows = []; clearTimeout(timer); controller.abort(); };
  async function get(url) {
    const response = await fetch(url, {headers: {Authorization: 'Bearer ' + token}, cache: 'no-store', signal: controller.signal});
    if (response.status === 401 || response.status === 403) {
      if (!stopped) unauthorized();
      throw new Error('Authentication required.');
    }
    if (!response.ok) throw new Error('Live feed unavailable; reconnecting. Previously displayed observations may be stale.');
    return response;
  }
  async function poll() {
    try {
      const status = await (await get('/api/realtime/status')).json();
      if (stopped) return;
      const text = await (await get('/api/stream/sales?once=true&after=' + cursor)).text();
      if (stopped) return;
      if (text.includes('event: authentication-required')) { unauthorized(); return; }
      const batch = parseSales(text);
      for (const row of batch) {
        if (row.id > cursor) { rows.push(row); cursor = row.id; }
      }
      rows = rows.slice(-20);
      $('live').textContent = 'Feed: ' + status.mode + ' · Sales freshness: ' + status.sales.status +
        ' · Sources: ' + (status.source_labels.join(', ') || 'no observations') +
        ' · Checked ' + new Date().toLocaleTimeString() + '. Frozen research results are unchanged.';
      cards('live-metrics', [['Units / 15 minutes', number(status.features.units_15min)],
        ['Units / hour', number(status.features.units_1hour)], ['Feed state', status.mode === 'off' ? 'Disabled' : status.task_status]]);
      $('weather').textContent = 'Weather: ' + status.weather.fetch_status + ' · Reading freshness: ' +
        status.weather.reading_freshness.status + '. ' + (status.weather.values ?
          number(status.weather.values.temperature_2m) + ' °C · ' + number(status.weather.values.precipitation) + ' mm precipitation · ' + status.weather.values.observed_at :
          'No weather observation available.');
      table('live-events', ['Store', 'Units', 'Occurred (UTC)', 'Source', 'Synthetic'],
        rows.map(row => [row.store_id, row.quantity, row.occurred_at, row.source, row.synthetic ? 'Yes' : 'No']));
    } catch (error) {
      if (!stopped) $('live').textContent = error.name === 'TypeError' ? 'Connection lost; reconnecting. Displayed observations may be stale.' : error.message;
    } finally {
      if (!stopped) timer = setTimeout(poll, 5000);
    }
  }
  poll();
}
if (typeof module !== 'undefined') module.exports = {parseSales};
