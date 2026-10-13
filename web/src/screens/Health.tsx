import { ChevronRight, Info, Target, Users } from 'lucide-react'
import { useState } from 'react'
import { api, type ScoreBreakdown } from '../api'
import { HEALTH_EXPLAINER } from '../config'
import { ScoreHistoryChart, HATCH, TrendChip } from '../components/ScoreHistory'
import { ScoreRing } from '../components/ScoreRing'
import type { Tab } from '../components/TabBar'
import { Card, Chip, ErrorState, ProgressBar, SectionTitle, Skeleton } from '../components/ui'
import { byWeight, dimensionLabel, dimensionShort, formatPoints, weakest } from '../dimensions'
import { bandTone, formatPercent, scoreTone, TONE_CLASSES, titleCase } from '../format'
import { useApi } from '../useApi'

const BAND_COPY: Record<string, string> = {
  strong: 'In great shape. Keep your habits steady and plan ahead.',
  healthy: 'Solid ground, with a few areas that could still get stronger.',
  fragile: 'Getting by, but a surprise expense could put pressure on you.',
  critical: 'Under strain right now. Small, focused changes make a real difference.',
}

export function Health({ userId, onNavigate }: { userId: string; onNavigate: (tab: Tab) => void }) {
  const health = useApi(`health:${userId}`, () => api.health(userId))
  const history = useApi(`history:${userId}`, () => api.healthHistory(userId))
  const demoUsers = useApi('demo-users', api.demoUsers)

  if (health.error) return <ErrorState error={health.error} />
  if (!health.data) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-64" />
        <Skeleton className="h-72" />
      </div>
    )
  }

  const { financial_health: fh, credit_readiness: cr, segment } = health.data
  const segments = demoUsers.data?.map((u) => u.segment_label) ?? []
  const holdingBack = weakest(cr.dimensions)

  return (
    <div className="space-y-4">
      <Card className="rise">
        <div className="flex items-center gap-[18px]">
          <ScoreRing score={fh.score} tone={bandTone(fh.band)} size={128} stroke={12} />
          <div className="min-w-0">
            <p className="text-xs font-bold uppercase tracking-wide text-muted">Financial health index</p>
            <div className="mt-1.5 flex flex-wrap gap-1.5">
              <Chip tone={bandTone(fh.band)}>{titleCase(fh.band)}</Chip>
              {history.data && <TrendChip history={history.data} showSince={false} />}
            </div>
            <p className="mt-2 text-[13px] leading-[18px] text-muted">{BAND_COPY[fh.band]}</p>
          </div>
        </div>
        {history.data ? <ScoreHistoryChart history={history.data} /> : <Skeleton className="mt-4 h-20" />}
      </Card>

      <ScoreExplainer breakdown={fh} />

      <Card className="rise">
        <p className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-muted">
          <Users size={14} /> Your money profile
        </p>
        <p className="mt-1.5 text-xl font-extrabold tracking-tight">{segment.label}</p>
        <p className="mt-1 text-sm text-muted">{segment.description}</p>
        {segments.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {segments.map((label) => (
              <span
                key={label}
                className={`rounded-full px-2.5 py-1 text-xs font-bold ${
                  label === segment.label ? 'bg-ink text-white' : 'bg-canvas text-muted'
                }`}
              >
                {label}
              </span>
            ))}
          </div>
        )}
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

      <button type="button" onClick={() => onNavigate('coach')} className="rise block w-full text-left">
        <Card padding="px-5 py-4" className="flex items-center gap-3.5 transition-transform active:scale-[0.99]">
          <ScoreRing score={cr.score} tone={bandTone(cr.band)} size={56} stroke={7} label="" />
          <div className="min-w-0 flex-1">
            <p className="text-[15px] font-bold tracking-tight">
              Credit readiness · <span className={TONE_CLASSES[bandTone(cr.band)].text}>{titleCase(cr.band)}</span>
            </p>
            <p className="mt-0.5 text-[13px] leading-[18px] text-muted">
              {holdingBack.score >= 80
                ? 'Nothing is holding it back.'
                : `Held back by ${holdingBack.label.toLowerCase()}.`}{' '}
              Try a loan in the simulator.
            </p>
          </div>
          <ChevronRight size={18} className="shrink-0" />
        </Card>
      </button>

      <p className="flex gap-2 px-1 text-xs text-muted">
        <Info size={14} className="mt-0.5 shrink-0" />
        Scores are calculated from your last 12 months of activity with a transparent, weighted formula. They are
        guidance, not a credit decision.
      </p>
    </div>
  )
}

