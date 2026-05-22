import { extractDomain, normalizeDomain, STORAGE_KEYS, type AuthState } from './shared';
import { logAttempt } from './api';

const BLOCKED_PAGE = chrome.runtime.getURL('blocked.html');
const unlockCache = new Map<string, number>();

async function getAuthState(): Promise<AuthState> {
  const result = await chrome.storage.local.get(STORAGE_KEYS.auth);
  return result[STORAGE_KEYS.auth] ?? {};
}

async function getBlockedSites(): Promise<string[]> {
  const result = await chrome.storage.local.get(STORAGE_KEYS.blockedSites);
  return (result[STORAGE_KEYS.blockedSites] ?? []).map((site: { domain: string }) => normalizeDomain(site.domain));
}

async function shouldBlock(url: string): Promise<string | null> {
  const domain = extractDomain(url);
  if (!domain) {
    return null;
  }

  const auth = await getAuthState();
  const unlockUntil = auth.unlockUntil ?? 0;
  if (unlockUntil > Date.now()) {
    return null;
  }

  const blockedSites = await getBlockedSites();
  const match = blockedSites.find((site) => domain === site || domain.endsWith(`.${site}`));
  return match ?? null;
}

chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  const candidateUrl = changeInfo.url ?? tab.url;
  if (!candidateUrl) {
    return;
  }

  const blockedDomain = await shouldBlock(candidateUrl);
  if (!blockedDomain) {
    return;
  }

  const auth = await getAuthState();
  const token = auth.token;
  await chrome.tabs.update(tabId, { url: `${BLOCKED_PAGE}?domain=${encodeURIComponent(blockedDomain)}` });

  if (token) {
    await logAttempt(token, {
      domain: blockedDomain,
      url: candidateUrl,
      tab_id: tabId,
      source: 'extension',
      reason: 'blocked',
    });
  }
});

chrome.tabs.onRemoved.addListener(async () => {
  const auth = await getAuthState();
  if (!auth.token) {
    return;
  }
  const unlockUntil = auth.unlockUntil ?? 0;
  if (unlockUntil > Date.now()) {
    return;
  }
});

chrome.runtime.onInstalled.addListener(async () => {
  const auth = await getAuthState();
  if (!auth.token) {
    await chrome.storage.local.set({ [STORAGE_KEYS.auth]: { token: '' } });
  }
});

chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name !== 'unlock-expiry') {
    return;
  }
  const auth = await getAuthState();
  if ((auth.unlockUntil ?? 0) <= Date.now()) {
    await chrome.storage.local.set({ [STORAGE_KEYS.auth]: { ...auth, unlockUntil: 0 } });
  }
});

chrome.tabs.onActivated.addListener(async ({ tabId }) => {
  const tab = await chrome.tabs.get(tabId);
  const blockedDomain = tab.url ? await shouldBlock(tab.url) : null;
  if (blockedDomain && tab.url) {
    const auth = await getAuthState();
    if (auth.token) {
      await logAttempt(auth.token, {
        domain: blockedDomain,
        url: tab.url,
        tab_id: tabId,
        source: 'extension',
        reason: 'activated',
      });
    }
  }
});
