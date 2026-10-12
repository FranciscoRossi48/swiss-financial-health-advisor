const BASE = (import.meta.env.VITE_API_URL ?? '/api').replace(/\/$/, '')

export type TransactionType = 'income' | 'expense' | 'savings'

export interface DemoUser {
  user_id: string
  segment_label: string
  financial_health_score: number
  health_band: string
}

export interface UserScore {
  user_id: string
  financial_health_score: number
  health_band: string
  credit_readiness_score: number
  credit_readiness_band: string
  segment_label: string
  avg_income: number
  avg_net_cashflow: number
  avg_savings_rate: number
  avg_debt_to_income: number
}

export interface Transaction {
  date: string
  category: string
  category_label: string
  merchant: string
  transaction_type: TransactionType
  amount_chf: number
}

export interface CategorySpend {
  category: string
  category_label: string
  amount_chf: number
}

export interface AccountOverview {
  user_id: string
  balance_chf: number
  month: string
  month_income: number
  month_spending: number
  month_savings: number
  previous_month_spending: number
  spending_by_category: CategorySpend[]
}

export interface MonthlySummary {
  month: string
  income: number
  expense: number
  savings: number
  net_cashflow: number
}

export interface ScoreDimension {
  key: string
  label: string
  score: number
  weight: number
}

export interface ScoreBreakdown {
  score: number
  band: string
  dimensions: ScoreDimension[]
}

export interface SegmentComparison {
  metric: string
  label: string
  user_value: number
  segment_value: number
}

export interface HealthProfile {
  user_id: string
  financial_health: ScoreBreakdown
  credit_readiness: ScoreBreakdown
  segment: { label: string; description: string; comparison: SegmentComparison[] }
}

export interface Recommendation {
  priority_dimension: string
  recommendation: string
  explanation: string
}

export interface RiskFlag {
  flag: string
  severity: 'low' | 'medium' | 'high'
  explanation: string
}

export interface LoanResult {
  user_id: string
  monthly_payment: number
  resulting_debt_to_income: number
  projected_free_cashflow: number
  verdict: 'affordable' | 'marginal' | 'not recommended'
  explanation: string
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}${path}`, init)
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText} — ${path}`)
  }
  return response.json() as Promise<T>
}

export const api = {
  demoUsers: () => request<DemoUser[]>('/demo-users'),
  user: (id: string) => request<UserScore>(`/users/${id}`),
  overview: (id: string) => request<AccountOverview>(`/users/${id}/overview`),
  monthly: (id: string) => request<MonthlySummary[]>(`/users/${id}/monthly`),
  health: (id: string) => request<HealthProfile>(`/users/${id}/health`),
  recommendation: (id: string) => request<Recommendation>(`/users/${id}/recommendation`),
  riskFlags: (id: string) => request<RiskFlag[]>(`/users/${id}/risk-flags`),
  transactions: (id: string, params: { type?: TransactionType; month?: string; limit?: number } = {}) => {
    const query = new URLSearchParams()
    if (params.type) query.set('type', params.type)
    if (params.month) query.set('month', params.month)
    query.set('limit', String(params.limit ?? 50))
    return request<Transaction[]>(`/users/${id}/transactions?${query}`)
  },
  loan: (id: string, body: { loan_amount: number; annual_rate: number; term_years: number }) =>
    request<LoanResult>(`/users/${id}/loan-affordability`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
}
