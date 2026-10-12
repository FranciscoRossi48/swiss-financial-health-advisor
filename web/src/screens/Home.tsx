import { ArrowRight, Sparkles, TrendingDown, TrendingUp } from 'lucide-react'
import { api } from '../api'
import { Card, Chip, ErrorState, ProgressBar, SectionTitle, Skeleton } from '../components/ui'
import { CategoryIcon } from '../components/CategoryIcon'
import { ScoreRing } from '../components/ScoreRing'
import { TransactionList } from '../components/TransactionList'
import type { Tab } from '../components/TabBar'
import { bandTone, formatCHF, formatCHFRounded, formatMonth, formatPercent, titleCase } from '../format'
import { useApi } from '../useApi'

export function Home({ userId, onNavigate }: { userId: string; onNavigate: (tab: Tab) => void }) {
  const overview = useApi(`overview:${userId}`, () => api.overview(userId))
  const user = useApi(`user:${userId}`, () => api.user(userId))
  const recommendation = useApi(`rec:${userId}`, () => api.recommendation(userId))
  const recent = useApi(`tx:${userId}:recent`, () => api.transactions(userId, { limit: 5 }))

  if (overview.error) return <ErrorState error={overview.error} />

  const o = overview.data
  const spendingDelta = o && o.previous_month_spending ? o.month_spending / o.previous_month_spending - 1 : 0
  const topCategories = o?.spending_by_category.slice(0, 4) ?? []
  const maxCategory = topCategories[0]?.amount_chf ?? 1

  return (
    <div className="space-y-4">
      <section className="rise relative overflow-hidden rounded-3xl bg-ink p-5 text-white">
        <div className="pointer-events-none absolute -right-16 -top-20 h-56 w-56 rounded-full bg-mint/25 blur-3xl" />
        <p className="text-sm font-semibold text-white/60">Main account · CHF</p>
        {o ? (
          <p className="tabular mt-1 text-[34px] font-extrabold tracking-tight">{formatCHF(o.balance_chf)}</p>
        ) : (
          <Skeleton className="mt-2 h-10 w-48 bg-white/10" />
        )}
        <div className="mt-5 grid grid-cols-2 gap-3">
          <div className="rounded-2xl bg-white/[0.07] p-3">
            <p className="text-xs font-semibold text-white/60">Money in</p>
            <p className="tabular mt-0.5 font-bold text-mint">{o ? `+${formatCHFRounded(o.month_income)}` : '…'}</p>
          </div>
          <div className="rounded-2xl bg-white/[0.07] p-3">
            <p className="text-xs font-semibold text-white/60">Spent</p>
            <p className="tabular mt-0.5 font-bold">{o ? `−${formatCHFRounded(o.month_spending)}` : '…'}</p>
          </div>
        </div>
        {o && <p className="mt-3 text-xs text-white/50">{formatMonth(o.month)}</p>}
      </section>

      <button type="button" onClick={() => onNavigate('health')} className="rise block w-full text-left">
        <Card className="flex items-center gap-4 transition-transform active:scale-[0.99]">
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
              <>
                <div className="mt-1.5 flex flex-wrap gap-1.5">
                  <Chip tone={bandTone(user.data.health_band)}>{titleCase(user.data.health_band)}</Chip>
                  <Chip tone="info">{user.data.segment_label}</Chip>
                </div>
                <p className="mt-2 flex items-center gap-1 text-sm font-bold">
                  See what's behind it <ArrowRight size={15} />
                </p>
              </>
            ) : (
              <Skeleton className="mt-2 h-12 w-full" />
            )}
          </div>
        </Card>
      </button>

      {recommendation.data && (
        <button type="button" onClick={() => onNavigate('coach')} className="rise block w-full text-left">
          <Card className="border border-mint/40 bg-gradient-to-br from-mint-soft to-white">
            <p className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-mint-deep">
              <Sparkles size={14} /> Your coach suggests
            </p>
            <p className="mt-2 text-[15px] font-semibold leading-snug">{recommendation.data.recommendation}</p>
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
                    <span className="font-semibold">{c.category_label}</span>
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
