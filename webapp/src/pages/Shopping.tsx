import { useEffect, useState } from 'react'
import client from '../api/client'
import { ShoppingItemRow } from '../components/ShoppingItemRow'
import type { ShoppingItem } from '../types/api'

export function Shopping() {
  const [items, setItems] = useState<ShoppingItem[]>([])
  const [loading, setLoading] = useState(true)
  const [name, setName] = useState('')

  const load = () => {
    client.get('/shopping').then((r) => {
      setItems(r.data)
      setLoading(false)
    })
  }

  useEffect(() => {
    load()
  }, [])

  const handleAdd = async () => {
    if (!name.trim()) return
    await client.post('/shopping', { name: name.trim() })
    setName('')
    load()
  }

  const handleToggle = async (id: number) => {
    await client.patch(`/shopping/${id}`)
    load()
  }

  const handleDelete = async (id: number) => {
    await client.delete(`/shopping/${id}`)
    load()
  }

  const handleClearBought = async () => {
    await client.delete('/shopping/bought')
    load()
  }

  const boughtCount = items.filter((i) => i.is_bought).length

  return (
    <div>
      <h2 style={{ marginBottom: '16px' }}>🛒 Список покупок</h2>

      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Добавить товар..."
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

      {boughtCount > 0 && (
        <button
          onClick={handleClearBought}
          style={{
            width: '100%',
            padding: '8px',
            borderRadius: '8px',
            border: '1px solid #e53e3e',
            background: 'transparent',
            color: '#e53e3e',
            cursor: 'pointer',
            fontSize: '14px',
            marginBottom: '12px',
          }}
        >
          Очистить купленные ({boughtCount})
        </button>
      )}

      {loading ? (
        <div>Загрузка...</div>
      ) : items.length === 0 ? (
        <div style={{ color: 'var(--tg-theme-hint-color, #999)', textAlign: 'center', marginTop: '32px' }}>
          Список покупок пуст
        </div>
      ) : (
        items.map((item) => (
          <ShoppingItemRow
            key={item.id}
            item={item}
            onToggle={handleToggle}
            onDelete={handleDelete}
          />
        ))
      )}
    </div>
  )
}
