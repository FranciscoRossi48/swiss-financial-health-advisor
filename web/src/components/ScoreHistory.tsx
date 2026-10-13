import { TrendingDown, TrendingUp } from 'lucide-react'
import type { ScorePoint } from '../api'
import { formatMonth } from '../format'

export const HATCH = 'repeating-linear-gradient(135deg, #f3f6f4 0 4px, #e9efec 4px 8px)'

const HEALTHY_FROM = 60
const TREND_MONTHS = 5

function linePoints(values: number[], width: number, height: number, low: number, high: number) {
  return values.map((value, index) => {
    const x = values.length === 1 ? width : (index / (values.length - 1)) * width
    const y = height - ((value - low) / (high - low)) * height
    return `${x.toFixed(1)},${y.toFixed(1)}`
  })
}

/** Score change over the last few months, e.g. "+4 since Jul". */
function scoreTrend(history: ScorePoint[]) {
  if (history.length < 2) return null
  const from = history[Math.max(0, history.length - 1 - TREND_MONTHS)]
  const delta = Math.round(history[history.length - 1].score - from.score)
  return { delta, since: formatMonth(from.month, 'short') }
}

export function TrendChip({ history, showSince = true }: { history: ScorePoint[]; showSince?: boolean }) {
  const trend = scoreTrend(history)
  if (!trend) return null
  const down = trend.delta < 0
  const Icon = down ? TrendingDown : TrendingUp
  return (
    <span
      className={`inline-flex items-center gap-[3px] rounded-full bg-canvas px-2 py-1 text-xs font-bold ${
        down ? 'text-danger' : 'text-mint-deep'
      }`}
    >
      <Icon size={13} />
      {trend.delta > 0 ? '+' : ''}
      {trend.delta}
      {showSince && ` since ${trend.since}`}
    </span>
  )
}

/** Small score sparkline for the Home health card. */
export function Sparkline({ history }: { history: ScorePoint[] }) {
  const scores = history.map((p) => p.score)
  const low = Math.min(...scores) - 3
  const high = Math.max(...scores) + 3
  const points = linePoints(scores, 200, 32, low, high)
  return (
    <svg viewBox="0 0 200 36" preserveAspectRatio="none" className="mt-2 block h-[30px] w-full" aria-hidden="true">
      <path d={`M0,36 L${points.join(' L')} L200,36 Z`} fill="var(--color-mint-soft)" />
      <polyline
        points={points.join(' ')}
        fill="none"
        stroke="var(--color-mint)"
        strokeWidth={2}
        strokeLinejoin="round"
        strokeLinecap="round"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  )
}

/** Full-width score history with the "healthy" threshold marked. */
export function ScoreHistoryChart({ history }: { history: ScorePoint[] }) {
  const scores = history.map((p) => p.score)
  const low = Math.max(0, Math.min(...scores, HEALTHY_FROM) - 8)
  const high = Math.min(100, Math.max(...scores, HEALTHY_FROM) + 8)
  const points = linePoints(scores, 300, 60, low, high)
  const thresholdY = 60 - ((HEALTHY_FROM - low) / (high - low)) * 60
  const first = history[0]
  const last = history[history.length - 1]

  return (
    <div className="mt-4">
      <svg
        viewBox="0 0 300 64"
        preserveAspectRatio="none"
        className="block h-16 w-full"
        role="img"
        aria-label={`Score went from ${Math.round(first.score)} to ${Math.round(last.score)}`}
      >
        <line x1={0} x2={300} y1={thresholdY} y2={thresholdY} stroke="var(--color-line)" strokeDasharray="3 3" />
        <path d={`M0,64 L${points.join(' L')} L300,64 Z`} fill="var(--color-mint-soft)" />
        <polyline
          points={points.join(' ')}
          fill="none"
          stroke="var(--color-mint)"
          strokeWidth={2.5}
          strokeLinejoin="round"
          strokeLinecap="round"
          vectorEffect="non-scaling-stroke"
        />
      </svg>
      <div className="mt-1 flex justify-between text-[10px] font-semibold text-muted">
        <span>{formatMonth(first.month, 'short')} {first.month.slice(0, 4)}</span>
        <span>Healthy from {HEALTHY_FROM}</span>
        <span>{formatMonth(last.month, 'short')}</span>
      </div>
    </div>
  )
}
