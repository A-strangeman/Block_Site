export type AuthState = {
  token?: string;
  unlockUntil?: number;
};

export type BlockedSite = {
  id?: string;
  domain: string;
  is_active?: boolean;
};

export type AttemptPayload = {
  domain: string;
  url: string;
  tab_id?: number;
  source: string;
  reason: string;
};

export const STORAGE_KEYS = {
  auth: 'focusguard_auth',
  blockedSites: 'focusguard_blocked_sites',
  friend: 'focusguard_friend',
};

export function normalizeDomain(value: string): string {
  return value.trim().toLowerCase().replace(/^https?:\/\//, '').replace(/^www\./, '').split('/')[0];
}

export function extractDomain(url: string): string {
  try {
    return normalizeDomain(new URL(url).hostname);
  } catch {
    return '';
  }
}
