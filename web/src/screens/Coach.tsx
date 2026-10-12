import { AlertTriangle, CheckCircle2, Sparkles } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api, type LoanResult } from '../api'
import { Card, Chip, ErrorState, SectionTitle, Skeleton } from '../components/ui'
import { bandTone, formatCHFRounded, formatPercent, titleCase } from '../format'
import { useApi } from '../useApi'

const AFFORDABILITY_CEILING = 0.33

export function Coach({ userId }: { userId: string }) {
  const recommendation = useApi(`rec:${userId}`, () => api.recommendation(userId))
  const flags = useApi(`flags:${userId}`, () => api.riskFlags(userId))

  if (recommendation.error) return <ErrorState error={recommendation.error} />

  return (
    <div className="space-y-4">
      {recommendation.data ? (
        <section className="rise relative overflow-hidden rounded-3xl bg-ink p-5 text-white">
          <div className="pointer-events-none absolute -bottom-24 -left-10 h-56 w-56 rounded-full bg-mint/20 blur-3xl" />
          <p className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-mint">
            <Sparkles size={14} /> Focus area · {titleCase(recommendation.data.priority_dimension)}
          </p>
          <p className="mt-3 text-xl font-extrabold leading-snug tracking-tight">
            {recommendation.data.recommendation}
          </p>
          <p className="mt-3 text-sm text-white/70">{recommendation.data.explanation}</p>
        </section>
      ) : (
        <Skeleton className="h-48" />
      )}

      <Card className="rise">
        <SectionTitle>Things to keep an eye on</SectionTitle>
        {flags.data ? (
          flags.data.length > 0 ? (
            <ul className="space-y-2.5">
              {flags.data.map((f) => (
                <li key={f.flag} className="flex gap-3 rounded-2xl bg-canvas p-3">
                  <AlertTriangle size={18} className={`mt-0.5 shrink-0 ${f.severity === 'high' ? 'text-danger' : 'text-warn'}`} />
                  <div className="flex-1">
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-sm font-bold">{f.flag}</p>
                      <Chip tone={bandTone(f.severity)}>{titleCase(f.severity)}</Chip>
                    </div>
                    <p className="mt-0.5 text-sm text-muted">{f.explanation}</p>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="flex items-center gap-2 rounded-2xl bg-mint-soft p-3 text-sm font-semibold text-mint-deep">
              <CheckCircle2 size={18} /> Nothing to flag right now. Nice work.
            </p>
          )
        ) : (
          <Skeleton className="h-28" />
        )}
      </Card>

      <LoanSimulator userId={userId} />

      <p className="px-1 text-xs text-muted">
        Pulse insights are educational guidance based on synthetic data. They are not credit approval, investment
        advice or regulated financial advice.
      </p>
    </div>
  )
}

function LoanSimulator({ userId }: { userId: string }) {
  const [amount, setAmount] = useState(10000)
  const [rate, setRate] = useState(5)
  const [years, setYears] = useState(3)
  const [result, setResult] = useState<LoanResult>()
  const [error, setError] = useState<Error>()

  useEffect(() => {
    let cancelled = false
    const timer = setTimeout(() => {
      api
        .loan(userId, { loan_amount: amount, annual_rate: rate / 100, term_years: years })
        .then((data) => {
          if (!cancelled) {
            setResult(data)
            setError(undefined)
          }
        })
        .catch((err: Error) => !cancelled && setError(err))
    }, 200)
    return () => {
      cancelled = true
      clearTimeout(timer)
    }
  }, [userId, amount, rate, years])

  return (
    <Card className="rise">
      <SectionTitle>Could I afford a loan?</SectionTitle>
      <div className="space-y-4">
        <Slider label="Amount" value={formatCHFRounded(amount)} min={1000} max={60000} step={500} current={amount} onChange={setAmount} />
        <Slider label="Interest rate" value={`${rate.toFixed(1)}%`} min={0} max={15} step={0.1} current={rate} onChange={setRate} />
        <Slider label="Term" value={`${years} ${years === 1 ? 'year' : 'years'}`} min={1} max={10} step={1} current={years} onChange={setYears} />
      </div>

      {error && <p className="mt-4 text-sm text-danger">{error.message}</p>}
      {result && (
        <div className="mt-5 rounded-2xl bg-canvas p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-muted">Monthly payment</p>
              <p className="tabular text-2xl font-extrabold tracking-tight">{formatCHFRounded(result.monthly_payment)}</p>
            </div>
            <Chip tone={bandTone(result.verdict)}>{titleCase(result.verdict)}</Chip>
          </div>

          <div className="mt-4">
            <div className="flex justify-between text-xs font-semibold">
              <span className="text-muted">Debt payments vs income</span>
              <span className="tabular">{formatPercent(result.resulting_debt_to_income, 1)}</span>
            </div>
            <div className="relative mt-1.5 h-2 rounded-full bg-white">
              <div
                className={`h-full rounded-full transition-[width] duration-500 ${
                  result.resulting_debt_to_income > AFFORDABILITY_CEILING ? 'bg-danger' : 'bg-mint'
                }`}
                style={{ width: `${Math.min(100, (result.resulting_debt_to_income / 0.6) * 100)}%` }}
              />
              <div
                className="absolute -top-1 h-4 w-0.5 rounded bg-ink"
                style={{ left: `${(AFFORDABILITY_CEILING / 0.6) * 100}%` }}
                title="33% affordability guideline"
              />
            </div>
            <p className="mt-1 text-[11px] text-muted">Marker: the 33% affordability guideline used in Switzerland.</p>
          </div>

          <p className="mt-3 text-sm">
            Left over each month after the payment:{' '}
            <span className={`tabular font-bold ${result.projected_free_cashflow < 0 ? 'text-danger' : 'text-mint-deep'}`}>
              {formatCHFRounded(result.projected_free_cashflow)}
            </span>
          </p>
          <p className="mt-2 text-sm text-muted">{result.explanation}</p>
        </div>
      )}
    </Card>
  )
}

interface SliderProps {
  label: string
  value: string
  min: number
  max: number
  step: number
  current: number
  onChange: (value: number) => void
}

function Slider({ label, value, min, max, step, current, onChange }: SliderProps) {
  return (
    <label className="block">
      <span className="flex justify-between text-sm">
        <span className="font-semibold">{label}</span>
        <span className="tabular font-bold">{value}</span>
      </span>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={current}
        onChange={(event) => onChange(Number(event.target.value))}
        className="mt-2 w-full"
      />
    </label>
  )
}
