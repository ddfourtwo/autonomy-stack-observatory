// Proxies /media/* requests to the private R2 bucket.
// Access is gated by Cloudflare Access on the Pages domain.
export async function onRequest(context) {
	const { params, env } = context;
	const key = params.path.join('/');

	if (!key) {
		return new Response('Not found', { status: 404 });
	}

	const object = await env.OBSERVATORY_MEDIA.get(key);

	if (!object) {
		return new Response('Not found', { status: 404 });
	}

	const headers = new Headers();
	object.writeHttpMetadata(headers);
	headers.set('Cache-Control', 'public, max-age=86400');

	return new Response(object.body, { headers });
}
