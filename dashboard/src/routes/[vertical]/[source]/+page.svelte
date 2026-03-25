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

	// Group entries by module/suite
	function groupEntries(entries) {
		const groups = {};
		for (const entry of entries) {
			const key = entry.module || entry.suite || 'Other';
			if (!groups[key]) groups[key] = [];
			groups[key].push(entry);
		}
		return Object.entries(groups).sort((a, b) => a[0].localeCompare(b[0]));
	}
</script>

<main>
	<a class="back" href="/">&larr; Back</a>

	<h1>{formatSource(data.source)}</h1>
	<p class="vertical-label">{data.vertical}</p>

	{#if data.latest}
		{@const s = data.latest.data.summary}
		{@const allPassing = s.failed === 0}

		<div class="summary-bar" class:green={allPassing} class:red={!allPassing}>
			<div class="stat">
				<span class="number">{s.passed}</span>
				<span class="label">passed</span>
			</div>
			{#if s.failed > 0}
				<div class="stat">
					<span class="number failed">{s.failed}</span>
					<span class="label">failed</span>
				</div>
			{/if}
			{#if s.skipped > 0}
				<div class="stat">
					<span class="number skipped">{s.skipped}</span>
					<span class="label">skipped</span>
				</div>
			{/if}
			<div class="stat">
				<span class="number">{s.total}</span>
				<span class="label">total</span>
			</div>
			{#if s.duration_seconds}
				<div class="stat">
					<span class="number">{s.duration_seconds}s</span>
					<span class="label">duration</span>
				</div>
			{/if}
			{#if s.coverage_percent != null}
				<div class="stat">
					<span class="number">{s.coverage_percent}%</span>
					<span class="label">coverage</span>
				</div>
			{/if}
		</div>

		<p class="date">Run: {data.latest.data.timestamp} ({data.latest.file.replace('.json', '')})</p>

		{#if data.latest.data.entries && data.latest.data.entries.length > 0}
			{@const grouped = groupEntries(data.latest.data.entries)}

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
	{:else}
		<p class="empty">No data available for this source.</p>
	{/if}
</main>

<style>
	main {
		max-width: 960px;
		margin: 0 auto;
		padding: 2rem;
		font-family: system-ui, -apple-system, sans-serif;
		color: #1a1a1a;
	}

	.back {
		color: #666;
		text-decoration: none;
		font-size: 0.9rem;
	}
	.back:hover { color: #1a1a1a; }

	h1 { font-size: 1.5rem; margin: 0.75rem 0 0; }

	.vertical-label {
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: #999;
		font-size: 0.8rem;
		margin: 0.25rem 0 1.5rem;
	}

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

	.stat { display: flex; flex-direction: column; align-items: center; }
	.stat .number { font-size: 1.25rem; font-weight: 700; }
	.stat .number.failed { color: #ef4444; }
	.stat .number.skipped { color: #f59e0b; }
	.stat .label { font-size: 0.75rem; color: #999; text-transform: uppercase; letter-spacing: 0.05em; }

	.date { color: #999; font-size: 0.8rem; margin-bottom: 1.5rem; }

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

	.empty { color: #999; font-style: italic; }
</style>
