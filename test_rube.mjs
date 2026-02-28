// Try to find the correct Rube API endpoint
const endpoints = [
    'https://rube.app/v1/execute',
    'https://app.rube.app/v1/execute',
    'https://rube.app/api/v1/execute',
];

const RUBE_API_KEY = 'rube_02d419ed60f0827a3124bb12fb466b84bcbc660065';

async function tryEndpoint(url) {
    try {
        const res = await fetch(url, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${RUBE_API_KEY}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                tool_slug: 'ASANA_GET_SECTIONS_IN_PROJECT',
                arguments: { project_gid: '1209825657498498' },
            }),
            signal: AbortSignal.timeout(10000),
        });
        const text = await res.text();
        console.log(`${url} => ${res.status}: ${text.substring(0, 300)}`);
    } catch (e) {
        console.log(`${url} => ERROR: ${e.message}`);
    }
}

for (const url of endpoints) {
    await tryEndpoint(url);
}
