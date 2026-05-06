#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const repoRoot = path.resolve(__dirname, '..');
const productDir = path.join(repoRoot, 'data', 'product');

function label(source) {
  return source.replace(/-/g, ' ').toUpperCase();
}

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

function latestFile(dir) {
  if (!fs.existsSync(dir)) return null;
  const files = fs.readdirSync(dir).filter(f => f.endsWith('.json')).sort();
  if (!files.length) return null;
  return path.join(dir, files[files.length - 1]);
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

function summaryRow(source, file) {
  const data = readJson(file);
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

function productRows() {
  if (!fs.existsSync(productDir)) return [];
  return fs.readdirSync(productDir, { withFileTypes: true })
    .filter(entry => entry.isDirectory())
    .map(entry => [entry.name, latestFile(path.join(productDir, entry.name))])
    .filter(([, file]) => file)
    .map(([source, file]) => summaryRow(source, file))
    .sort((a, b) => a[0].localeCompare(b[0]));
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

function changedRows() {
  return changedDataFiles().map(name => {
    const parts = name.split('/');
    return summaryRow(parts[2], path.join(repoRoot, name));
  }).sort((a, b) => a[0].localeCompare(b[0]));
}

function message() {
  const product = productRows();
  const changed = changedRows();
  const lines = [
    '## Observatory updated',
    '',
    `Commit: ${process.env.GITHUB_SHA || execSync('git rev-parse HEAD', { cwd: repoRoot, encoding: 'utf8' }).trim()}`,
    '',
    '### Product results',
    product.length ? table(['Source', 'Date', 'Pass %', 'Fail %', 'Passed', 'Failed', 'Errors', 'Skipped', 'Total', 'Duration'], product) : '_No product results found._',
    '',
    '### New test results in this push',
    changed.length ? table(['Source', 'Date', 'Pass %', 'Fail %', 'Passed', 'Failed', 'Errors', 'Skipped', 'Total', 'Duration'], changed) : '_No product test result JSON files changed in this push._',
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
