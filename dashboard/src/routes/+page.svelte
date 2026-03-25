<script>
	let { data } = $props();

	const verticalLabels = {
		product: 'Product',
		growth: 'Growth',
		website: 'Website',
		sales: 'Sales',
		finance: 'Finance',
		infrastructure: 'Infrastructure',
	};

	function getStatus(summary, source) {
		if (!summary) return 'empty';
		// Security coverage uses overall_coverage
		if (summary.overall_coverage != null) {
			if (summary.overall_coverage >= 80) return 'green';
			if (summary.overall_coverage >= 30) return 'amber';
			return 'red';
		}
		if (summary.failed > 0) return 'red';
		if (summary.total === 0) return 'empty';
		return 'green';
	}

	function isCoverage(sourceData) {
		return sourceData.summary?.overall_coverage != null;
	}

	function formatSource(source) {
		return source.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
	}
</script>

<main>
	<h1>Observatory</h1>
	<p class="subtitle">Autonomy stack measurement layer</p>

	{#each Object.entries(data.verticals) as [vertical, sources]}
		{#if Object.keys(sources).length > 0}
			<section class="vertical">
				<h2>{verticalLabels[vertical] || vertical}</h2>
				<div class="sources">
					{#each Object.entries(sources) as [source, { file, data: sourceData }]}
						{@const status = getStatus(sourceData.summary, source)}
						<a class="card {status}" href="/{vertical}/{source}">
							<div class="card-header">
								<span class="indicator"></span>
								<h3>{formatSource(source)}</h3>
							</div>

							{#if isCoverage(sourceData)}
								<div class="summary">
									<span class="coverage-pct">{sourceData.summary.overall_coverage}%</span>
									<span class="total">coverage across {sourceData.summary.total_endpoints} endpoints</span>
								</div>
							{:else}
								<div class="summary">
									<span class="passed">{sourceData.summary.passed} passed</span>
									{#if sourceData.summary.failed > 0}
										<span class="failed">{sourceData.summary.failed} failed</span>
									{/if}
									<span class="total">/ {sourceData.summary.total} total</span>
								</div>

								{#if sourceData.summary.duration_seconds}
									<div class="meta">{sourceData.summary.duration_seconds}s</div>
								{/if}
							{/if}

							<div class="meta">{file.replace('.json', '')}</div>
						</a>
					{/each}
				</div>
			</section>
		{/if}
	{/each}

	{#if Object.values(data.verticals).every(v => Object.keys(v).length === 0)}
		<p class="empty">No data yet. Run a test playbook to populate.</p>
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

	h1 { font-size: 1.5rem; margin: 0; }

	.subtitle {
		color: #666;
		margin: 0.25rem 0 2rem;
		font-size: 0.9rem;
	}

	.vertical { margin-bottom: 2rem; }

	.vertical h2 {
		font-size: 1.1rem;
		margin: 0 0 0.75rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: #666;
		font-weight: 500;
	}

	.sources {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
		gap: 1rem;
	}

	a.card {
		display: block;
		border: 1px solid #e0e0e0;
		border-radius: 8px;
		padding: 1.25rem;
		border-left: 4px solid #e0e0e0;
		text-decoration: none;
		color: inherit;
		transition: box-shadow 0.15s;
		cursor: pointer;
	}

	a.card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.08); }

	.card.green { border-left-color: #22c55e; }
	.card.red { border-left-color: #ef4444; }
	.card.amber { border-left-color: #f59e0b; }
	.card.empty { border-left-color: #d1d5db; }

	.card-header {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-bottom: 0.75rem;
	}

	.indicator {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background: #d1d5db;
		flex-shrink: 0;
	}

	.green .indicator { background: #22c55e; }
	.red .indicator { background: #ef4444; }
	.amber .indicator { background: #f59e0b; }

	.card-header h3 { margin: 0; font-size: 0.95rem; }

	.summary {
		display: flex;
		gap: 0.5rem;
		align-items: baseline;
		margin-bottom: 0.25rem;
	}

	.passed { color: #22c55e; font-weight: 600; font-size: 0.9rem; }
	.failed { color: #ef4444; font-weight: 600; font-size: 0.9rem; }
	.total { color: #999; font-size: 0.85rem; }
	.meta { color: #999; font-size: 0.8rem; }
	.coverage-pct { color: #f59e0b; font-weight: 600; font-size: 0.9rem; }

	.empty { color: #999; font-style: italic; }
</style>
