'use strict';

function datedPoints(dates, values) {
  const points = [];
  const day = 86400000;
  let previous = null;
  dates.forEach((date, index) => {
    const timestamp = Date.parse(date + 'T00:00:00Z');
    if (!Number.isFinite(timestamp) || previous !== null && timestamp <= previous) {
      throw new Error('Chart dates must be valid and strictly increasing.');
    }
    // A null breaks the line; an unscored day is never a zero or a prediction.
    if (previous !== null && timestamp - previous > day) {
      points.push([previous + day, null]);
    }
    points.push([timestamp, Number.isFinite(values[index]) ? values[index] : null]);
    previous = timestamp;
  });
  return points;
}

if (typeof module !== 'undefined') module.exports = { datedPoints };
