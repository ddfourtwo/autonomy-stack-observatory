<script>
	let { data } = $props();

	function formatSource(source) {
		return source.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
	}

	const isSecurityCoverage = $derived(data.source === 'security-coverage');
	const sourceData = $derived(data.latest?.data);

	const METHOD_COLORS = {
		GET: '#61affe', POST: '#49cc90', PUT: '#fca130',
		PATCH: '#50e3c2', DELETE: '#f93e3e', HEAD: '#9012fe',
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

	const STATUS_ICON = { passed: '✓', failed: '✗', error: '✗', skipped: '—' };
	const STATUS_CLASS = { passed: 'pass', failed: 'fail', error: 'err', skipped: 'skip' };

	// Two-level grouping: app (section) → test class (subsection)
	function groupByAppAndClass(entries) {
		const apps = {};
		for (const entry of entries) {
			const moduleParts = (entry.module || 'other').split('.');
			const appKey = moduleParts[0];
			const appLabel = appKey.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
			const classKey = entry.suite || entry.module || 'Other';

			if (!apps[appLabel]) {
				apps[appLabel] = { classes: {}, passed: 0, failed: 0, errors: 0, total: 0 };
			}
			if (!apps[appLabel].classes[classKey]) {
				apps[appLabel].classes[classKey] = { module: entry.module, entries: [] };
			}
			apps[appLabel].classes[classKey].entries.push(entry);
			apps[appLabel].total++;
			if (entry.status === 'passed') apps[appLabel].passed++;
			else if (entry.status === 'error') apps[appLabel].errors++;
			else if (entry.status === 'failed') apps[appLabel].failed++;
		}

		return Object.entries(apps).sort((a, b) => {
			const aFail = a[1].failed + a[1].errors;
			const bFail = b[1].failed + b[1].errors;
			if (aFail > 0 && bFail === 0) return -1;
			if (bFail > 0 && aFail === 0) return 1;
			return a[0].localeCompare(b[0]);
		});
	}

	let expandedApps = $state({});
</script>

<main>
	<nav class="topbar"><div class="topbar-inner"><a href="/">&larr; Back to Observatory</a></div></nav>

	<div class="wrapper">
		<div class="info">
			<h1>{formatSource(data.source)}</h1>
			{#if sourceData}
				<p>{data.vertical} &middot; {data.latest.file.replace('.json', '')}</p>
			{/if}
		</div>

		{#if !sourceData}
			<p class="empty">No data available.</p>

		{:else if isSecurityCoverage}
			<div class="summary">
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

			<table>
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
							<tr class:row-green={allCovered} class:row-amber={partiallyCovered}>
								<td>
									<span class="method" style="background:{METHOD_COLORS[ep.method] || '#888'}">{ep.method}</span>
								</td>
								<td class="path">{ep.path}</td>
								{#each sourceData.test_types as tt}
									<td class="center">
										{#if ep[`${tt}_tested`]}
											<span class="check">✓</span>
										{:else if ep[`${tt}_na`]}
											<span class="na" title={ep[`${tt}_na_reason`] || 'N/A'}>N/A</span>
										{:else}
											<span class="cross">✗</span>
										{/if}
									</td>
								{/each}
								<td class="center total-col">{covered}/{applicable}</td>
							</tr>
						{/each}
					{/each}
				</tbody>
			</table>

		{:else}
			{@const s = sourceData.summary}
			<div class="summary">
				<div class="stat" class:primary={s.failed === 0} class:danger={s.failed > 0}>
					<div class="stat-value">{s.failed === 0 ? '100%' : Math.round((s.passed / s.total) * 100) + '%'}</div>
					<div class="stat-label">Pass Rate</div>
				</div>
				<div class="stat">
					<div class="stat-value">{s.passed}</div>
					<div class="stat-label">Passed</div>
				</div>
				{#if s.failed > 0}
					<div class="stat">
						<div class="stat-value stat-fail">{s.failed}</div>
						<div class="stat-label">Failed</div>
					</div>
				{/if}
				{#if s.errors > 0}
					<div class="stat">
						<div class="stat-value stat-error">{s.errors}</div>
						<div class="stat-label">Errors</div>
					</div>
				{/if}
				<div class="stat">
					<div class="stat-value">{s.total}</div>
					<div class="stat-label">Total</div>
				</div>
				{#if s.duration_seconds}
					<div class="stat">
						<div class="stat-value">{s.duration_seconds}s</div>
						<div class="stat-label">Duration</div>
					</div>
				{/if}
			</div>

			{#if s.total > 0}
				<div class="bar-container">
					<div class="bar-segment bar-pass" style="width:{(s.passed / s.total) * 100}%"></div>
					<div class="bar-segment bar-fail" style="width:{(s.failed / s.total) * 100}%"></div>
					{#if s.errors > 0}
						<div class="bar-segment bar-err" style="width:{(s.errors / s.total) * 100}%"></div>
					{/if}
				</div>
			{/if}

			{#if sourceData.entries && sourceData.entries.length > 0}
				{@const grouped = groupByAppAndClass(sourceData.entries)}

				<table>
					<thead>
						<tr>
							<th style="width:36px" class="center"></th>
							<th>Test</th>
							<th style="width:80px" class="center">Result</th>
						</tr>
					</thead>
					<tbody>
						{#each grouped as [appName, app]}
							{@const appHasFails = app.failed + app.errors > 0}
							{@const appExpanded = expandedApps[appName] ?? appHasFails}
							<tr
								class="section-header clickable"
								onclick={() => expandedApps[appName] = !appExpanded}
							>
								<td colspan="3">
									<span class="section-chevron">{appExpanded ? '▼' : '▶'}</span>
									<span class="section-name">{appName}</span>
									<span class="section-stats">
										{app.total} tests
										{#if app.failed > 0}
											&middot; <span class="stat-fail">{app.failed} failed</span>
										{/if}
										{#if app.errors > 0}
											&middot; <span class="stat-error">{app.errors} errors</span>
										{/if}
										&middot; {app.passed} passed
									</span>
								</td>
							</tr>
							{#if appExpanded}
								{#each Object.entries(app.classes) as [className, cls]}
									<tr class="class-header">
										<td colspan="3">
											<span class="class-name">{className}</span>
											<span class="class-module">{cls.module}</span>
										</td>
									</tr>
									{#each cls.entries as entry}
										<tr
											class:row-green={entry.status === 'passed'}
											class:row-red={entry.status === 'failed' || entry.status === 'error'}
										>
											<td class="center">
												<span class={STATUS_CLASS[entry.status] || 'skip'}>{STATUS_ICON[entry.status] || '?'}</span>
											</td>
											<td>
												<span class="test-name">{entry.name}</span>
												{#if entry.description}
													<div class="test-desc">{entry.description}</div>
												{/if}
												{#if entry.error}
													<div class="error-msg">{entry.error}</div>
												{/if}
											</td>
											<td class="center">
												<span class="result-badge {STATUS_CLASS[entry.status] || 'skip'}">
													{entry.status === 'error' ? 'ERROR' : (entry.status || '?').toUpperCase()}
												</span>
											</td>
										</tr>
									{/each}
								{/each}
							{/if}
						{/each}
					</tbody>
				</table>
			{:else}
				<p class="empty">No individual test entries recorded.</p>
			{/if}
		{/if}

		<div class="footer">
			<p>Data: <code>data/{data.vertical}/{data.source}/{data.latest?.file || '—'}</code></p>
		</div>
	</div>
</main>

<style>
	* { box-sizing: border-box; margin: 0; padding: 0; }
	main {
		font-family: 'Open Sans', system-ui, -apple-system, sans-serif;
		background: #fafafa;
		color: #3b4151;
		min-height: 100vh;
	}

	.topbar { background: #1b1b1b; padding: 10px 0; }
	.topbar-inner { max-width: 1460px; margin: 0 auto; padding: 0 20px; }
	.topbar a { color: #fff; text-decoration: none; font-size: 14px; }
	.topbar a:hover { text-decoration: underline; }

	.wrapper { max-width: 1460px; margin: 0 auto; padding: 20px; }

	.info { margin-bottom: 24px; }
	.info h1 { font-size: 28px; font-weight: 700; margin-bottom: 6px; }
	.info p { color: #666; font-size: 14px; }

	.summary { display: flex; gap: 15px; margin-bottom: 20px; flex-wrap: wrap; }

	.stat {
		background: #fff; border: 1px solid #d9d9d9; border-radius: 4px;
		padding: 15px 25px; text-align: center; min-width: 100px;
	}
	.stat.primary { background: #49cc90; border-color: #49cc90; color: #fff; }
	.stat.danger { background: #f93e3e; border-color: #f93e3e; color: #fff; }
	.stat.primary .stat-label, .stat.danger .stat-label { color: rgba(255,255,255,0.9); }

	.stat-value { font-size: 24px; font-weight: 700; }
	.stat-fail { color: #f93e3e; }
	.stat-error { color: #e67e22; }
	.stat-label { font-size: 11px; text-transform: uppercase; color: #666; margin-top: 4px; }
	.stat-detail { font-size: 11px; color: #999; margin-top: 2px; }

	.bar-container {
		display: flex; height: 8px; border-radius: 4px; overflow: hidden;
		margin-bottom: 24px; background: #e0e0e0;
	}
	.bar-segment { height: 100%; }
	.bar-pass { background: #49cc90; }
	.bar-fail { background: #f93e3e; }
	.bar-err { background: #e67e22; }

	table {
		width: 100%; border-collapse: collapse; background: #fff;
		border: 1px solid #d9d9d9; border-radius: 4px;
	}
	th {
		background: #fafafa; border-bottom: 1px solid #d9d9d9;
		padding: 12px 15px; text-align: left; font-size: 12px;
		text-transform: uppercase; font-weight: 600; color: #3b4151;
	}
	td { padding: 10px 15px; border-bottom: 1px solid #ebebeb; font-size: 14px; }
	tr:last-child td { border-bottom: none; }
	.center { text-align: center; }

	/* App-level section headers (like API sections in security) */
	.section-header { background: #f5f5f5 !important; }
	.section-header td { padding: 12px 15px; border-bottom: 2px solid #d9d9d9; }
	.section-header.clickable { cursor: pointer; user-select: none; }
	.section-header.clickable:hover { background: #eee !important; }
	.section-chevron { font-size: 10px; margin-right: 8px; color: #888; }
	.section-name { font-weight: 700; font-size: 14px; color: #3b4151; }
	.section-stats { margin-left: 12px; font-size: 12px; color: #888; font-weight: 400; }

	/* Test class sub-headers */
	.class-header { background: #fafafa !important; }
	.class-header td { padding: 8px 15px 8px 30px; border-bottom: 1px solid #e0e0e0; }
	.class-name { font-weight: 600; font-size: 13px; color: #555; }
	.class-module {
		margin-left: 10px; font-size: 11px; color: #aaa;
		font-family: 'Source Code Pro', monospace;
	}

	.row-green { background: rgba(73, 204, 144, 0.05); }
	.row-red { background: rgba(249, 62, 62, 0.05); }
	.row-amber { background: rgba(252, 161, 48, 0.1); }

	.pass { color: #49cc90; font-weight: 700; font-size: 16px; }
	.fail { color: #f93e3e; font-weight: 700; font-size: 16px; }
	.err { color: #e67e22; font-weight: 700; font-size: 16px; }
	.skip { color: #888; font-size: 14px; }
	.check { color: #49cc90; font-weight: 700; }
	.cross { color: #cc4949; }
	.na { color: #888; font-size: 11px; font-weight: 600; cursor: help; text-decoration: underline dotted #ccc; }
	.total-col { font-weight: 600; font-size: 13px; }

	.test-name {
		font-family: 'Source Code Pro', monospace; font-size: 13px;
		font-weight: 600; display: block;
	}
	.test-desc { font-size: 12px; color: #888; margin-top: 2px; padding-left: 12px; }
	.error-msg {
		font-family: 'Source Code Pro', monospace; font-size: 12px; color: #f93e3e;
		margin-top: 6px; padding: 6px 10px; background: rgba(249, 62, 62, 0.05);
		border-radius: 3px; border-left: 3px solid #f93e3e; word-break: break-word;
	}

	.result-badge {
		display: inline-block; padding: 3px 10px; border-radius: 3px;
		font-size: 11px; font-weight: 700; text-transform: uppercase;
	}
	.result-badge.pass { background: rgba(73, 204, 144, 0.15); color: #2d8a5e; }
	.result-badge.fail { background: rgba(249, 62, 62, 0.15); color: #c0392b; }
	.result-badge.err { background: rgba(230, 126, 34, 0.15); color: #a0522d; }
	.result-badge.skip { background: rgba(136, 136, 136, 0.15); color: #666; }

	.method {
		display: inline-block; padding: 4px 8px; border-radius: 3px;
		font-size: 11px; font-weight: 700; color: #fff; min-width: 60px;
		text-align: center; text-transform: uppercase;
	}
	.path { font-family: 'Source Code Pro', monospace; font-size: 13px; font-weight: 600; }

	.footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #d9d9d9; color: #666; font-size: 13px; }
	.footer code { background: #f0f0f0; padding: 3px 8px; border-radius: 3px; font-family: 'Source Code Pro', monospace; }
	.empty { color: #999; font-style: italic; }
</style>
