<script>
	let { data } = $props();

	function formatSource(source) {
		return source.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
	}

	function statusColor(status) {
		if (status === 'passed') return '#22c55e';
		if (status === 'failed') return '#ef4444';
		if (status === 'skipped') return '#f59e0b';
		return '#999';
	}

	function groupEntries(entries) {
		const groups = {};
		for (const entry of entries) {
			const key = entry.module || entry.suite || 'Other';
			if (!groups[key]) groups[key] = [];
			groups[key].push(entry);
		}
		return Object.entries(groups).sort((a, b) => a[0].localeCompare(b[0]));
	}

	const isSecurityCoverage = $derived(data.source === 'security-coverage');
	const sourceData = $derived(data.latest?.data);

	const METHOD_COLORS = {
		GET: '#61affe',
		POST: '#49cc90',
		PUT: '#fca130',
		PATCH: '#50e3c2',
		DELETE: '#f93e3e',
		HEAD: '#9012fe',
		OPTIONS: '#0d5aa7',
	};

	const TEST_TYPE_LABELS = {
		auth: { short: 'Auth', tip: 'Unauthenticated requests return 401' },
		idor: { short: 'IDOR', tip: 'Users cannot access other users\' resources' },
		input: { short: 'Input', tip: 'Malicious input (XSS, SQLi) doesn\'t cause 500' },
		rate: { short: 'Rate', tip: 'Rate limits enforced to prevent abuse' },
		jwt: { short: 'JWT', tip: 'Expired/invalid tokens rejected with 401' },
		cors: { short: 'CORS', tip: 'Cross-origin requests from untrusted domains blocked' },
		sensitive: { short: 'Sens.', tip: 'No secrets/tokens/keys in responses' },
	};
</script>

