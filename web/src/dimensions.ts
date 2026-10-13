import type { ScoreDimension } from './api'

// Customer-facing names for the Financial Health Score parts, keyed by API dimension key.
const NAMES: Record<string, { label: string; short: string }> = {
  liquidity_score: { label: 'Liquidity', short: 'Liquidity' },
  savings_score: { label: 'Savings capacity', short: 'Savings' },
  income_stability_score: { label: 'Income stability', short: 'Income' },
  debt_score: { label: 'Debt exposure', short: 'Debt' },
}

export const dimensionLabel = (d: ScoreDimension) => NAMES[d.key]?.label ?? d.label
export const dimensionShort = (d: ScoreDimension) => NAMES[d.key]?.short ?? d.label

/** Heaviest parts first, so the points bar reads from the biggest to the smallest share. */
export const byWeight = (dims: ScoreDimension[]) => [...dims].sort((a, b) => b.weight - a.weight)

/** The part with the most points still to earn. */
export const biggestLever = (dims: ScoreDimension[]) =>
  dims.reduce((best, d) => (d.points_left > best.points_left ? d : best), dims[0])

/** The lowest-scoring part. */
export const weakest = (dims: ScoreDimension[]) => dims.reduce((low, d) => (d.score < low.score ? d : low), dims[0])

export const formatPoints = (points: number) => (Number.isInteger(points) ? `${points}` : points.toFixed(1))
