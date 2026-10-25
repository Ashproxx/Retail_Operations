const assert = require('node:assert/strict');
const { datedPoints } = require('../../app/ml_dashboard/static/chart-data.js');
const utc = date => Date.parse(date + 'T00:00:00Z');

assert.deepEqual(datedPoints(['2026-08-05', '2026-09-02'], [164, 179]), [
  [utc('2026-08-05'), 164], [utc('2026-08-06'), null], [utc('2026-09-02'), 179]
]);
assert.deepEqual(datedPoints(['2026-08-05', '2026-08-06'], [0, 2]), [
  [utc('2026-08-05'), 0], [utc('2026-08-06'), 2]
]);
assert.equal(datedPoints(['2026-08-05'], [])[0][1], null);
assert.equal(datedPoints(['2026-08-05'], [NaN])[0][1], null);
assert.deepEqual(datedPoints([], []), []);
assert.throws(() => datedPoints(['2026-08-05', '2026-08-05'], [1, 2]));
assert.throws(() => datedPoints(['invalid'], [1]));
console.log('PASS: separated windows break lines, genuine zeros survive, missing values remain null.');
