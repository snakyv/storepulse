export function formatMoney(cents: number, currency = 'EUR'): string {
  return new Intl.NumberFormat('en-GB', {
    style: 'currency',
    currency,
  }).format(cents / 100)
}

export function connectionLabel(connected: boolean): string {
  return connected ? 'Live channel connected' : 'Live channel reconnecting'
}
