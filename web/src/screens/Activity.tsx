import { useMemo, useState } from 'react'
import { api, type TransactionType } from '../api'
import { Card, ErrorState, SectionTitle, Skeleton } from '../components/ui'
import { TransactionList } from '../components/TransactionList'
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
  const months = useMemo(() => monthly.data?.map((m) => m.month).reverse() ?? [], [monthly.data])
  const [month, setMonth] = useState<string | null>(null)
  const [filter, setFilter] = useState<TransactionType | 'all'>('all')

  const selectedMonth = month ?? months[0] ?? null
  const transactions = useApi(selectedMonth ? `tx:${userId}:${selectedMonth}` : null, () =>
    api.transactions(userId, { month: selectedMonth!, limit: 500 }),
  )

  if (monthly.error) return <ErrorState error={monthly.error} />

  const summary = monthly.data?.find((m) => m.month === selectedMonth)
  const visible = transactions.data?.filter((tx) => filter === 'all' || tx.transaction_type === filter) ?? []

  return (
    <div className="space-y-4">
      <div className="no-scrollbar -mx-4 flex gap-2 overflow-x-auto px-4">
        {months.length === 0 && <Skeleton className="h-9 w-full" />}
        {months.map((m) => (
          <button
            key={m}
            type="button"
            onClick={() => setMonth(m)}
            className={`shrink-0 rounded-full px-4 py-2 text-sm font-bold transition-colors ${
              m === selectedMonth ? 'bg-ink text-white' : 'bg-white text-muted hover:text-ink'
            }`}
          >
            {formatMonth(m, 'short')}
          </button>
        ))}
      </div>

      <Card className="rise">
        <p className="text-xs font-bold uppercase tracking-wide text-muted">
          {selectedMonth ? formatMonth(selectedMonth) : '…'}
        </p>
        {summary ? (
          <>
            <div className="mt-3 grid grid-cols-3 gap-2 text-center">
              <Stat label="In" value={`+${formatCHFRounded(summary.income)}`} className="text-mint-deep" />
              <Stat label="Spent" value={`−${formatCHFRounded(summary.expense)}`} />
              <Stat label="Saved" value={formatCHFRounded(summary.savings)} />
            </div>
            <p className="mt-4 rounded-2xl bg-canvas px-3 py-2.5 text-sm">
              {summary.net_cashflow >= 0 ? 'You kept ' : 'You overspent by '}
              <span className={`tabular font-bold ${summary.net_cashflow >= 0 ? 'text-mint-deep' : 'text-danger'}`}>
                {formatCHFRounded(Math.abs(summary.net_cashflow))}
              </span>
              {' after spending and saving.'}
            </p>
          </>
        ) : (
          <Skeleton className="mt-3 h-24" />
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

function Stat({ label, value, className = '' }: { label: string; value: string; className?: string }) {
  return (
    <div>
      <p className="text-xs font-semibold text-muted">{label}</p>
      <p className={`tabular mt-0.5 text-[15px] font-extrabold ${className}`}>{value}</p>
    </div>
  )
}
