import { describe, expect, it } from 'vitest'

import { connectionLabel, formatMoney } from './format'

describe('format helpers', () => {
  it('formats integer minor units as money', () => {
    expect(formatMoney(1234)).toContain('12.34')
  })

  it('reports websocket connection state', () => {
    expect(connectionLabel(true)).toBe('Live channel connected')
    expect(connectionLabel(false)).toBe('Live channel reconnecting')
  })
})