<main>
	<a class="back" href="/">&larr; Back</a>

	<h1>{formatSource(data.source)}</h1>
	<p class="vertical-label">{data.vertical}</p>

	{#if !sourceData}
		<p class="empty">No data available.</p>
	{:else if isSecurityCoverage}
		<!-- Security Coverage Matrix -->
		<div class="coverage-summary">
			<div class="stat primary">
				<div class="stat-value">{sourceData.summary.overall_coverage}%</div>
				<div class="stat-label">Overall</div>
			</div>
			{#each Object.entries(sourceData.summary.coverage) as [type, pct]}
				{@const info = sourceData.summary.tests_by_type[type]}
				<div class="stat">
					<div class="stat-value">{pct}%</div>
					<div class="stat-label">{TEST_TYPE_LABELS[type]?.short || type}</div>
					<div class="stat-detail">{info.covered}/{info.applicable}</div>
				</div>
			{/each}
		</div>

		<p class="date">{sourceData.summary.total_endpoints} endpoints &middot; {data.latest.file.replace('.json', '')}</p>

		<div class="table-wrap">
			<table class="coverage-table">
				<thead>
					<tr>
						<th style="width:80px">Method</th>
						<th>Endpoint</th>
						{#each sourceData.test_types as tt}
							<th class="center" style="width:50px" title={TEST_TYPE_LABELS[tt]?.tip || tt}>
								{TEST_TYPE_LABELS[tt]?.short || tt}
							</th>
						{/each}
						<th class="center" style="width:50px">Total</th>
					</tr>
				</thead>
				<tbody>
					{#each Object.entries(sourceData.sections) as [section, { endpoints, stats }]}
						<tr class="section-header">
							<td colspan={sourceData.test_types.length + 3}>
								<span class="section-name">{section}</span>
								<span class="section-stats">{stats.total} endpoints &middot; {stats.coverage_pct}% covered</span>
							</td>
						</tr>
						{#each endpoints as ep}
							{@const covered = sourceData.test_types.filter(tt => ep[`${tt}_tested`]).length}
							{@const applicable = sourceData.test_types.filter(tt => !ep[`${tt}_na`]).length}
							{@const allCovered = applicable > 0 && covered === applicable}
							{@const partiallyCovered = covered > 0 && !allCovered}
							<tr
								class:row-green={allCovered}
								class:row-amber={partiallyCovered}
							>
								<td>
									<span class="method" style="background:{METHOD_COLORS[ep.method] || '#888'}">
										{ep.method}
									</span>
								</td>
								<td class="path">{ep.path}</td>
								{#each sourceData.test_types as tt}
									<td class="center">
										{#if ep[`${tt}_tested`]}
											<span class="check">&#10003;</span>
										{:else if ep[`${tt}_na`]}
											<span class="na" title={ep[`${tt}_na_reason`] || 'N/A'}>N/A</span>
										{:else}
											<span class="cross">&#10007;</span>
										{/if}
									</td>
								{/each}
								<td class="center total-col">{covered}/{applicable}</td>
							</tr>
						{/each}
					{/each}
				</tbody>
			</table>
		</div>
	{:else}
		<!-- Standard test results -->
		{@const s = sourceData.summary}
		{@const allPassing = s.failed === 0}

		<div class="summary-bar" class:green={allPassing} class:red={!allPassing}>
			<div class="stat">
				<span class="stat-value">{s.passed}</span>
				<span class="stat-label">passed</span>
			</div>
			{#if s.failed > 0}
				<div class="stat">
					<span class="stat-value failed">{s.failed}</span>
					<span class="stat-label">failed</span>
				</div>
			{/if}
			{#if s.skipped > 0}
				<div class="stat">
					<span class="stat-value skipped">{s.skipped}</span>
					<span class="stat-label">skipped</span>
				</div>
			{/if}
			<div class="stat">
				<span class="stat-value">{s.total}</span>
				<span class="stat-label">total</span>
			</div>
			{#if s.duration_seconds}
				<div class="stat">
					<span class="stat-value">{s.duration_seconds}s</span>
					<span class="stat-label">duration</span>
				</div>
			{/if}
		</div>

		<p class="date">Run: {sourceData.timestamp} ({data.latest.file.replace('.json', '')})</p>

		{#if sourceData.entries && sourceData.entries.length > 0}
			{@const grouped = groupEntries(sourceData.entries)}

			{#each grouped as [group, entries]}
				<section class="group">
					<h2>{group}</h2>
					<table>
						<thead>
							<tr>
								<th class="status-col"></th>
								<th>Test</th>
								{#if entries.some(e => e.duration_seconds != null)}
									<th class="dur-col">Duration</th>
								{/if}
							</tr>
						</thead>
						<tbody>
							{#each entries as entry}
								<tr class:fail-row={entry.status === 'failed'}>
									<td class="status-col">
										<span class="dot" style="background: {statusColor(entry.status)}"></span>
									</td>
									<td>
										<span class="test-name">{entry.name}</span>
										{#if entry.error}
											<span class="error">{entry.error}</span>
										{/if}
									</td>
									{#if entries.some(e => e.duration_seconds != null)}
										<td class="dur-col">
											{entry.duration_seconds != null ? `${entry.duration_seconds}s` : ''}
										</td>
									{/if}
								</tr>
							{/each}
						</tbody>
					</table>
				</section>
			{/each}
		{:else}
			<p class="empty">No individual test entries recorded.</p>
		{/if}
	{/if}
</main>

<style>
	main {
		max-width: 1460px;
		margin: 0 auto;
		padding: 2rem;
		font-family: 'Open Sans', system-ui, -apple-system, sans-serif;
		color: #3b4151;
	}

	.back { color: #666; text-decoration: none; font-size: 0.9rem; }
	.back:hover { color: #1a1a1a; }

	h1 { font-size: 1.75rem; font-weight: 700; margin: 0.75rem 0 0; }

	.vertical-label {
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: #999;
		font-size: 0.8rem;
		margin: 0.25rem 0 1.5rem;
	}

	.date { color: #999; font-size: 0.8rem; margin-bottom: 1.5rem; }
	.empty { color: #999; font-style: italic; }

	/* Coverage summary stats */
	.coverage-summary {
		display: flex;
		gap: 15px;
		margin-bottom: 1rem;
		flex-wrap: wrap;
	}

	.stat {
		background: #fff;
		border: 1px solid #d9d9d9;
		border-radius: 4px;
		padding: 15px 25px;
		text-align: center;
		min-width: 100px;
	}

	.stat.primary {
		background: #49cc90;
		border-color: #49cc90;
		color: #fff;
	}

	.stat-value { font-size: 1.5rem; font-weight: 700; }
	.stat-value.failed { color: #ef4444; }
	.stat-value.skipped { color: #f59e0b; }

	.stat-label {
		font-size: 0.7rem;
		text-transform: uppercase;
		color: #666;
		margin-top: 4px;
	}

	.stat.primary .stat-label { color: rgba(255,255,255,0.9); }

	.stat-detail { font-size: 0.65rem; color: #999; margin-top: 2px; }
	.stat.primary .stat-detail { color: rgba(255,255,255,0.7); }

	/* Coverage table */
	.table-wrap { overflow-x: auto; }

	.coverage-table {
		width: 100%;
		border-collapse: collapse;
		background: #fff;
		border: 1px solid #d9d9d9;
		border-radius: 4px;
		font-size: 0.85rem;
	}

	.coverage-table th {
		background: #fafafa;
		border-bottom: 1px solid #d9d9d9;
		padding: 10px 12px;
		text-align: left;
		font-size: 0.7rem;
		text-transform: uppercase;
		font-weight: 600;
		color: #3b4151;
	}

	.coverage-table td {
		padding: 8px 12px;
		border-bottom: 1px solid #ebebeb;
	}

	.coverage-table tr:last-child td { border-bottom: none; }

	.center { text-align: center; }

	.method {
		display: inline-block;
		padding: 4px 8px;
		border-radius: 3px;
		font-size: 0.7rem;
		font-weight: 700;
		color: #fff;
		min-width: 60px;
		text-align: center;
		text-transform: uppercase;
	}

	.path {
		font-family: 'Source Code Pro', monospace;
		font-size: 0.8rem;
		font-weight: 600;
	}

	.check { color: #49cc90; font-weight: 700; }
	.cross { color: #cc4949; font-weight: 400; }

	.na {
		color: #888;
		font-size: 0.65rem;
		font-weight: 600;
		cursor: help;
		text-decoration: underline dotted #ccc;
	}
	.na:hover { color: #555; }

	.total-col { font-weight: 600; font-size: 0.8rem; }

	.section-header { background: #f5f5f5; }
	.section-header td {
		padding: 10px 12px;
		border-bottom: 2px solid #d9d9d9;
	}
	.section-name { font-weight: 700; font-size: 0.85rem; }
	.section-stats { margin-left: 12px; font-size: 0.75rem; color: #888; font-weight: 400; }

	.row-green { background: rgba(73, 204, 144, 0.1); }
	.row-amber { background: rgba(252, 161, 48, 0.1); }

	/* Standard test results */
	.summary-bar {
		display: flex;
		gap: 2rem;
		padding: 1rem 1.25rem;
		border-radius: 8px;
		border: 1px solid #e0e0e0;
		border-left: 4px solid #d1d5db;
		margin-bottom: 0.5rem;
	}

	.summary-bar.green { border-left-color: #22c55e; }
	.summary-bar.red { border-left-color: #ef4444; }

	.group { margin-bottom: 2rem; }

	.group h2 {
		font-size: 0.85rem;
		font-family: monospace;
		color: #666;
		margin: 0 0 0.5rem;
		padding-bottom: 0.25rem;
		border-bottom: 1px solid #f0f0f0;
	}

	table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }

	th {
		text-align: left;
		font-weight: 500;
		color: #999;
		font-size: 0.75rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		padding: 0.375rem 0.5rem;
		border-bottom: 1px solid #e0e0e0;
	}

	td { padding: 0.375rem 0.5rem; border-bottom: 1px solid #f5f5f5; }

	.status-col { width: 24px; text-align: center; }
	.dur-col { width: 80px; text-align: right; color: #999; font-family: monospace; font-size: 0.8rem; }

	.dot {
		display: inline-block;
		width: 8px;
		height: 8px;
		border-radius: 50%;
	}

	.test-name { font-family: monospace; font-size: 0.8rem; }

	.error {
		display: block;
		font-size: 0.75rem;
		color: #ef4444;
		margin-top: 0.125rem;
		font-family: monospace;
	}

	.fail-row { background: #fef2f2; }
</style>
