export interface Store {
  id: string
  name: string
  code: string
  timezone: string
  daily_target_cents: number
  responsible_name: string
  responsible_email: string
  last_seen_at: string | null
  online: boolean
}
