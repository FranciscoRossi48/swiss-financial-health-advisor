import {
  ArrowDownLeft,
  Briefcase,
  CreditCard,
  House,
  Plane,
  PiggyBank,
  Repeat,
  ShieldCheck,
  ShoppingBag,
  ShoppingBasket,
  TrainFront,
  UtensilsCrossed,
  type LucideIcon,
} from 'lucide-react'

const ICONS: Record<string, { icon: LucideIcon; className: string }> = {
  salary: { icon: ArrowDownLeft, className: 'bg-mint-soft text-mint-deep' },
  freelance: { icon: Briefcase, className: 'bg-mint-soft text-mint-deep' },
  rent: { icon: House, className: 'bg-[#EEE9FB] text-[#6B4FD8]' },
  insurance: { icon: ShieldCheck, className: 'bg-info-soft text-info' },
  groceries: { icon: ShoppingBasket, className: 'bg-[#FFF1E0] text-[#C26A0A]' },
  transport: { icon: TrainFront, className: 'bg-[#FDE8EC] text-[#C5283D]' },
  restaurants: { icon: UtensilsCrossed, className: 'bg-[#FFF4D6] text-[#A07400]' },
  shopping: { icon: ShoppingBag, className: 'bg-[#FCE7F6] text-[#B8338F]' },
  travel: { icon: Plane, className: 'bg-[#E3F5FB] text-[#0F7EA3]' },
  subscriptions: { icon: Repeat, className: 'bg-[#ECEEF2] text-[#4A5468]' },
  debt_payment: { icon: CreditCard, className: 'bg-danger-soft text-danger' },
  savings_transfer: { icon: PiggyBank, className: 'bg-mint-soft text-mint-deep' },
}

export function CategoryIcon({ category, size = 40 }: { category: string; size?: number }) {
  const entry = ICONS[category] ?? { icon: CreditCard, className: 'bg-canvas text-muted' }
  const Icon = entry.icon
  return (
    <span
      className={`inline-flex shrink-0 items-center justify-center rounded-2xl ${entry.className}`}
      style={{ width: size, height: size }}
    >
      <Icon size={size * 0.45} strokeWidth={2.2} />
    </span>
  )
}
