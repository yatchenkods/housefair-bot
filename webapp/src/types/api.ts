export interface Member {
  id: number
  family_id: number
  user_id: number | null
  username: string
  display_name: string
  role: string
}

export interface Chore {
  id: number
  family_id: number
  title: string
  description: string
  chore_type: string
  category: string
  assigned_to: number | null
  created_by: number
  created_at: string
  due_date: string | null
  completed_at: string | null
  status: string
}

export interface Product {
  id: number
  family_id: number
  name: string
  quantity: number
  unit: string
  category: string
  expiry_date: string | null
  added_at: string
}

export interface ShoppingItem {
  id: number
  family_id: number
  name: string
  is_bought: boolean
  added_at: string
}

export interface DashboardData {
  active_chores: number
  overdue_chores: number
  products_count: number
  shopping_pending: number
  my_chores: Chore[]
}

export interface LeaderboardEntry {
  member_id: number
  display_name: string
  chores_completed: number
  recipes_cooked: number
  total_points: number
}

export interface StatsData {
  period: string
  since: string
  leaderboard: LeaderboardEntry[]
  popular_chores: { title: string; count: number }[]
}
