// Type definitions for alarm system
export type AssetClass = 'crypto' | 'forex' | 'stock';
export type AlarmType = 'price' | 'rsi' | 'bollinger';

export interface AlarmParams {
  target_price?: number;
  period?: number;
  threshold?: number;
  std_dev?: number;
  direction?: 'above' | 'below';
}

export interface AlarmData {
  asset_class: AssetClass;
  asset_symbol: string;
  alarm_type: AlarmType;
  params: AlarmParams;
  email: string;
}

export interface AlarmResponse {
  id: number;
  asset_class: AssetClass;
  asset_symbol: string;
  alarm_type: AlarmType;
  params: AlarmParams;
  email: string;
  created_at: string;
  status?: string;
}

export interface AssetsResponse {
  assets: string[];
}

// ------------------------------
// API URL configuration
// ------------------------------
// Tarayıcı (frontend) ve SSR/Docker ortamı farkını otomatik algılar
const API_BASE_URL = (() => {
  if (typeof window !== "undefined") {
    // Tarayıcıda çalışıyorsa
    return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  } else {
    // Node / SSR tarafı
    return process.env.NEXT_PUBLIC_API_URL || "http://backend:8000";
  }
})();

// ------------------------------
// API Error
// ------------------------------
export class APIError extends Error {
  statusCode: number;
  details?: any;

  constructor(statusCode: number, message: string, details?: any) {
    super(message);
    this.name = 'APIError';
    this.statusCode = statusCode;
    this.details = details;
  }
}

// ------------------------------
// Fetch helper
// ------------------------------
async function fetchWithError<T>(url: string, options?: RequestInit): Promise<T> {
  try {
    const res = await fetch(url, options);
    if (!res.ok) {
      let errorData: any = {};
      try {
        errorData = await res.json();
      } catch {
        errorData = { detail: res.statusText };
      }
      throw new APIError(res.status, errorData.detail || res.statusText || 'API error', errorData);
    }
    return res.json();
  } catch (err) {
    if (err instanceof APIError) throw err;
    throw new APIError(500, err instanceof Error ? err.message : 'Unknown error', err);
  }
}

// ------------------------------
// API functions
// ------------------------------
export async function createAlarm(data: AlarmData): Promise<AlarmResponse> {
  return fetchWithError<AlarmResponse>(`${API_BASE_URL}/alarms`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
}

export async function getAssets(assetClass: AssetClass): Promise<AssetsResponse> {
  return fetchWithError<AssetsResponse>(`${API_BASE_URL}/assets/${assetClass}`);
}

// ------------------------------
// Asset caching
// ------------------------------
interface CacheEntry {
  data: string[];
  timestamp: number;
}

const assetCache: Record<string, CacheEntry> = {};
const CACHE_DURATION_MS = 5 * 60 * 1000; // 5 dakika

export async function getCachedAssets(assetClass: AssetClass): Promise<string[]> {
  const now = Date.now();
  const cached = assetCache[assetClass];
  if (cached && now - cached.timestamp < CACHE_DURATION_MS) {
    return cached.data;
  }

  try {
    const response = await getAssets(assetClass);
    assetCache[assetClass] = { data: response.assets, timestamp: now };
    return response.assets;
  } catch (err) {
    if (cached) {
      console.warn('Using cached assets due to API error');
      return cached.data;
    }
    throw err;
  }
}

// ------------------------------
// Type guard
// ------------------------------
export function isValidAssetClass(assetClass: string): assetClass is AssetClass {
  return ['crypto', 'forex', 'stock'].includes(assetClass);
}
