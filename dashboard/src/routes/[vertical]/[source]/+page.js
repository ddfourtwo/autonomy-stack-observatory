export const prerender = true;

const dataModules = import.meta.glob('$data/**/*.json', { eager: true });

export function entries() {
	const routes = [];
	for (const path of Object.keys(dataModules)) {
		const parts = path.split('/');
		const source = parts[parts.length - 2];
		const vertical = parts[parts.length - 3];
		// Deduplicate — we only need one route per vertical/source pair
		if (!routes.find(r => r.vertical === vertical && r.source === source)) {
			routes.push({ vertical, source });
		}
	}
	return routes;
}

export function load({ params }) {
	const { vertical, source } = params;

	// Find all data files for this vertical/source
	const files = [];
	for (const [path, module] of Object.entries(dataModules)) {
		const parts = path.split('/');
		const fileSource = parts[parts.length - 2];
		const fileVertical = parts[parts.length - 3];
		const filename = parts[parts.length - 1];

		if (fileVertical === vertical && fileSource === source) {
			files.push({ file: filename, data: module.default || module });
		}
	}

	files.sort((a, b) => b.file.localeCompare(a.file));
	const latest = files[0] || null;

	return { vertical, source, latest, history: files };
}
