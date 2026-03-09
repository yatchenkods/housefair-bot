import { useEffect, useState } from 'react'
import client from '../api/client'
import { ChoreCard } from '../components/ChoreCard'
import type { DashboardData } from '../types/api'

export function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    client.get('/dashboard').then((r) => {
      setData(r.data)
      setLoading(false)
    })
  }, [])

  if (loading) return <div>Загрузка...</div>
  if (!data) return <div>Ошибка загрузки</div>

  const stats = [
    { label: 'Активных задач', value: data.active_chores, color: '#4299e1' },
    { label: 'Просрочено', value: data.overdue_chores, color: '#e53e3e' },
    { label: 'Продуктов', value: data.products_count, color: '#38a169' },
    { label: 'Купить', value: data.shopping_pending, color: '#e08000' },
  ]

  return (
    <div>
      <h2 style={{ marginBottom: '16px' }}>🏠 Главная</h2>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '24px' }}>
        {stats.map((s) => (
          <div
            key={s.label}
            style={{
              padding: '16px',
              borderRadius: '10px',
              background: 'var(--tg-theme-secondary-bg-color, #f5f5f5)',
              textAlign: 'center',
            }}
          >
            <div style={{ fontSize: '28px', fontWeight: 700, color: s.color }}>{s.value}</div>
            <div style={{ fontSize: '12px', color: 'var(--tg-theme-hint-color, #666)', marginTop: '4px' }}>
              {s.label}
            </div>
          </div>
        ))}
      </div>

      {data.my_chores.length > 0 && (
        <>
          <h3 style={{ marginBottom: '12px' }}>Мои задачи</h3>
          {data.my_chores.map((chore) => (
            <ChoreCard key={chore.id} chore={chore} />
          ))}
        </>
      )}
    </div>
  )
}
