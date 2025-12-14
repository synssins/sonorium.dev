/* Sonorium API Module */

// API Helper - works with both direct access and HA ingress
function getBasePath() {
    // For ingress, the page URL includes the ingress path
    // We need to use relative paths from wherever we're served
    const path = window.location.pathname;
    // Remove trailing slash and index.html if present
    let base = path.replace(/\/?(index\.html)?$/, '');
    return base || '';
}

const BASE_PATH = getBasePath();

async function api(method, endpoint, body = null) {
    const options = {
        method,
        headers: { 'Content-Type': 'application/json' }
    };
    if (body) options.body = JSON.stringify(body);

    // Use relative path from current location
    const url = `${BASE_PATH}/api${endpoint}`;
    const response = await fetch(url, options);
    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(error.detail || error.error || 'Request failed');
    }
    if (response.status === 204) return null;
    const result = await response.json();
    // Handle API-level errors (200 response with error field)
    if (result && result.error) {
        throw new Error(result.error);
    }
    return result;
}
