export const prerender = true;

// Import all data JSON files at build time
// Path is relative to project root (dashboard/), so ../../ doesn't work.
// We use a Vite alias configured in vite.config.js
const dataModules = import.meta.glob('$data/**/*.json', { eager: true });

function buildVerticals() {
	const verticals = {};

	for (const [path, module] of Object.entries(dataModules)) {
		const data = module.default || module;

		// Path: /../../data/product/security-backend/2026-03-25.json
		const parts = path.split('/');
		const filename = parts.pop(); // 2026-03-25.json
		const source = parts.pop(); // security-backend
		const vertical = parts.pop(); // product

		if (!verticals[vertical]) verticals[vertical] = {};
		if (!verticals[vertical][source]) verticals[vertical][source] = [];

		verticals[vertical][source].push({ file: filename, data });
	}

	// Keep only the latest file per source
	for (const vertical of Object.values(verticals)) {
		for (const [source, files] of Object.entries(vertical)) {
			files.sort((a, b) => b.file.localeCompare(a.file));
			vertical[source] = files[0]; // latest only
		}
	}

	return verticals;
}

export function load() {
	return { verticals: buildVerticals() };
}
