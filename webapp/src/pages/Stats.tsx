import { useEffect, useState } from 'react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import client from '../api/client'
import type { StatsData } from '../types/api'

export function Stats() {
  const [data, setData] = useState<StatsData | null>(null)
  const [period, setPeriod] = useState<'week' | 'month'>('week')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    client.get(`/stats?period=${period}`).then((r) => {
      setData(r.data)
      setLoading(false)
    })
  }, [period])

  return (
    <div>
      <h2 style={{ marginBottom: '16px' }}>📊 Статистика</h2>

      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
        {(['week', 'month'] as const).map((p) => (
          <button
            key={p}
            onClick={() => setPeriod(p)}
            style={{
              padding: '6px 16px',
              borderRadius: '16px',
              border: 'none',
              background: period === p ? 'var(--tg-theme-button-color, #2481cc)' : 'var(--tg-theme-secondary-bg-color, #eee)',
              color: period === p ? 'var(--tg-theme-button-text-color, #fff)' : 'inherit',
              cursor: 'pointer',
              fontSize: '14px',
            }}
          >
            {p === 'week' ? 'Неделя' : 'Месяц'}
          </button>
        ))}
      </div>

      {loading ? (
        <div>Загрузка...</div>
      ) : !data ? (
        <div>Нет данных</div>
      ) : (
        <>
          {data.leaderboard.length > 0 && (
            <>
              <h3 style={{ marginBottom: '12px' }}>🏆 Лидеры</h3>
              <div style={{ marginBottom: '24px' }}>
                {data.leaderboard.map((entry, i) => (
                  <div
                    key={entry.member_id}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '10px 12px',
                      marginBottom: '6px',
                      borderRadius: '8px',
                      background: 'var(--tg-theme-secondary-bg-color, #f5f5f5)',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span style={{ fontSize: '18px' }}>
                        {i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `${i + 1}.`}
                      </span>
                      <span style={{ fontWeight: 500 }}>{entry.display_name}</span>
                    </div>
                    <div style={{ textAlign: 'right', fontSize: '13px' }}>
                      <div style={{ fontWeight: 700, color: 'var(--tg-theme-button-color, #2481cc)' }}>
                        {entry.total_points} очков
                      </div>
                      <div style={{ color: 'var(--tg-theme-hint-color, #666)' }}>
                        {entry.chores_completed} дел · {entry.recipes_cooked} рецептов
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <h3 style={{ marginBottom: '12px' }}>Баллы по участникам</h3>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={data.leaderboard}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="display_name" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="total_points" fill="#4299e1" name="Баллы" />
                </BarChart>
              </ResponsiveContainer>
            </>
          )}

          {data.popular_chores.length > 0 && (
            <div style={{ marginTop: '24px' }}>
              <h3 style={{ marginBottom: '12px' }}>Топ задач</h3>
              {data.popular_chores.map((c) => (
                <div
                  key={c.title}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    padding: '8px 12px',
                    marginBottom: '6px',
                    borderRadius: '8px',
                    background: 'var(--tg-theme-secondary-bg-color, #f5f5f5)',
                  }}
                >
                  <span>{c.title}</span>
                  <span style={{ fontWeight: 600 }}>{c.count}×</span>
                </div>
              ))}
            </div>
          )}

          {data.leaderboard.length === 0 && (
            <div style={{ color: 'var(--tg-theme-hint-color, #999)', textAlign: 'center', marginTop: '32px' }}>
              Нет данных за этот период
            </div>
          )}
        </>
      )}
    </div>
  )
}
