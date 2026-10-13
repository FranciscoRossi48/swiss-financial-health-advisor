interface RangeSliderProps {
  label: string
  value: string
  min: number
  max: number
  step: number
  current: number
  onChange: (value: number) => void
}

// Custom-drawn track and thumb, with the native range input layered on top (invisible) so
// keyboard control, touch and screen readers keep working.
export function RangeSlider({ label, value, min, max, step, current, onChange }: RangeSliderProps) {
  const pct = `${((current - min) / (max - min)) * 100}%`
  return (
    <label className="block">
      <span className="flex justify-between text-sm">
        <span className="font-semibold">{label}</span>
        <span className="tabular font-extrabold">{value}</span>
      </span>
      <span className="relative mt-2 block h-[22px]">
        <span className="absolute inset-x-0 top-2 h-1.5 rounded-full bg-line" />
        <span className="absolute left-0 top-2 h-1.5 rounded-full bg-ink" style={{ width: pct }} />
        <span
          className="absolute top-0 -ml-[11px] h-[22px] w-[22px] rounded-full border-2 border-ink bg-white shadow-[0_2px_6px_rgba(12,26,23,0.18)]"
          style={{ left: pct }}
        />
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={current}
          aria-label={label}
          onChange={(event) => onChange(Number(event.target.value))}
          className="absolute inset-0 m-0 w-full cursor-pointer opacity-0"
        />
      </span>
    </label>
  )
}
