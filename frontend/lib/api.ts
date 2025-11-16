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

export interface AssetsResponse {
  assets: string[];
}

// Determine API base URL for client and server environments
const API_BASE_URL = (() => {
  if (typeof window !== "undefined") {
    return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  } else {
    return process.env.NEXT_PUBLIC_API_URL || "http://backend:8000";
  }
})();

// Custom API error class for structured error handling
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

// Helper function for HTTP requests with unified error handling
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

export interface CreateAlarmResponse {
  status: string;
  alarm_id: number;
}

// Submit new alarm to backend API
export async function createAlarm(data: AlarmData): Promise<CreateAlarmResponse> {
  return fetchWithError<CreateAlarmResponse>(`${API_BASE_URL}/alarms`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
}

// Retrieve available assets for a given class from backend API
export async function getAssets(assetClass: AssetClass): Promise<AssetsResponse> {
  return fetchWithError<AssetsResponse>(`${API_BASE_URL}/assets/${assetClass}`);
}