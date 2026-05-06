#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const repoRoot = path.resolve(__dirname, '..');
const productDir = path.join(repoRoot, 'data', 'product');
const RESULT_HEADERS = ['Source', 'Date', 'Pass %', 'Fail %', 'Passed', 'Failed', 'Errors', 'Skipped', 'Total', 'Duration'];

function label(source) {
  return source.replace(/-/g, ' ').toUpperCase();
}

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

function jsonFiles(dir) {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir)
    .filter(f => f.endsWith('.json'))
    .sort()
    .map(f => path.join(dir, f));
}

function latestFile(dir) {
  return jsonFiles(dir).at(-1) || null;
}

function previousFile(file) {
  const files = jsonFiles(path.dirname(file));
  const index = files.indexOf(file);
  return index > 0 ? files[index - 1] : null;
}

function duration(summary) {
  const seconds = summary?.duration_seconds;
  return typeof seconds === 'number' ? `${seconds.toFixed(1)}s` : '-';
}

function passPercent(summary) {
  if (summary?.overall_coverage != null) return `${summary.overall_coverage}%`;
  const total = summary?.total;
  const passed = summary?.passed;
  if (typeof total !== 'number' || total <= 0 || typeof passed !== 'number') return '';
  return `${((passed / total) * 100).toFixed(1)}%`;
}

function failPercent(summary) {
  if (summary?.overall_coverage != null) return `${(100 - summary.overall_coverage).toFixed(1)}%`;
  const total = summary?.total;
  if (typeof total !== 'number' || total <= 0) return '';
  const failures = (summary?.failed || 0) + (summary?.errors || 0);
  return `${((failures / total) * 100).toFixed(1)}%`;
}

function resultKey(entry) {
  return [entry.module || '', entry.suite || '', entry.name || ''].join('::');
}

function failingEntries(data) {
  return (data.entries || []).filter(entry => entry.status === 'failed' || entry.status === 'error');
}

function failureLabel(entry) {
  const suite = entry.suite ? `${entry.suite} / ` : '';
  const module = entry.module ? `${entry.module} / ` : '';
  return `${module}${suite}${entry.name || 'unknown'} (${entry.status})`;
}

function compareFailures(currentData, previousData) {
  if (!previousData) return { newFailures: [], fixedFailures: [] };
  const current = new Map(failingEntries(currentData).map(entry => [resultKey(entry), entry]));
  const previous = new Map(failingEntries(previousData).map(entry => [resultKey(entry), entry]));
  const newFailures = [...current.entries()]
    .filter(([key]) => !previous.has(key))
    .map(([, entry]) => failureLabel(entry))
    .sort();
  const fixedFailures = [...previous.entries()]
    .filter(([key]) => !current.has(key))
    .map(([, entry]) => failureLabel(entry))
    .sort();
  return { newFailures, fixedFailures };
}

function changedMetric(currentSummary, previousSummary, key) {
  if (!previousSummary) return '';
  const current = currentSummary?.[key];
  const previous = previousSummary?.[key];
  if (typeof current !== 'number' || typeof previous !== 'number') return '';
  const delta = current - previous;
  if (!delta) return '';
  return `${delta > 0 ? '+' : ''}${delta}`;
}

function sourceResult(source, file) {
  const data = readJson(file);
  const previous = previousFile(file);
  const previousData = previous ? readJson(previous) : null;
  const summary = data.summary || {};
  const previousSummary = previousData?.summary || null;
  return {
    source,
    file,
    date: path.basename(file, '.json'),
    data,
    previousData,
    row: summaryRow(source, file, data),
    deltas: {
      passed: changedMetric(summary, previousSummary, 'passed'),
      failed: changedMetric(summary, previousSummary, 'failed'),
      errors: changedMetric(summary, previousSummary, 'errors'),
      skipped: changedMetric(summary, previousSummary, 'skipped'),
      total: changedMetric(summary, previousSummary, 'total'),
      coverage: changedMetric(summary, previousSummary, 'overall_coverage'),
    },
    failures: compareFailures(data, previousData),
  };
}

function summaryRow(source, file, data = readJson(file)) {
  const summary = data.summary || {};
  const date = path.basename(file, '.json');
  if (summary.overall_coverage != null) {
    return [label(source), date, passPercent(summary), failPercent(summary), '-', '-', '-', String(summary.total_endpoints || 0), duration(summary)];
  }
  return [
    label(source),
    date,
    passPercent(summary),
    failPercent(summary),
    String(summary.passed ?? ''),
    String(summary.failed ?? ''),
    String(summary.errors ?? ''),
    String(summary.skipped ?? ''),
    String(summary.total ?? ''),
    duration(summary),
  ];
}

function table(headers, rows) {
  const sep = headers.map(() => '---');
  return [headers, sep, ...rows]
    .map(row => `| ${row.map(cell => String(cell ?? '').replace(/\|/g, '\\|')).join(' | ')} |`)
    .join('\n');
}

