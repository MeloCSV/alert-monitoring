'use strict';

// The experimental `@angular/build:unit-test` builder (vitest runner) has no
// built-in coverage threshold gate (unlike the old karma builder's
// coverageIstanbulReporter.thresholds). This mirrors the backend's
// `--cov-fail-under=80` (see alert-monitoring-back-web-api/pyproject.toml)
// by reading the json-summary report `ng test --code-coverage` produces.

const fs = require('fs');
const path = require('path');

const THRESHOLD = 80;
const METRICS = ['lines', 'statements', 'functions', 'branches'];
const summaryPath = path.join(__dirname, '..', 'coverage', 'coverage-summary.json');

if (!fs.existsSync(summaryPath)) {
  console.error(
    `Coverage summary not found at ${summaryPath}. Run "npm run test:coverage" first.`
  );
  process.exit(1);
}

const { total } = JSON.parse(fs.readFileSync(summaryPath, 'utf8'));

let failed = false;
for (const metric of METRICS) {
  const pct = total[metric].pct;
  const status = pct >= THRESHOLD ? 'OK  ' : 'FAIL';
  console.log(`[${status}] ${metric}: ${pct}% (threshold: ${THRESHOLD}%)`);
  if (pct < THRESHOLD) failed = true;
}

if (failed) {
  console.error(`\nCoverage is below the ${THRESHOLD}% threshold.`);
  process.exit(1);
}

console.log(`\nAll coverage metrics are at or above ${THRESHOLD}%.`);
