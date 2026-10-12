import { Check, X } from 'lucide-react'
import type { DemoUser } from '../api'
import { bandTone, personaName, TONE_CLASSES } from '../format'

export function Avatar({ userId, size = 36 }: { userId: string; size?: number }) {
  return (
    <span
      className="inline-flex shrink-0 items-center justify-center rounded-full bg-mint font-extrabold text-ink"
      style={{ width: size, height: size, fontSize: size * 0.42 }}
    >
      {personaName(userId).charAt(0)}
    </span>
  )
}

interface PersonaListProps {
  users: DemoUser[]
  selected: string | null
  onSelect: (userId: string) => void
  dark?: boolean
}

export function PersonaList({ users, selected, onSelect, dark = false }: PersonaListProps) {
  return (
    <ul className="space-y-2">
      {users.map((user) => {
        const active = user.user_id === selected
        const tone = TONE_CLASSES[bandTone(user.health_band)]
        return (
          <li key={user.user_id}>
            <button
              type="button"
              onClick={() => onSelect(user.user_id)}
              aria-pressed={active}
              className={`flex w-full items-center gap-3 rounded-2xl p-3 text-left transition-colors ${
                dark
                  ? active
                    ? 'bg-white/10'
                    : 'hover:bg-white/5'
                  : active
                    ? 'bg-mint-soft'
                    : 'bg-canvas hover:bg-line/60'
              }`}
            >
              <Avatar userId={user.user_id} />
              <span className="min-w-0 flex-1">
                <span className={`block font-bold ${dark ? 'text-white' : ''}`}>{personaName(user.user_id)}</span>
                <span className={`block text-xs ${dark ? 'text-white/60' : 'text-muted'}`}>{user.segment_label}</span>
              </span>
              <span className={`tabular rounded-full px-2 py-0.5 text-xs font-bold ${tone.bg} ${tone.text}`}>
                {Math.round(user.financial_health_score)}
              </span>
              {active && <Check size={16} className={dark ? 'text-mint' : 'text-mint-deep'} />}
            </button>
          </li>
        )
      })}
    </ul>
  )
}

export function PersonaSheet({ open, onClose, ...listProps }: PersonaListProps & { open: boolean; onClose: () => void }) {
  if (!open) return null
  return (
    <div className="absolute inset-0 z-30 flex items-end bg-ink/40" onClick={onClose}>
      <div
        className="sheet-in w-full rounded-t-[28px] bg-white p-5 pb-8"
        role="dialog"
        aria-label="Switch demo customer"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="mb-4 flex items-start justify-between">
          <div>
            <p className="text-lg font-extrabold tracking-tight">Switch demo customer</p>
            <p className="text-sm text-muted">One synthetic customer from each money profile.</p>
          </div>
          <button type="button" onClick={onClose} aria-label="Close" className="rounded-full bg-canvas p-2">
            <X size={16} />
          </button>
        </div>
        <PersonaList
          {...listProps}
          onSelect={(id) => {
            listProps.onSelect(id)
            onClose()
          }}
        />
      </div>
    </div>
  )
}
