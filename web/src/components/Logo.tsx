export function PulseMark({ size = 28 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true">
      <rect width="32" height="32" rx="9" fill="#0C1A17" />
      <path
        d="M5 17h5l3-7 5 13 3-6h6"
        fill="none"
        stroke="#1FD99A"
        strokeWidth="2.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

export function Logo({ size = 28, light = false }: { size?: number; light?: boolean }) {
  return (
    <span className="inline-flex items-center gap-2">
      <PulseMark size={size} />
      <span className={`font-extrabold tracking-tight ${light ? 'text-white' : 'text-ink'}`} style={{ fontSize: size * 0.75 }}>
        pulse
      </span>
    </span>
  )
}
