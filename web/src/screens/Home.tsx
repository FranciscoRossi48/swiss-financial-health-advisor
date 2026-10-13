import { ArrowRight, Sparkles, TrendingDown, TrendingUp } from 'lucide-react'
import type { AccountOverview } from '../api'
import { api } from '../api'
import { CategoryIcon } from '../components/CategoryIcon'
import { ScoreRing } from '../components/ScoreRing'
import { Sparkline, TrendChip } from '../components/ScoreHistory'
import type { Tab } from '../components/TabBar'
import { TransactionList } from '../components/TransactionList'
import { Card, Chip, ErrorState, ProgressBar, SectionTitle, Skeleton } from '../components/ui'
import { biggestLever, dimensionLabel, formatPoints } from '../dimensions'
import { bandTone, formatCHF, formatCHFRounded, formatMonth, formatPercent, titleCase } from '../format'
import { useApi } from '../useApi'
import { usePlanProgress } from '../usePlanProgress'

const plain = new Intl.NumberFormat('de-CH', { maximumFractionDigits: 0 })

export function Home({ userId, onNavigate }: { userId: string; onNavigate: (tab: Tab) => void }) {
  const overview = useApi(`overview:${userId}`, () => api.overview(userId))
  const user = useApi(`user:${userId}`, () => api.user(userId))
  const health = useApi(`health:${userId}`, () => api.health(userId))
  const history = useApi(`history:${userId}`, () => api.healthHistory(userId))
  const recommendation = useApi(`rec:${userId}`, () => api.recommendation(userId))
  const recent = useApi(`tx:${userId}:recent`, () => api.transactions(userId, { limit: 5 }))
  const plan = usePlanProgress(userId)

  if (overview.error) return <ErrorState error={overview.error} />

  const o = overview.data
  const spendingDelta = o && o.previous_month_spending ? o.month_spending / o.previous_month_spending - 1 : 0
  const topCategories = o?.spending_by_category.slice(0, 4) ?? []
  const maxCategory = topCategories[0]?.amount_chf ?? 1
  const lever = health.data && biggestLever(health.data.financial_health.dimensions)
  const planPoints = recommendation.data?.steps.reduce((sum, step) => sum + step.points, 0) ?? 0
  const stepCount = recommendation.data?.steps.length ?? 3

  return (
    <div className="space-y-4">
      <BalanceCard overview={o} />

      <button type="button" onClick={() => onNavigate('health')} className="rise block w-full text-left">
        <Card className="transition-transform active:scale-[0.99]">
          <div className="flex items-center gap-4">
            {user.data ? (
              <ScoreRing
                score={user.data.financial_health_score}
                tone={bandTone(user.data.health_band)}
                size={84}
                stroke={9}
                label=""
              />
            ) : (
              <Skeleton className="h-[84px] w-[84px] rounded-full" />
            )}
            <div className="min-w-0 flex-1">
              <p className="text-xs font-bold uppercase tracking-wide text-muted">Financial health</p>
              {user.data ? (
                <div className="mt-1.5 flex flex-wrap gap-1.5">
                  <Chip tone={bandTone(user.data.health_band)}>{titleCase(user.data.health_band)}</Chip>
                  {history.data && <TrendChip history={history.data} />}
                </div>
              ) : (
                <Skeleton className="mt-2 h-6 w-32" />
              )}
              {history.data ? <Sparkline history={history.data} /> : <Skeleton className="mt-2 h-[30px]" />}
            </div>
          </div>
          <div className="mt-3.5 flex items-center justify-between gap-2 border-t border-line pt-3">
            <p className="text-[13px] leading-[18px] text-muted">
              {lever && lever.points_left > 0 ? (
                <>
                  Biggest lever: <span className="font-bold text-ink">{dimensionLabel(lever)}</span> ·{' '}
                  {formatPoints(lever.points_left)} pts left to earn
                </>
              ) : lever ? (
                'Every part of your score is at full points.'
              ) : (
                'See what is behind your score'
              )}
            </p>
            <ArrowRight size={16} className="shrink-0" />
          </div>
        </Card>
      </button>

      {recommendation.data && (
        <button type="button" onClick={() => onNavigate('coach')} className="rise block w-full text-left">
          <Card className="border border-mint/40 bg-gradient-to-br from-mint-soft to-white">
            <div className="flex items-center justify-between gap-2">
              <p className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-mint-deep">
                <Sparkles size={14} /> Your coach suggests
              </p>
              {planPoints > 0 && (
                <span className="rounded-full bg-ink px-2 py-[3px] text-xs font-extrabold text-mint">
                  up to +{planPoints} pts
                </span>
              )}
            </div>
            <p className="mt-2 text-[15px] font-semibold leading-snug">{recommendation.data.recommendation}</p>
            <div className="mt-3 flex items-center gap-2.5">
              <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-ink/8">
                <div
                  className="h-full rounded-full bg-mint-deep transition-[width] duration-500"
                  style={{ width: `${(plan.doneCount / stepCount) * 100}%` }}
                />
              </div>
              <span className="tabular text-xs font-bold">
                {plan.doneCount} of {stepCount} steps
              </span>
            </div>
          </Card>
        </button>
      )}

      <Card className="rise">
        <SectionTitle
          action={
            o && (
              <span
                className={`flex items-center gap-1 text-xs font-bold ${spendingDelta > 0 ? 'text-danger' : 'text-mint-deep'}`}
              >
                {spendingDelta > 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                {formatPercent(Math.abs(spendingDelta))} vs last month
              </span>
            )
          }
        >
          Where your money went
        </SectionTitle>
        {o ? (
          <ul className="space-y-3">
            {topCategories.map((c) => (
              <li key={c.category} className="flex items-center gap-3">
                <CategoryIcon category={c.category} size={34} />
                <div className="flex-1">
                  <div className="flex justify-between text-sm">
                    <span className="font-semibold">
                      {c.category_label}{' '}
                      <span className="text-xs font-medium text-muted">
                        · {formatPercent(o.month_spending ? c.amount_chf / o.month_spending : 0)}
                      </span>
                    </span>
                    <span className="tabular font-bold">{formatCHFRounded(c.amount_chf)}</span>
                  </div>
                  <ProgressBar value={(c.amount_chf / maxCategory) * 100} tone="good" className="mt-1.5" />
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <Skeleton className="h-36" />
        )}
      </Card>

      <Card className="rise">
        <SectionTitle
          action={
            <button type="button" onClick={() => onNavigate('activity')} className="text-sm font-bold text-mint-deep">
              See all
            </button>
          }
        >
          Recent activity
        </SectionTitle>
        {recent.data ? <TransactionList transactions={recent.data} grouped={false} /> : <Skeleton className="h-60" />}
      </Card>
    </div>
  )
}

function BalanceCard({ overview: o }: { overview: AccountOverview | undefined }) {
  const leftOver = o ? o.month_income - o.month_spending - o.month_savings : 0
  const parts = o
    ? [
        { label: 'Spent', value: o.month_spending, color: 'rgba(255,255,255,0.85)' },
        { label: 'Saved', value: o.month_savings, color: '#7fe9c4' },
        { label: 'Left over', value: leftOver, color: 'var(--color-mint)' },
      ]
    : []

  return (
    <section className="rise relative overflow-hidden rounded-3xl bg-ink p-5 text-white">
      <div className="pointer-events-none absolute -right-16 -top-20 h-56 w-56 rounded-full bg-mint/25 blur-3xl" />
      <p className="relative text-sm font-semibold text-white/60">Main account · CHF</p>
      {o ? (
        <p className="tabular relative mt-1 text-[34px] font-extrabold tracking-tight">{formatCHF(o.balance_chf)}</p>
      ) : (
        <Skeleton className="mt-2 h-10 w-48 bg-white/10" />
      )}
      {o ? (
        <>
          <div
            className="relative mt-4 flex h-2 gap-[3px] overflow-hidden rounded-full"
            role="img"
            aria-label={`Of CHF ${plain.format(o.month_income)} in: ${parts
              .map((p) => `${p.label.toLowerCase()} CHF ${plain.format(p.value)}`)
              .join(', ')}`}
          >
            {parts.map((p) => (
              <div key={p.label} style={{ flex: Math.max(0, p.value), background: p.color }} />
            ))}
          </div>
          <div className="relative mt-3 grid grid-cols-3 gap-2">
            {parts.map((p) => (
              <div key={p.label}>
                <p className="flex items-center gap-1.5 text-xs font-semibold text-white/60">
                  <span className="h-1.5 w-1.5 rounded-full" style={{ background: p.color }} />
                  {p.label}
                </p>
                <p
                  className={`tabular mt-0.5 font-bold ${
                    p.label === 'Left over' ? (p.value < 0 ? 'text-[#ff8a8d]' : 'text-mint') : ''
                  }`}
                >
                  {p.value < 0 ? '−' : ''}
                  {plain.format(Math.abs(p.value))}
                </p>
              </div>
            ))}
          </div>
          <p className="relative mt-3.5 text-xs text-white/50">
            {formatMonth(o.month)} · of CHF {plain.format(o.month_income)} coming in
          </p>
        </>
      ) : (
        <Skeleton className="mt-4 h-16 bg-white/10" />
      )}
    </section>
  )
}
