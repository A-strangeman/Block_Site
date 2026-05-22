const API_BASE = 'http://localhost:8000';
export async function apiFetch(path, token, init = {}) {
    const headers = new Headers(init.headers);
    headers.set('Content-Type', 'application/json');
    if (token) {
        headers.set('Authorization', `Bearer ${token}`);
    }
    return fetch(`${API_BASE}${path}`, { ...init, headers });
}
export async function addBlockedSite(token, domain) {
    const response = await apiFetch('/add-blocked-site', token, {
        method: 'POST',
        body: JSON.stringify({ domain }),
    });
    if (!response.ok) {
        throw new Error(`Failed to add blocked site: ${response.status}`);
    }
    return response.json();
}
export async function logAttempt(token, payload) {
    await apiFetch('/log-attempt', token, {
        method: 'POST',
        body: JSON.stringify(payload),
    });
}
export async function sendApproval(token) {
    const response = await apiFetch('/send-approval', token, { method: 'POST', body: '{}' });
    if (!response.ok) {
        throw new Error(`Failed to request approval: ${response.status}`);
    }
    return response.json();
}
export async function registerUser(email, password) {
    const response = await apiFetch('/register', undefined, {
        method: 'POST',
        body: JSON.stringify({ email, password }),
    });
    if (!response.ok) {
        const text = await response.text();
        throw new Error(`Register failed: ${response.status} ${text}`);
    }
    return response.json();
}
export async function loginUser(email, password) {
    const response = await apiFetch('/login', undefined, {
        method: 'POST',
        body: JSON.stringify({ email, password }),
    });
    if (!response.ok) {
        const text = await response.text();
        throw new Error(`Login failed: ${response.status} ${text}`);
    }
    return response.json();
}
