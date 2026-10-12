import { TONE_CLASSES, type Tone } from '../format'

interface ScoreRingProps {
  score: number
  tone: Tone
  size?: number
  stroke?: number
  label?: string
  dark?: boolean
}

export function ScoreRing({ score, tone, size = 168, stroke = 14, label = 'of 100', dark = false }: ScoreRingProps) {
  const radius = (size - stroke) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference * (1 - Math.max(0, Math.min(100, score)) / 100)

  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={dark ? 'rgba(255,255,255,0.12)' : 'var(--color-canvas)'}
          strokeWidth={stroke}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={TONE_CLASSES[tone].stroke}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 0.9s cubic-bezier(0.2, 0.8, 0.2, 1)' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span
          className={`tabular font-extrabold tracking-tight ${dark ? 'text-white' : 'text-ink'}`}
          style={{ fontSize: size * 0.28, lineHeight: 1 }}
        >
          {Math.round(score)}
        </span>
        {label && (
          <span className={`mt-1 font-semibold ${dark ? 'text-white/60' : 'text-muted'}`} style={{ fontSize: Math.max(10, size * 0.075) }}>
            {label}
          </span>
        )}
      </div>
    </div>
  )
}