function productResults() {
  if (!fs.existsSync(productDir)) return [];
  return fs.readdirSync(productDir, { withFileTypes: true })
    .filter(entry => entry.isDirectory())
    .map(entry => [entry.name, latestFile(path.join(productDir, entry.name))])
    .filter(([, file]) => file)
    .map(([source, file]) => sourceResult(source, file))
    .sort((a, b) => label(a.source).localeCompare(label(b.source)));
}

function changedDataFiles() {
  const before = process.env.GITHUB_EVENT_BEFORE || process.env.GITHUB_BEFORE || '';
  const sha = process.env.GITHUB_SHA || 'HEAD';
  let output = '';
  try {
    if (before && !/^0+$/.test(before)) {
      output = execSync(`git diff --name-only ${before} ${sha}`, { cwd: repoRoot, encoding: 'utf8' });
    } else {
      output = execSync(`git diff-tree --no-commit-id --name-only -r ${sha}`, { cwd: repoRoot, encoding: 'utf8' });
    }
  } catch (err) {
    output = '';
  }
  return output.split('\n')
    .filter(Boolean)
    .filter(name => /^data\/product\/[^/]+\/[^/]+\.json$/.test(name))
    .filter(name => fs.existsSync(path.join(repoRoot, name)));
}

function changedResults() {
  return changedDataFiles().map(name => {
    const parts = name.split('/');
    return sourceResult(parts[2], path.join(repoRoot, name));
  }).sort((a, b) => label(a.source).localeCompare(label(b.source)));
}

function deltaText(result) {
  const parts = [];
  if (result.deltas.coverage) parts.push(`coverage ${result.deltas.coverage} pts`);
  if (result.deltas.passed) parts.push(`passed ${result.deltas.passed}`);
  if (result.deltas.failed) parts.push(`failed ${result.deltas.failed}`);
  if (result.deltas.errors) parts.push(`errors ${result.deltas.errors}`);
  if (result.deltas.skipped) parts.push(`skipped ${result.deltas.skipped}`);
  if (result.deltas.total) parts.push(`total ${result.deltas.total}`);
  return parts.join(', ') || '-';
}

function comparisonRows(results) {
  return results.map(result => [
    label(result.source),
    result.date,
    deltaText(result),
    String(result.failures.newFailures.length),
    String(result.failures.fixedFailures.length),
  ]);
}

function listLines(title, items) {
  if (!items.length) return [`${title}: none`];
  const shown = items.slice(0, 10).map(item => `- ${item}`);
  if (items.length > shown.length) shown.push(`- ...and ${items.length - shown.length} more`);
  return [`${title}:`, ...shown];
}

function failureSections(results) {
  const sections = [];
  for (const result of results) {
    if (!result.failures.newFailures.length && !result.failures.fixedFailures.length) continue;
    sections.push(`#### ${label(result.source)}`);
    sections.push(...listLines('New failures', result.failures.newFailures));
    sections.push(...listLines('Fixed failures', result.failures.fixedFailures));
    sections.push('');
  }
  return sections.length ? sections : ['No new or fixed failures.'];
}

function message() {
  const product = productResults();
  const changed = changedResults();
  const lines = [
    '## Observatory updated',
    '',
    `Commit: ${process.env.GITHUB_SHA || execSync('git rev-parse HEAD', { cwd: repoRoot, encoding: 'utf8' }).trim()}`,
    '',
    '### Product results',
    product.length ? table(RESULT_HEADERS, product.map(result => result.row)) : '_No product results found._',
    '',
    '### New test results in this push',
    changed.length ? table(RESULT_HEADERS, changed.map(result => result.row)) : '_No product test result JSON files changed in this push._',
    '',
    '### Previous-run comparison',
    changed.length ? table(['Source', 'Date', 'Summary delta', 'New failures', 'Fixed failures'], comparisonRows(changed)) : '_No product test result JSON files changed in this push._',
    '',
    '### Failure changes',
    ...(changed.length ? failureSections(changed) : ['_No product test result JSON files changed in this push._']),
  ];
  return lines.join('\n');
}

async function postMattermost(text) {
  const baseUrl = process.env.MATTERMOST_URL || 'https://mattermost.beoflow.com';
  const token = process.env.MATTERMOST_BOT_TOKEN;
  const channelId = process.env.MATTERMOST_CHANNEL_ID;
  if (!token || !channelId) {
    console.log('Mattermost token or channel not configured; printing message only.');
    console.log(text);
    return;
  }
  const response = await fetch(`${baseUrl.replace(/\/$/, '')}/api/v4/posts`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ channel_id: channelId, message: text }),
  });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Mattermost post failed: ${response.status} ${body}`);
  }
  console.log('Posted Mattermost observatory summary.');
}

const dryRun = process.argv.includes('--dry-run');
const text = message();
if (dryRun) {
  console.log(text);
} else {
  postMattermost(text).catch(err => {
    console.error(err.message);
    process.exit(1);
  });
}
