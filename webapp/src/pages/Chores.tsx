import { useEffect, useState } from 'react'
import client from '../api/client'
import { ChoreCard } from '../components/ChoreCard'
import type { Chore } from '../types/api'

export function Chores() {
  const [chores, setChores] = useState<Chore[]>([])
  const [loading, setLoading] = useState(true)
  const [title, setTitle] = useState('')
  const [filter, setFilter] = useState<string>('')

  const load = () => {
    const params = filter ? `?status=${filter}` : ''
    client.get(`/chores${params}`).then((r) => {
      setChores(r.data)
      setLoading(false)
    })
  }

  useEffect(() => {
    load()
  }, [filter])

  const handleDone = async (id: number) => {
    await client.patch(`/chores/${id}/done`)
    load()
  }

  const handleDelete = async (id: number) => {
    await client.delete(`/chores/${id}`)
    load()
  }

  const handleAdd = async () => {
    if (!title.trim()) return
    await client.post('/chores', { title: title.trim() })
    setTitle('')
    load()
  }

  return (
    <div>
      <h2 style={{ marginBottom: '16px' }}>✅ Задачи</h2>

      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Новая задача..."
          onKeyDown={(e) => e.key === 'Enter' && handleAdd()}
          style={{
            flex: 1,
            padding: '10px',
            borderRadius: '8px',
            border: '1px solid var(--tg-theme-hint-color, #ccc)',
            background: 'var(--tg-theme-bg-color, #fff)',
            color: 'var(--tg-theme-text-color, #000)',
            fontSize: '16px',
          }}
        />
        <button
          onClick={handleAdd}
          style={{
            padding: '10px 16px',
            borderRadius: '8px',
            border: 'none',
            background: 'var(--tg-theme-button-color, #2481cc)',
            color: 'var(--tg-theme-button-text-color, #fff)',
            cursor: 'pointer',
            fontSize: '16px',
          }}
        >
          +
        </button>
      </div>

      <div style={{ display: 'flex', gap: '6px', marginBottom: '16px', flexWrap: 'wrap' }}>
        {[['', 'Все'], ['pending', 'Активные'], ['overdue', 'Просрочены'], ['completed', 'Выполнены']].map(
          ([val, label]) => (
            <button
              key={val}
              onClick={() => setFilter(val)}
              style={{
                padding: '4px 10px',
                borderRadius: '16px',
                border: 'none',
                background: filter === val ? 'var(--tg-theme-button-color, #2481cc)' : 'var(--tg-theme-secondary-bg-color, #eee)',
                color: filter === val ? 'var(--tg-theme-button-text-color, #fff)' : 'inherit',
                cursor: 'pointer',
                fontSize: '13px',
              }}
            >
              {label}
            </button>
          ),
        )}
      </div>

      {loading ? (
        <div>Загрузка...</div>
      ) : chores.length === 0 ? (
        <div style={{ color: 'var(--tg-theme-hint-color, #999)', textAlign: 'center', marginTop: '32px' }}>
          Задачи не найдены
        </div>
      ) : (
        chores.map((chore) => (
          <ChoreCard
            key={chore.id}
            chore={chore}
            onDone={chore.status !== 'completed' ? handleDone : undefined}
            onDelete={handleDelete}
          />
        ))
      )}
    </div>
  )
}
