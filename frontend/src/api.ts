import type { Store } from './types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'

export async function fetchStores(): Promise<Store[]> {
  const response = await fetch(`${API_BASE_URL}/stores`)
  if (!response.ok) {
    throw new Error(`Store API request failed with status ${response.status}`)
  }
  return response.json() as Promise<Store[]>
}
