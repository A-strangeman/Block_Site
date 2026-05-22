import { extractDomain, STORAGE_KEYS, type BlockedSite } from './shared';

const pageUrl = location.href;
const domain = extractDomain(pageUrl);

async function isBlockedDomain(currentDomain: string): Promise<boolean> {
  const result = await chrome.storage.local.get(STORAGE_KEYS.blockedSites);
  const blockedSites = (result[STORAGE_KEYS.blockedSites] ?? []) as BlockedSite[];
  return blockedSites.some((site) => {
    const normalized = site.domain.toLowerCase();
    return currentDomain === normalized || currentDomain.endsWith(`.${normalized}`);
  });
}

(async () => {
  if (!domain) {
    return;
  }

  const blocked = await isBlockedDomain(domain);
  if (!blocked) {
    return;
  }

  const blockedUrl = chrome.runtime.getURL(`blocked.html?domain=${encodeURIComponent(domain)}`);
  if (!pageUrl.startsWith(blockedUrl)) {
    window.location.replace(blockedUrl);
  }
})();
