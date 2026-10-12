import type { Transaction } from '../api'
import { formatDay, formatSigned } from '../format'
import { CategoryIcon } from './CategoryIcon'

function TransactionRow({ tx }: { tx: Transaction }) {
  return (
    <li className="flex items-center gap-3 py-2.5">
      <CategoryIcon category={tx.category} />
      <div className="min-w-0 flex-1">
        <p className="truncate text-[15px] font-semibold">{tx.merchant}</p>
        <p className="truncate text-xs text-muted">{tx.category_label}</p>
      </div>
      <span className={`tabular text-[15px] font-bold ${tx.amount_chf > 0 ? 'text-mint-deep' : 'text-ink'}`}>
        {formatSigned(tx.amount_chf)}
      </span>
    </li>
  )
}

export function TransactionList({ transactions, grouped = true }: { transactions: Transaction[]; grouped?: boolean }) {
  if (transactions.length === 0) {
    return <p className="py-6 text-center text-sm text-muted">No transactions here yet.</p>
  }
  if (!grouped) {
    return (
      <ul className="divide-y divide-line">
        {transactions.map((tx, index) => (
          <TransactionRow key={`${tx.date}-${tx.category}-${index}`} tx={tx} />
        ))}
      </ul>
    )
  }

  const groups = new Map<string, Transaction[]>()
  for (const tx of transactions) {
    groups.set(tx.date, [...(groups.get(tx.date) ?? []), tx])
  }

  return (
    <div className="space-y-4">
      {[...groups].map(([date, items]) => (
        <div key={date}>
          <p className="mb-1 text-xs font-bold uppercase tracking-wide text-muted">{formatDay(date)}</p>
          <ul className="divide-y divide-line">
            {items.map((tx, index) => (
              <TransactionRow key={`${date}-${tx.category}-${index}`} tx={tx} />
            ))}
          </ul>
        </div>
      ))}
    </div>
  )
}
