import { AlertTriangle, Check, CheckCircle2, Sparkles } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api, type LoanResult, type PlanStep, type RiskFlag } from '../api'
import { RangeSlider } from '../components/RangeSlider'
import { Card, Chip, ErrorState, SectionTitle, Skeleton } from '../components/ui'
import { bandTone, formatCHFRounded, formatPercent, titleCase } from '../format'
import { useApi } from '../useApi'
import { usePlanProgress } from '../usePlanProgress'

const AFFORDABILITY_CEILING = 0.33
const DTI_SCALE_MAX = 0.6
const NO_FLAGS = 'No major risk flags'

// Which plan focus (and step) each risk flag is addressed by, so a flag can point to the plan.
const FLAG_PLAN_STEP: Record<string, { focus: string; step: number }> = {
  'Negative free cashflow': { focus: 'liquidity', step: 1 },
  'Thin cashflow buffer': { focus: 'liquidity', step: 1 },
  'High discretionary spend': { focus: 'liquidity', step: 2 },
  'Low savings discipline': { focus: 'savings capacity', step: 1 },
  'Elevated debt burden': { focus: 'debt exposure', step: 1 },
  'High debt burden': { focus: 'debt exposure', step: 1 },
  'Variable income': { focus: 'income stability', step: 1 },
  'Highly variable income': { focus: 'income stability', step: 1 },
}

const SEVERITY_STYLE: Record<RiskFlag['severity'], { bg: string; icon: string; label: string }> = {
  high: { bg: 'bg-danger-soft', icon: 'text-danger', label: 'text-danger' },
  medium: { bg: 'bg-warn-soft', icon: 'text-warn', label: 'text-[#a86a0c]' },
  low: { bg: 'bg-info-soft', icon: 'text-info', label: 'text-info' },
}

