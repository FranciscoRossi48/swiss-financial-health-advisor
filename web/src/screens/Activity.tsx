import { useState } from 'react'
import { api, type MonthlySummary, type TransactionType } from '../api'
import { TransactionList } from '../components/TransactionList'
import { Card, ErrorState, SectionTitle, Skeleton } from '../components/ui'
import { formatCHFRounded, formatMonth } from '../format'
import { useApi } from '../useApi'

const FILTERS: { id: TransactionType | 'all'; label: string }[] = [
  { id: 'all', label: 'All' },
  { id: 'income', label: 'Money in' },
  { id: 'expense', label: 'Spending' },
  { id: 'savings', label: 'Savings' },
]

export function Activity({ userId }: { userId: string }) {
  const monthly = useApi(`monthly:${userId}`, () => api.monthly(userId))
  const [month, setMonth] = useState<string | null>(null)
  const [filter, setFilter] = useState<TransactionType | 'all'>('all')

  const months = monthly.data ?? []
  const selectedMonth = month ?? months[months.length - 1]?.month ?? null
  const transactions = useApi(selectedMonth ? `tx:${userId}:${selectedMonth}` : null, () =>
    api.transactions(userId, { month: selectedMonth!, limit: 500 }),
  )

  if (monthly.error) return <ErrorState error={monthly.error} />

  const summary = months.find((m) => m.month === selectedMonth)
  const bestMonth = months.length ? Math.max(...months.map((m) => m.net_cashflow)) : null
  const visible = transactions.data?.filter((tx) => filter === 'all' || tx.transaction_type === filter) ?? []

  return (
    <div className="space-y-4">
      {monthly.data && selectedMonth ? (
        <LeftOverChart months={months} selected={selectedMonth} onSelect={setMonth} />
      ) : (
        <Skeleton className="h-36" />
      )}

      <Card className="rise">
        {summary ? (
          <>
            <div className="grid grid-cols-3 gap-2 text-center">
              <Stat label="In" value={`+${formatCHFRounded(summary.income)}`} className="text-mint-deep" />
              <Stat label="Spent" value={`−${formatCHFRounded(summary.expense)}`} />
              <Stat label="Saved" value={formatCHFRounded(summary.savings)} />
            </div>
            <p className="mt-4 rounded-2xl bg-canvas px-3 py-2.5 text-sm">
              {summary.net_cashflow >= 0 ? 'You kept ' : 'You overspent by '}
              <span className={`tabular font-bold ${summary.net_cashflow >= 0 ? 'text-mint-deep' : 'text-danger'}`}>
                {formatCHFRounded(Math.abs(summary.net_cashflow))}
              </span>
              {' after spending and saving'}
              {summary.net_cashflow === bestMonth && summary.net_cashflow > 0
                ? ' — your best month this year.'
                : '.'}
            </p>
          </>
        ) : (
          <Skeleton className="h-24" />
        )}
      </Card>

      <Card className="rise">
        <SectionTitle>Transactions</SectionTitle>
        <div className="mb-3 grid grid-cols-4 gap-1 rounded-2xl bg-canvas p-1">
          {FILTERS.map((f) => (
            <button
              key={f.id}
              type="button"
              onClick={() => setFilter(f.id)}
              className={`rounded-xl py-1.5 text-xs font-bold transition-colors ${
                filter === f.id ? 'bg-white text-ink shadow-sm' : 'text-muted'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
        {transactions.error ? (
          <ErrorState error={transactions.error} />
        ) : transactions.data ? (
          <TransactionList transactions={visible} />
        ) : (
          <Skeleton className="h-80" />
        )}
      </Card>
    </div>
  )
}

const CHART_HEIGHT = 84
const ZERO_LINE = 56

// Money left over after spending and saving, one bar per month. Tapping a bar selects that month.
function LeftOverChart({
  months,
  selected,
  onSelect,
}: {
  months: MonthlySummary[]
  selected: string
  onSelect: (month: string) => void
}) {
  const max = Math.max(1, ...months.map((m) => Math.abs(m.net_cashflow)))
  const year = selected.slice(0, 4)

  return (
    <Card className="rise" padding="p-4 pb-3">
      <div className="flex items-baseline justify-between">
        <p className="text-xs font-bold uppercase tracking-wide text-muted">Left over · {year}</p>
        <p className="text-xs font-bold text-mint-deep">{formatMonth(selected)}</p>
      </div>
      <div className="relative mt-2.5" style={{ height: CHART_HEIGHT }}>
        <div className="absolute inset-x-0 h-px bg-line" style={{ top: ZERO_LINE }} />
        <div className="absolute inset-0 grid" style={{ gridTemplateColumns: `repeat(${months.length}, 1fr)` }}>
          {months.map((m) => {
            const height = Math.max(2, (Math.abs(m.net_cashflow) / max) * (ZERO_LINE - 4))
            const positive = m.net_cashflow >= 0
            return (
              <button
                key={m.month}
                type="button"
                onClick={() => onSelect(m.month)}
                aria-label={`${formatMonth(m.month)}: ${formatCHFRounded(m.net_cashflow)} left over`}
                aria-pressed={m.month === selected}
                className="relative h-full"
              >
                <span
                  className={`absolute inset-x-[18%] rounded transition-opacity ${positive ? 'bg-mint' : 'bg-danger'}`}
                  style={{
                    top: positive ? ZERO_LINE - height : ZERO_LINE,
                    height: positive ? height : Math.min(height, CHART_HEIGHT - ZERO_LINE - 2),
                    opacity: m.month === selected ? 1 : 0.4,
                  }}
                />
              </button>
            )
          })}
        </div>
      </div>
      <div
        className="mt-1 grid text-center text-[10px] font-bold"
        style={{ gridTemplateColumns: `repeat(${months.length}, 1fr)` }}
        aria-hidden="true"
      >
        {months.map((m) => (
          <span key={m.month} className={m.month === selected ? 'text-ink' : 'text-muted'}>
            {formatMonth(m.month, 'short').charAt(0)}
          </span>
        ))}
      </div>
    </Card>
  )
}

function Stat({ label, value, className = '' }: { label: string; value: string; className?: string }) {
  return (
    <div>
      <p className="text-xs font-semibold text-muted">{label}</p>
      <p className={`tabular mt-0.5 text-[15px] font-extrabold ${className}`}>{value}</p>
    </div>
  )
}
