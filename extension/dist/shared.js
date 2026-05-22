export const STORAGE_KEYS = {
    auth: 'focusguard_auth',
    blockedSites: 'focusguard_blocked_sites',
    friend: 'focusguard_friend',
};
export function normalizeDomain(value) {
    return value.trim().toLowerCase().replace(/^https?:\/\//, '').replace(/^www\./, '').split('/')[0];
}
export function extractDomain(url) {
    try {
        return normalizeDomain(new URL(url).hostname);
    }
    catch {
        return '';
    }
}
