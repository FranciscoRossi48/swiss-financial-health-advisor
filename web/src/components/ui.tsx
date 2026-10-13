import type { ReactNode } from 'react'
import { TONE_CLASSES, type Tone } from '../format'

export function Card({
  children,
  className = '',
  padding = 'p-5',
}: {
  children: ReactNode
  className?: string
  padding?: string
}) {
  return (
    <section className={`rounded-3xl bg-white shadow-[0_1px_2px_rgba(12,26,23,0.04)] ${padding} ${className}`}>
      {children}
    </section>
  )
}

export function SectionTitle({ children, action }: { children: ReactNode; action?: ReactNode }) {
  return (
    <div className="mb-3 flex items-baseline justify-between">
      <h2 className="text-[15px] font-bold tracking-tight">{children}</h2>
      {action}
    </div>
  )
}

export function Chip({ tone, children }: { tone: Tone; children: ReactNode }) {
  const classes = TONE_CLASSES[tone]
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-bold ${classes.bg} ${classes.text}`}>
      {children}
    </span>
  )
}

export function ProgressBar({ value, tone, className = '' }: { value: number; tone: Tone; className?: string }) {
  return (
    <div className={`h-2 overflow-hidden rounded-full bg-canvas ${className}`}>
      <div
        className={`h-full rounded-full transition-[width] duration-700 ${TONE_CLASSES[tone].fill}`}
        style={{ width: `${Math.max(2, Math.min(100, value))}%` }}
      />
    </div>
  )
}

export function Skeleton({ className = '' }: { className?: string }) {
  return <div className={`animate-pulse rounded-2xl bg-line/70 ${className}`} />
}

export function ErrorState({ error }: { error: Error }) {
  return (
    <Card className="text-sm">
      <p className="font-bold">We couldn't load this right now.</p>
      <p className="mt-1 text-muted">Make sure the Pulse API is running (uvicorn app.api:app --port 8000).</p>
      <p className="mt-2 font-mono text-xs text-muted">{error.message}</p>
    </Card>
  )
}
