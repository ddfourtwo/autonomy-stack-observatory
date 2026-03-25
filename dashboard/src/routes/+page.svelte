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

	function getStatus(summary) {
		if (!summary) return 'empty';
		if (summary.failed > 0) return 'red';
		if (summary.total === 0) return 'empty';
		return 'green';
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
						{@const status = getStatus(sourceData.summary)}
						<div class="card {status}">
							<div class="card-header">
								<span class="indicator"></span>
								<h3>{formatSource(source)}</h3>
							</div>

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

							<div class="meta">{file.replace('.json', '')}</div>

							{#if sourceData.entries && sourceData.entries.length > 0}
								{@const failures = sourceData.entries.filter(e => e.status === 'failed')}
								{#if failures.length > 0}
									<div class="failures">
										<h4>Failures</h4>
										{#each failures as entry}
											<div class="failure">
												<span class="name">{entry.name}</span>
												{#if entry.error}
													<span class="error">{entry.error}</span>
												{/if}
											</div>
										{/each}
									</div>
								{/if}
							{/if}
						</div>
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

	h1 {
		font-size: 1.5rem;
		margin: 0;
	}

	.subtitle {
		color: #666;
		margin: 0.25rem 0 2rem;
		font-size: 0.9rem;
	}

	.vertical {
		margin-bottom: 2rem;
	}

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

	.card {
		border: 1px solid #e0e0e0;
		border-radius: 8px;
		padding: 1.25rem;
		border-left: 4px solid #e0e0e0;
	}

	.card.green { border-left-color: #22c55e; }
	.card.red { border-left-color: #ef4444; }
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

	.card-header h3 {
		margin: 0;
		font-size: 0.95rem;
	}

	.summary {
		display: flex;
		gap: 0.5rem;
		align-items: baseline;
		margin-bottom: 0.25rem;
	}

	.passed {
		color: #22c55e;
		font-weight: 600;
		font-size: 0.9rem;
	}

	.failed {
		color: #ef4444;
		font-weight: 600;
		font-size: 0.9rem;
	}

	.total {
		color: #999;
		font-size: 0.85rem;
	}

	.meta {
		color: #999;
		font-size: 0.8rem;
	}

	.failures {
		margin-top: 0.75rem;
		padding-top: 0.75rem;
		border-top: 1px solid #f0f0f0;
	}

	.failures h4 {
		margin: 0 0 0.5rem;
		font-size: 0.8rem;
		color: #ef4444;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.failure {
		margin-bottom: 0.5rem;
	}

	.failure .name {
		display: block;
		font-size: 0.85rem;
		font-family: monospace;
	}

	.failure .error {
		display: block;
		font-size: 0.8rem;
		color: #999;
		margin-top: 0.125rem;
	}

	.empty {
		color: #999;
		font-style: italic;
	}
</style>