function ScoreExplainer({ breakdown }: { breakdown: ScoreBreakdown }) {
  const dims = byWeight(breakdown.dimensions)
  const [open, setOpen] = useState<string | null>(() => weakest(dims).key)
  const showPointsBar = HEALTH_EXPLAINER === 'points'

  return (
    <Card className="rise">
      <SectionTitle action={<span className="text-xs font-bold text-muted">Tap a part</span>}>
        How your {Math.round(breakdown.score)} adds up
      </SectionTitle>
      <p className="-mt-2 text-[13px] leading-[18px] text-muted">Each part can earn up to its weight in points.</p>

      {showPointsBar && (
        <>
          <div className="mt-3.5 flex h-7 gap-[3px]">
            {dims.map((d) => (
              <button
                key={d.key}
                type="button"
                title={dimensionLabel(d)}
                aria-label={`${dimensionLabel(d)}: ${formatPoints(d.points)} of ${d.weight * 100} points`}
                onClick={() => setOpen(open === d.key ? null : d.key)}
                className={`relative overflow-hidden rounded-lg outline-offset-2 ${
                  open === d.key ? 'outline-2 outline-ink' : ''
                }`}
                style={{ flex: d.weight * 100, background: HATCH }}
              >
                <span
                  className={`absolute inset-y-0 left-0 transition-[width] duration-700 ${TONE_CLASSES[scoreTone(d.score)].fill}`}
                  style={{ width: `${d.score}%` }}
                />
              </button>
            ))}
          </div>
          <div className="mt-1.5 flex gap-[3px]" aria-hidden="true">
            {dims.map((d) => (
              <span key={d.key} className="truncate text-[10px] font-bold text-muted" style={{ flex: d.weight * 100 }}>
                {dimensionShort(d)}
              </span>
            ))}
          </div>
        </>
      )}

      <ul className="mt-3.5 space-y-1.5">
        {dims.map((d) => {
          const isOpen = open === d.key
          return (
            <li key={d.key}>
              <button
                type="button"
                onClick={() => setOpen(isOpen ? null : d.key)}
                aria-expanded={isOpen}
                className={`block w-full rounded-2xl px-3 py-2.5 text-left transition-colors ${isOpen ? 'bg-canvas' : 'hover:bg-canvas/60'}`}
              >
                <div className="flex items-baseline justify-between text-sm">
                  <span className="font-semibold">{dimensionLabel(d)}</span>
                  <span className="tabular">
                    <span className="font-extrabold">{formatPoints(d.points)}</span>
                    <span className="text-xs text-muted"> / {d.weight * 100} pts</span>
                  </span>
                </div>
                {!showPointsBar && <ProgressBar value={d.score} tone={scoreTone(d.score)} className="mt-1.5" />}
                {isOpen && (
                  <div className="mt-2 space-y-1.5">
                    {d.driver && <p className="text-[13px] leading-[18px] text-ink">{d.driver}</p>}
                    {d.target && (
                      <p
                        className={`flex items-center gap-1.5 text-xs font-bold ${
                          d.score < 60 ? 'text-mint-deep' : 'text-muted'
                        }`}
                      >
                        <Target size={13} className="shrink-0" />
                        {d.target}
                      </p>
                    )}
                  </div>
                )}
              </button>
            </li>
          )
        })}
      </ul>
    </Card>
  )
}
