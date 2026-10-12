import { useEffect, useRef, useState } from 'react'
import { api } from './api'
import { Logo } from './components/Logo'
import { Avatar, PersonaList, PersonaSheet } from './components/PersonaPicker'
import { TabBar, type Tab } from './components/TabBar'
import { ErrorState, Skeleton } from './components/ui'
import { personaName } from './format'
import { Activity } from './screens/Activity'
import { Coach } from './screens/Coach'
import { Health } from './screens/Health'
import { Home } from './screens/Home'
import { useApi } from './useApi'

const STORAGE_KEY = 'pulse:user'

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
      <aside className="hidden w-[360px] lg:block">
        <Logo size={40} />
        <h1 className="mt-8 text-4xl font-extrabold leading-[1.1] tracking-tight">
          Your money,
          <br />
          and what it says about you.
        </h1>
        <p className="mt-4 text-muted">
          A banking-app prototype that pairs everyday account activity with an explainable financial health index,
          a behavioural money profile and personal guidance.
        </p>
        <p className="mb-3 mt-8 text-xs font-bold uppercase tracking-wide text-muted">Try a demo customer</p>
        {demoUsers.data ? <PersonaList {...listProps} /> : <Skeleton className="h-72" />}
        <p className="mt-8 text-xs text-muted">
          Pulse is a fictional brand. All customers and transactions are synthetic. Built as part of a Data Science
          thesis project.
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
              {tab === 'health' && <Health userId={activeUser} />}
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
