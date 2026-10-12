import { ChartNoAxesColumn, HeartPulse, House, Sparkles, type LucideIcon } from 'lucide-react'

export type Tab = 'home' | 'activity' | 'health' | 'coach'

const TABS: { id: Tab; label: string; icon: LucideIcon }[] = [
  { id: 'home', label: 'Home', icon: House },
  { id: 'activity', label: 'Activity', icon: ChartNoAxesColumn },
  { id: 'health', label: 'Health', icon: HeartPulse },
  { id: 'coach', label: 'Coach', icon: Sparkles },
]

export function TabBar({ active, onChange }: { active: Tab; onChange: (tab: Tab) => void }) {
  return (
    <nav className="border-t border-line bg-white/95 px-3 pb-[max(10px,env(safe-area-inset-bottom))] pt-2 backdrop-blur">
      <ul className="grid grid-cols-4">
        {TABS.map(({ id, label, icon: Icon }) => {
          const selected = id === active
          return (
            <li key={id}>
              <button
                type="button"
                onClick={() => onChange(id)}
                aria-current={selected ? 'page' : undefined}
                className={`flex w-full flex-col items-center gap-1 rounded-2xl py-1.5 text-[11px] font-bold transition-colors ${
                  selected ? 'text-ink' : 'text-muted hover:text-ink'
                }`}
              >
                <span
                  className={`flex h-8 w-14 items-center justify-center rounded-full transition-colors ${
                    selected ? 'bg-mint-soft' : ''
                  }`}
                >
                  <Icon size={20} strokeWidth={selected ? 2.5 : 2} />
                </span>
                {label}
              </button>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