export function Coach({ userId }: { userId: string }) {
  const recommendation = useApi(`rec:${userId}`, () => api.recommendation(userId))
  const flags = useApi(`flags:${userId}`, () => api.riskFlags(userId))
  const user = useApi(`user:${userId}`, () => api.user(userId))
  const plan = usePlanProgress(userId)

  if (recommendation.error) return <ErrorState error={recommendation.error} />

  const rec = recommendation.data
  const currentScore = user.data?.financial_health_score
  const realFlags = flags.data?.filter((f) => f.flag !== NO_FLAGS) ?? []

  return (
    <div className="space-y-4">
      {rec ? (
        <section className="rise relative overflow-hidden rounded-3xl bg-ink p-5 text-white">
          <div className="pointer-events-none absolute -bottom-24 -left-10 h-56 w-56 rounded-full bg-mint/20 blur-3xl" />
          <p className="relative flex items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-mint">
            <Sparkles size={14} /> Focus area · {titleCase(rec.priority_dimension)}
          </p>
          <p className="relative mt-3 text-xl font-extrabold leading-snug tracking-tight">{rec.recommendation}</p>
          <p className="relative mt-2.5 text-sm text-white/70">{rec.explanation}</p>
          {currentScore !== undefined && rec.projected_score > currentScore && (
            <div className="relative mt-4 flex items-center gap-3 rounded-2xl bg-white/[0.07] p-3">
              <div className="flex-1">
                <p className="text-xs font-semibold text-white/60">Projected score</p>
                <p className="tabular mt-0.5 text-[22px] font-extrabold tracking-tight">
                  {Math.round(currentScore)} <span className="text-white/40">→</span>{' '}
                  <span className="text-mint">{Math.round(rec.projected_score)}</span>
                </p>
              </div>
              <div className="flex h-2 w-[110px] overflow-hidden rounded-full bg-white/[0.12]" aria-hidden="true">
                <div className="bg-white" style={{ width: `${currentScore}%` }} />
                <div className="bg-mint" style={{ width: `${rec.projected_score - currentScore}%` }} />
              </div>
            </div>
          )}
        </section>
      ) : (
        <Skeleton className="h-56" />
      )}

      {rec && <PlanCard steps={rec.steps} done={plan.done} doneCount={plan.doneCount} onToggle={plan.toggle} />}

      <Card className="rise">
        <SectionTitle>Things to keep an eye on</SectionTitle>
        {flags.data ? (
          realFlags.length > 0 ? (
            <ul className="space-y-2.5">
              {realFlags.map((f) => {
                const style = SEVERITY_STYLE[f.severity]
                const link = FLAG_PLAN_STEP[f.flag]
                const addressed = rec && link && link.focus === rec.priority_dimension
                return (
                  <li key={f.flag} className={`flex gap-3 rounded-2xl p-3 ${style.bg}`}>
                    <AlertTriangle size={18} className={`mt-0.5 shrink-0 ${style.icon}`} />
                    <div className="flex-1">
                      <div className="flex items-start justify-between gap-2">
                        <p className="text-sm font-bold">{f.flag}</p>
                        <span className={`text-xs font-bold leading-5 ${style.label}`}>{titleCase(f.severity)}</span>
                      </div>
                      <p className="mt-0.5 text-sm text-muted">
                        {f.explanation}
                        {addressed && ` Step ${link.step} of your plan addresses this.`}
                      </p>
                    </div>
                  </li>
                )
              })}
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

      <LoanSimulator userId={userId} buffer={user.data?.avg_free_cashflow} />

      <p className="px-1 text-xs text-muted">
        Pulse insights are educational guidance based on synthetic data. They are not credit approval, investment
        advice or regulated financial advice.
      </p>
    </div>
  )
}

interface PlanCardProps {
  steps: PlanStep[]
  done: boolean[]
  doneCount: number
  onToggle: (index: number) => void
}

function PlanCard({ steps, done, doneCount, onToggle }: PlanCardProps) {
  return (
    <Card className="rise">
      <SectionTitle
        action={
          <span className="tabular text-xs font-bold text-muted">
            {doneCount} of {steps.length} done
          </span>
        }
      >
        Your plan
      </SectionTitle>
      <ol className="space-y-2">
        {steps.map((step, index) => {
          const isDone = done[index]
          return (
            <li key={step.title}>
              <button
                type="button"
                onClick={() => onToggle(index)}
                aria-pressed={isDone}
                className={`flex w-full gap-3 rounded-2xl p-3 text-left transition-colors ${
                  isDone ? 'bg-canvas' : 'bg-white hover:bg-canvas/60'
                }`}
              >
                <span
                  className={`mt-px flex h-[22px] w-[22px] shrink-0 items-center justify-center rounded-full border-2 text-white transition-colors ${
                    isDone ? 'border-mint-deep bg-mint-deep' : 'border-[#cfd8d4] bg-white'
                  }`}
                >
                  {isDone && <Check size={13} strokeWidth={3} />}
                </span>
                <span className="min-w-0 flex-1">
                  <span className={`block text-sm font-bold ${isDone ? 'line-through' : ''}`}>{step.title}</span>
                  <span className="mt-0.5 block text-[13px] leading-[18px] text-muted">{step.body}</span>
                </span>
                {step.points > 0 && (
                  <span className="shrink-0 self-start rounded-full bg-mint-soft px-2 py-0.5 text-xs font-extrabold text-mint-deep">
                    +{step.points}
                  </span>
                )}
              </button>
            </li>
          )
        })}
      </ol>
    </Card>
  )
}

function LoanSimulator({ userId, buffer }: { userId: string; buffer: number | undefined }) {
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

  const ceilingPct = (AFFORDABILITY_CEILING / DTI_SCALE_MAX) * 100
  const used = result && buffer !== undefined ? (buffer > 0 ? Math.min(1, result.monthly_payment / buffer) : 1) : 0

  return (
    <Card className="rise">
      <h2 className="text-[15px] font-bold tracking-tight">Could I afford a loan?</h2>
      <p className="mt-1 text-[13px] leading-[18px] text-muted">
        Test a loan against your real numbers. Nothing is applied for.
      </p>

      <div className="mt-4 flex flex-col items-center text-center" aria-live="polite">
        <p className="text-xs font-semibold text-muted">Monthly payment</p>
        {result ? (
          <>
            <p className="tabular text-[34px] font-extrabold leading-tight tracking-tight">
              {formatCHFRounded(result.monthly_payment)}
            </p>
            <span className="mt-1.5">
              <Chip tone={bandTone(result.verdict)}>{titleCase(result.verdict)}</Chip>
            </span>
          </>
        ) : (
          <Skeleton className="mt-1 h-16 w-40" />
        )}
      </div>

      <div className="mt-[18px] space-y-4">
        <RangeSlider
          label="Amount"
          value={formatCHFRounded(amount)}
          min={1000}
          max={60000}
          step={500}
          current={amount}
          onChange={setAmount}
        />
        <RangeSlider
          label="Interest rate"
          value={`${rate.toFixed(1)}%`}
          min={0}
          max={15}
          step={0.1}
          current={rate}
          onChange={setRate}
        />
        <RangeSlider
          label="Term"
          value={`${years} ${years === 1 ? 'year' : 'years'}`}
          min={1}
          max={10}
          step={1}
          current={years}
          onChange={setYears}
        />
      </div>

      {error && <p className="mt-4 text-sm text-danger">{error.message}</p>}
      {result && (
        <div className="mt-5 space-y-3.5 rounded-2xl bg-canvas p-4">
          <div>
            <div className="flex justify-between text-xs font-semibold">
              <span className="text-muted">Debt payments vs income</span>
              <span className="tabular font-extrabold">{formatPercent(result.resulting_debt_to_income, 1)}</span>
            </div>
            <div className="relative mt-2 h-2.5 overflow-hidden rounded-full bg-white">
              <div
                className="absolute inset-y-0 right-0"
                style={{
                  left: `${ceilingPct}%`,
                  background: 'repeating-linear-gradient(135deg, #fdecec 0 4px, #fff 4px 8px)',
                }}
              />
              <div
                className={`relative h-full rounded-full transition-[width] duration-500 ${
                  result.resulting_debt_to_income > AFFORDABILITY_CEILING ? 'bg-danger' : 'bg-ink'
                }`}
                style={{ width: `${Math.min(100, (result.resulting_debt_to_income / DTI_SCALE_MAX) * 100)}%` }}
              />
            </div>
            <div className="relative mt-1 h-3.5 text-[11px] text-muted">
              <span className="absolute -translate-x-1/2 font-bold" style={{ left: `${ceilingPct}%` }}>
                33% guideline
              </span>
            </div>
          </div>

          {buffer !== undefined && (
            <div>
              <div className="flex justify-between text-xs font-semibold">
                <span className="text-muted">Monthly buffer after payment</span>
                <span
                  className={`tabular font-extrabold ${result.projected_free_cashflow < 0 ? 'text-danger' : 'text-mint-deep'}`}
                >
                  {formatCHFRounded(result.projected_free_cashflow)}
                </span>
              </div>
              <div className="mt-2 flex h-2.5 overflow-hidden rounded-full bg-white">
                <div className="bg-ink transition-[width] duration-500" style={{ width: `${used * 100}%` }} />
                <div className="bg-mint transition-[width] duration-500" style={{ width: `${(1 - used) * 100}%` }} />
              </div>
              <p className="mt-1 text-[11px] text-muted">
                {buffer > 0
                  ? `Of your ${formatCHFRounded(buffer)} average monthly buffer, before savings transfers`
                  : 'You have no monthly buffer today: spending already uses all your income.'}
              </p>
            </div>
          )}

          <p className="text-sm text-ink">{result.explanation}</p>
        </div>
      )}
    </Card>
  )
}
