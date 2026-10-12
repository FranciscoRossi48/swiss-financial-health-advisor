const chf = new Intl.NumberFormat('de-CH', { style: 'currency', currency: 'CHF' })
const chfRounded = new Intl.NumberFormat('de-CH', {
  style: 'currency',
  currency: 'CHF',
  maximumFractionDigits: 0,
})

export const formatCHF = (value: number) => chf.format(value)
export const formatCHFRounded = (value: number) => chfRounded.format(value)
export const formatSigned = (value: number) => `${value > 0 ? '+' : value < 0 ? '−' : ''}${chf.format(Math.abs(value))}`
export const formatPercent = (value: number, digits = 0) => `${(value * 100).toFixed(digits)}%`

export const formatMonth = (month: string, style: 'long' | 'short' = 'long') =>
  new Date(`${month}-01T00:00:00`).toLocaleDateString('en-GB', {
    month: style,
    year: style === 'long' ? 'numeric' : undefined,
  })

export const formatDay = (date: string) =>
  new Date(`${date}T00:00:00`).toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' })

export const titleCase = (value: string) => value.charAt(0).toUpperCase() + value.slice(1)

// Synthetic customers only have ids; give each a stable fictional first name for the demo.
const FIRST_NAMES = [
  'Lena', 'Marco', 'Sofia', 'Jonas', 'Elif', 'Noah', 'Chiara', 'Luca', 'Mia', 'David', 'Nora', 'Samir',
  'Anja', 'Matteo', 'Leonie', 'Yannick', 'Sara', 'Elias', 'Laura', 'Nico', 'Alina', 'Tim', 'Giulia', 'Reto',
]

export function personaName(userId: string) {
  const number = Number(userId.replace(/\D/g, '')) || 0
  return FIRST_NAMES[number % FIRST_NAMES.length]
}

export type Tone = 'danger' | 'warn' | 'info' | 'good'

const BAND_TONES: Record<string, Tone> = {
  critical: 'danger',
  fragile: 'warn',
  healthy: 'good',
  strong: 'good',
  'not ready': 'danger',
  'needs improvement': 'warn',
  moderate: 'info',
  ready: 'good',
  high: 'danger',
  medium: 'warn',
  low: 'info',
  affordable: 'good',
  marginal: 'warn',
  'not recommended': 'danger',
}

export const bandTone = (band: string): Tone => BAND_TONES[band] ?? 'info'

export const scoreTone = (score: number): Tone =>
  score >= 60 ? 'good' : score >= 40 ? 'info' : score >= 25 ? 'warn' : 'danger'

export const TONE_CLASSES: Record<Tone, { text: string; bg: string; fill: string; stroke: string }> = {
  danger: { text: 'text-danger', bg: 'bg-danger-soft', fill: 'bg-danger', stroke: 'var(--color-danger)' },
  warn: { text: 'text-warn', bg: 'bg-warn-soft', fill: 'bg-warn', stroke: 'var(--color-warn)' },
  info: { text: 'text-info', bg: 'bg-info-soft', fill: 'bg-info', stroke: 'var(--color-info)' },
  good: { text: 'text-mint-deep', bg: 'bg-mint-soft', fill: 'bg-mint', stroke: 'var(--color-mint)' },
}
