import type { MonthlySummary } from '../api'
import { formatCHFRounded, formatMonth } from '../format'

// Net cashflow per month: what was left after spending and savings transfers.
export function CashflowChart({ months }: { months: MonthlySummary[] }) {
  const width = 320
  const height = 140
  const top = 10
  const bottom = 22
  const max = Math.max(1, ...months.map((m) => Math.abs(m.net_cashflow)))
  const hasNegative = months.some((m) => m.net_cashflow < 0)
  const zeroY = hasNegative ? top + (height - top - bottom) / 2 : height - bottom
  const scale = (hasNegative ? (height - top - bottom) / 2 : height - top - bottom) / max
  const slot = width / months.length
  const barWidth = slot * 0.56

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="w-full" role="img" aria-label="Monthly net cashflow">
      <line x1={0} x2={width} y1={zeroY} y2={zeroY} stroke="var(--color-line)" strokeWidth={1} />
      {months.map((m, index) => {
        const barHeight = Math.max(2, Math.abs(m.net_cashflow) * scale)
        const positive = m.net_cashflow >= 0
        const x = index * slot + (slot - barWidth) / 2
        return (
          <g key={m.month}>
            <title>{`${formatMonth(m.month)}: ${formatCHFRounded(m.net_cashflow)}`}</title>
            <rect
              x={x}
              y={positive ? zeroY - barHeight : zeroY}
              width={barWidth}
              height={barHeight}
              rx={Math.min(4, barWidth / 2)}
              fill={positive ? 'var(--color-mint)' : 'var(--color-danger)'}
              opacity={index === months.length - 1 ? 1 : 0.75}
            />
            <text
              x={index * slot + slot / 2}
              y={height - 6}
              textAnchor="middle"
              fontSize="10"
              fontWeight={600}
              fill="var(--color-muted)"
            >
              {formatMonth(m.month, 'short').charAt(0)}
            </text>
          </g>
        )
      })}
    </svg>
  )
}
