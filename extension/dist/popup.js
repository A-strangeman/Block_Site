import { STORAGE_KEYS, normalizeDomain } from './shared';
import { addBlockedSite, sendApproval, registerUser, loginUser } from './api';
const statusEl = document.getElementById('status');
const tokenInput = document.getElementById('token');
const domainInput = document.getElementById('domain');
const friendInput = document.getElementById('friend');
const emailInput = document.getElementById('email');
const passwordInput = document.getElementById('password');
function setStatus(message) {
    statusEl.textContent = message;
}
async function loadState() {
    const result = await chrome.storage.local.get([STORAGE_KEYS.auth, STORAGE_KEYS.blockedSites, STORAGE_KEYS.friend]);
    const auth = (result[STORAGE_KEYS.auth] ?? {});
    tokenInput.value = auth.token ?? '';
    friendInput.value = (result[STORAGE_KEYS.friend] ?? '');
}
async function saveAuth(token) {
    await chrome.storage.local.set({ [STORAGE_KEYS.auth]: { token } });
}
async function saveFriend(value) {
    await chrome.storage.local.set({ [STORAGE_KEYS.friend]: value });
}
async function saveBlockedSite(domain) {
    const result = await chrome.storage.local.get(STORAGE_KEYS.blockedSites);
    const blockedSites = (result[STORAGE_KEYS.blockedSites] ?? []).filter(Boolean);
    if (!blockedSites.some((site) => site.domain === domain)) {
        blockedSites.unshift({ domain });
    }
    await chrome.storage.local.set({ [STORAGE_KEYS.blockedSites]: blockedSites });
}
void loadState();
document.getElementById('save-token')?.addEventListener('click', async () => {
    await saveAuth(tokenInput.value.trim());
    setStatus('Token saved');
});
document.getElementById('register')?.addEventListener('click', async () => {
    const email = emailInput.value.trim();
    const password = passwordInput.value;
    if (!email || !password) {
        setStatus('Email and password required');
        return;
    }
    try {
        const resp = await registerUser(email, password);
        await saveAuth(resp.access_token);
        setStatus('Registered and token saved');
    }
    catch (err) {
        setStatus(err.message);
    }
});
document.getElementById('login')?.addEventListener('click', async () => {
    const email = emailInput.value.trim();
    const password = passwordInput.value;
    if (!email || !password) {
        setStatus('Email and password required');
        return;
    }
    try {
        const resp = await loginUser(email, password);
        await saveAuth(resp.access_token);
        setStatus('Logged in and token saved');
    }
    catch (err) {
        setStatus(err.message);
    }
});
document.getElementById('save-friend')?.addEventListener('click', async () => {
    await saveFriend(friendInput.value.trim());
    setStatus('Friend saved');
});
document.getElementById('add-site')?.addEventListener('click', async () => {
    const token = tokenInput.value.trim();
    const domain = normalizeDomain(domainInput.value);
    if (!token || !domain) {
        setStatus('Token and domain are required');
        return;
    }
    try {
        await addBlockedSite(token, domain);
        await saveBlockedSite(domain);
        setStatus(`Blocked ${domain}`);
    }
    catch (error) {
        setStatus(error.message);
    }
});
document.getElementById('unlock')?.addEventListener('click', async () => {
    const token = tokenInput.value.trim();
    if (!token) {
        setStatus('Save a token first');
        return;
    }
    try {
        await sendApproval(token);
        await chrome.storage.local.set({ [STORAGE_KEYS.auth]: { token, unlockUntil: Date.now() + 5 * 60 * 1000 } });
        await chrome.alarms.create('unlock-expiry', { when: Date.now() + 5 * 60 * 1000 });
        setStatus('Temporary unlock requested');
    }
    catch (error) {
        setStatus(error.message);
    }
});
