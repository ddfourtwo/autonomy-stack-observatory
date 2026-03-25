<script>
	// Data will be loaded at build time from ../data/
	// For now, placeholder structure
</script>

<main>
	<h1>Observatory</h1>
	<p>Measurement layer for the autonomy stack. Dashboard coming soon.</p>

	<section class="verticals">
		<div class="card">
			<h2>Product</h2>
			<p>E2E tests, unit tests, Sentry errors</p>
		</div>
		<div class="card">
			<h2>Sales</h2>
			<p>PostHog usage metrics</p>
		</div>
		<div class="card">
			<h2>Infrastructure</h2>
			<p>Uptime, resource usage</p>
		</div>
		<div class="card">
			<h2>Growth</h2>
			<p>Facebook Ads, Google Ads</p>
		</div>
		<div class="card">
			<h2>Website</h2>
			<p>Analytics, traffic</p>
		</div>
		<div class="card">
			<h2>Finance</h2>
			<p>MRR, churn</p>
		</div>
	</section>
</main>

<style>
	main {
		max-width: 960px;
		margin: 0 auto;
		padding: 2rem;
		font-family: system-ui, -apple-system, sans-serif;
	}

	h1 {
		font-size: 1.5rem;
		margin-bottom: 0.5rem;
	}

	.verticals {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
		gap: 1rem;
		margin-top: 2rem;
	}

	.card {
		border: 1px solid #e0e0e0;
		border-radius: 8px;
		padding: 1.5rem;
	}

	.card h2 {
		font-size: 1.1rem;
		margin: 0 0 0.5rem;
	}

	.card p {
		color: #666;
		margin: 0;
		font-size: 0.9rem;
	}
</style>
