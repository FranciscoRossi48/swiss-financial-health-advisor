import { useEffect, useRef, useState } from 'react'
import { api } from './api'
import { Logo } from './components/Logo'
import { Avatar, PersonaPills, PersonaSheet } from './components/PersonaPicker'
import { TabBar, type Tab } from './components/TabBar'
import { Card, ErrorState, Skeleton } from './components/ui'
import { SHOW_CASE_STUDY } from './config'
import { personaName } from './format'
import { Activity } from './screens/Activity'
import { Coach } from './screens/Coach'
import { Health } from './screens/Health'
import { Home } from './screens/Home'
import { useApi } from './useApi'

const STORAGE_KEY = 'pulse:user'

const PIPELINE = [
  { title: 'Transactions', body: 'Synthetic Open Banking-style movements, validated.' },
  { title: 'Behaviour', body: 'Monthly features: cashflow, savings rate, debt-to-income, volatility.' },
  { title: 'Score + profile', body: 'Weighted 0–100 index and K-Means money profile.' },
  { title: 'Guidance', body: 'Rule-based plan aimed at the weakest dimension.' },
]

// From the README's Demo Metrics table.
const METRICS = [
  { value: '57k', label: 'transactions' },
  { value: '150', label: 'customers' },
  { value: '5', label: 'segments' },
  { value: '0.63', label: 'silhouette' },
]

const TITLES: Record<Exclude<Tab, 'home'>, string> = {
  activity: 'Activity',
  health: 'Your financial health',
  coach: 'Coach',
}

function readStoredUser() {
  try {
    return localStorage.getItem(STORAGE_KEY)
  } catch {
    return null
  }
}

export default function App() {
  const demoUsers = useApi('demo-users', api.demoUsers)
  const [userId, setUserId] = useState<string | null>(readStoredUser)
  const [tab, setTab] = useState<Tab>('home')
  const [sheetOpen, setSheetOpen] = useState(false)
  const scrollRef = useRef<HTMLElement>(null)

  // A remembered customer only counts if it is still one of the demo customers.
  const activeUser =
    demoUsers.data?.find((user) => user.user_id === userId)?.user_id ?? demoUsers.data?.[0]?.user_id ?? null

  const selectUser = (id: string) => {
    setUserId(id)
    try {
      localStorage.setItem(STORAGE_KEY, id)
    } catch {
      // storage is a convenience only
    }
  }

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: 0 })
  }, [tab, activeUser])

  const listProps = { users: demoUsers.data ?? [], selected: activeUser, onSelect: selectUser }

  return (
    <div className="min-h-full bg-canvas lg:flex lg:items-center lg:justify-center lg:gap-20 lg:bg-[radial-gradient(circle_at_20%_20%,#dcf7eb,transparent_45%),linear-gradient(#f3f6f4,#e9efec)] lg:p-10">
      <aside className="hidden w-[380px] lg:block">
        <Logo size={40} />
        <h1 className="mt-8 text-4xl font-extrabold leading-[1.1] tracking-tight">
          Your money,
          <br />
          and what it says about you.
        </h1>
        <p className="mt-3.5 text-muted">
          A banking-app prototype that turns raw transactions into an explainable health score, a money profile and
          a plan you can act on.
        </p>
        {SHOW_CASE_STUDY && <HowPulseThinks />}
        <p className="mb-2.5 mt-6 text-xs font-bold uppercase tracking-wide text-muted">Try a demo customer</p>
        {demoUsers.data ? <PersonaPills {...listProps} /> : <Skeleton className="h-20" />}
        <p className="mt-6 text-xs text-muted">
          Pulse is a fictional brand. All customers and transactions are synthetic. Data Science thesis project ·
          Universidad Siglo 21.
        </p>
      </aside>

      <div className="relative mx-auto flex h-[100dvh] w-full max-w-md flex-col overflow-hidden bg-canvas lg:mx-0 lg:h-[844px] lg:w-[390px] lg:max-w-none lg:rounded-[52px] lg:border-[10px] lg:border-ink lg:shadow-[0_40px_80px_-20px_rgba(12,26,23,0.35)]">
        <header className="flex items-center justify-between px-4 pb-3 pt-[max(16px,env(safe-area-inset-top))] lg:pt-7">
          {tab === 'home' ? (
            <div>
              <p className="text-sm font-semibold text-muted">Grüezi,</p>
              <p className="text-2xl font-extrabold tracking-tight">{activeUser ? personaName(activeUser) : '…'}</p>
            </div>
          ) : (
            <p className="text-2xl font-extrabold tracking-tight">{TITLES[tab]}</p>
          )}
          {activeUser && (
            <button
              type="button"
              onClick={() => setSheetOpen(true)}
              aria-label="Switch demo customer"
              className="rounded-full ring-4 ring-white transition-transform active:scale-95"
            >
              <Avatar userId={activeUser} size={40} />
            </button>
          )}
        </header>

        <main ref={scrollRef} className="no-scrollbar flex-1 overflow-y-auto px-4 pb-6">
          {demoUsers.error ? (
            <ErrorState error={demoUsers.error} />
          ) : activeUser ? (
            <div key={`${activeUser}-${tab}`}>
              {tab === 'home' && <Home userId={activeUser} onNavigate={setTab} />}
              {tab === 'activity' && <Activity userId={activeUser} />}
              {tab === 'health' && <Health userId={activeUser} onNavigate={setTab} />}
              {tab === 'coach' && <Coach userId={activeUser} />}
            </div>
          ) : (
            <div className="space-y-4">
              <Skeleton className="h-48" />
              <Skeleton className="h-32" />
            </div>
          )}
        </main>

        <TabBar active={tab} onChange={setTab} />
        <PersonaSheet open={sheetOpen} onClose={() => setSheetOpen(false)} {...listProps} />
      </div>
    </div>
  )
}

function HowPulseThinks() {
  return (
    <Card className="mt-7" padding="px-[18px] pb-4 pt-[18px]">
      <p className="text-xs font-bold uppercase tracking-wide text-muted">How Pulse thinks</p>
      <ol className="mt-3 space-y-2.5">
        {PIPELINE.map((step, index) => (
          <li key={step.title} className="grid grid-cols-[24px_1fr] items-start gap-2.5">
            <span className="tabular flex h-6 w-6 items-center justify-center rounded-lg bg-ink text-xs font-extrabold text-mint">
              {index + 1}
            </span>
            <span>
              <span className="block text-sm font-bold">{step.title}</span>
              <span className="block text-xs text-muted">{step.body}</span>
            </span>
          </li>
        ))}
      </ol>
      <div className="mt-3.5 grid grid-cols-4 gap-2 border-t border-line pt-3.5">
        {METRICS.map((metric) => (
          <div key={metric.label}>
            <p className="tabular text-[15px] font-extrabold tracking-tight">{metric.value}</p>
            <p className="text-[11px] leading-[14px] text-muted">{metric.label}</p>
          </div>
        ))}
      </div>
    </Card>
  )
}
