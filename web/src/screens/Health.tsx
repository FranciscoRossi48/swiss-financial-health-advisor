import { Info, Users } from 'lucide-react'
import { api, type ScoreBreakdown } from '../api'
import { CashflowChart } from '../components/CashflowChart'
import { ScoreRing } from '../components/ScoreRing'
import { Card, Chip, ErrorState, ProgressBar, SectionTitle, Skeleton } from '../components/ui'
import { bandTone, formatPercent, scoreTone, titleCase } from '../format'
import { useApi } from '../useApi'

const BAND_COPY: Record<string, string> = {
  strong: 'Your finances are in great shape. Keep your habits steady and plan ahead.',
  healthy: 'You are on solid ground, with a few areas that could still get stronger.',
  fragile: 'You are getting by, but an unexpected expense could put pressure on you.',
  critical: 'Your finances are under strain right now. Small, focused changes can make a real difference.',
}

export function Health({ userId }: { userId: string }) {
  const health = useApi(`health:${userId}`, () => api.health(userId))
  const monthly = useApi(`monthly:${userId}`, () => api.monthly(userId))

  if (health.error) return <ErrorState error={health.error} />
  if (!health.data) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-72" />
        <Skeleton className="h-64" />
      </div>
    )
  }

  const { financial_health: fh, credit_readiness: cr, segment } = health.data

  return (
    <div className="space-y-4">
      <Card className="rise flex flex-col items-center text-center">
        <p className="text-xs font-bold uppercase tracking-wide text-muted">Financial health index</p>
        <div className="mt-4">
          <ScoreRing score={fh.score} tone={bandTone(fh.band)} />
        </div>
        <div className="mt-4">
          <Chip tone={bandTone(fh.band)}>{titleCase(fh.band)}</Chip>
        </div>
        <p className="mt-3 max-w-[30ch] text-sm text-muted">{BAND_COPY[fh.band]}</p>
      </Card>

      <Card className="rise">
        <SectionTitle>What shapes your score</SectionTitle>
        <DimensionList breakdown={fh} />
      </Card>

      <Card className="rise">
        <p className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-muted">
          <Users size={14} /> Your money profile
        </p>
        <p className="mt-1.5 text-xl font-extrabold tracking-tight">{segment.label}</p>
        <p className="mt-1 text-sm text-muted">{segment.description}</p>
        <div className="mt-4 space-y-3">
          {segment.comparison.map((c) => {
            const max = Math.max(c.user_value, c.segment_value, 0.0001)
            return (
              <div key={c.metric}>
                <p className="text-sm font-semibold">{c.label}</p>
                <div className="mt-1.5 grid grid-cols-[52px_1fr_44px] items-center gap-2 text-xs">
                  <span className="font-bold">You</span>
                  <ProgressBar value={(c.user_value / max) * 100} tone="good" />
                  <span className="tabular text-right font-bold">{formatPercent(c.user_value)}</span>
                  <span className="text-muted">Similar</span>
                  <ProgressBar value={(c.segment_value / max) * 100} tone="info" />
                  <span className="tabular text-right text-muted">{formatPercent(c.segment_value)}</span>
                </div>
              </div>
            )
          })}
        </div>
        <p className="mt-4 text-xs text-muted">"Similar" is the average of customers in the same profile.</p>
      </Card>

      <Card className="rise">
        <SectionTitle>Credit readiness</SectionTitle>
        <div className="flex items-center gap-4">
          <ScoreRing score={cr.score} tone={bandTone(cr.band)} size={92} stroke={9} label="" />
          <div>
            <Chip tone={bandTone(cr.band)}>{titleCase(cr.band)}</Chip>
            <p className="mt-2 text-sm text-muted">How well a new loan would fit your finances today.</p>
          </div>
        </div>
        <div className="mt-5">
          <DimensionList breakdown={cr} />
        </div>
      </Card>

      <Card className="rise">
        <SectionTitle>Left over each month</SectionTitle>
        {monthly.data ? <CashflowChart months={monthly.data} /> : <Skeleton className="h-36" />}
      </Card>

      <p className="flex gap-2 px-1 text-xs text-muted">
        <Info size={14} className="mt-0.5 shrink-0" />
        Scores are calculated from your last 12 months of activity with a transparent, weighted formula. They are
        guidance, not a credit decision.
      </p>
    </div>
  )
}

function DimensionList({ breakdown }: { breakdown: ScoreBreakdown }) {
  return (
    <ul className="space-y-3.5">
      {breakdown.dimensions.map((d) => (
        <li key={d.key}>
          <div className="flex items-baseline justify-between text-sm">
            <span className="font-semibold">
              {d.label} <span className="text-xs font-medium text-muted">· {formatPercent(d.weight)} weight</span>
            </span>
            <span className="tabular font-bold">{Math.round(d.score)}</span>
          </div>
          <ProgressBar value={d.score} tone={scoreTone(d.score)} className="mt-1.5" />
        </li>
      ))}
    </ul>
  )
}
