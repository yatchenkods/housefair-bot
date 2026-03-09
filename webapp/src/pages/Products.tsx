import { useEffect, useState } from 'react'
import client from '../api/client'
import { ProductCard } from '../components/ProductCard'
import type { Product } from '../types/api'

export function Products() {
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [name, setName] = useState('')
  const [quantity, setQuantity] = useState('1')
  const [unit, setUnit] = useState('шт')
  const [category, setCategory] = useState('')

  const load = () => {
    client.get('/products').then((r) => {
      setProducts(r.data)
      setLoading(false)
    })
  }

  useEffect(() => {
    load()
  }, [])

  const handleAdd = async () => {
    if (!name.trim()) return
    await client.post('/products', {
      name: name.trim(),
      quantity: parseFloat(quantity) || 1,
      unit,
      category,
    })
    setName('')
    setQuantity('1')
    load()
  }

  const handleDelete = async (id: number) => {
    await client.delete(`/products/${id}`)
    load()
  }

  const byCategory = products.reduce<Record<string, Product[]>>((acc, p) => {
    const cat = p.category || 'Без категории'
    ;(acc[cat] = acc[cat] || []).push(p)
    return acc
  }, {})

  return (
    <div>
      <h2 style={{ marginBottom: '16px' }}>🥕 Продукты</h2>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '12px' }}>
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Название"
          style={inputStyle}
        />
        <input
          value={quantity}
          onChange={(e) => setQuantity(e.target.value)}
          placeholder="Количество"
          type="number"
          min="0"
          style={inputStyle}
        />
        <input
          value={unit}
          onChange={(e) => setUnit(e.target.value)}
          placeholder="Единица (шт, кг...)"
          style={inputStyle}
        />
        <input
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          placeholder="Категория"
          style={inputStyle}
        />
      </div>
      <button onClick={handleAdd} style={btnStyle}>Добавить продукт</button>

      {loading ? (
        <div style={{ marginTop: '16px' }}>Загрузка...</div>
      ) : Object.keys(byCategory).length === 0 ? (
        <div style={{ color: 'var(--tg-theme-hint-color, #999)', textAlign: 'center', marginTop: '32px' }}>
          Список продуктов пуст
        </div>
      ) : (
        Object.entries(byCategory).sort().map(([cat, items]) => (
          <div key={cat} style={{ marginTop: '16px' }}>
            <div style={{ fontWeight: 600, marginBottom: '8px', color: 'var(--tg-theme-hint-color, #666)' }}>
              {cat}
            </div>
            {items.map((p) => (
              <ProductCard key={p.id} product={p} onDelete={handleDelete} />
            ))}
          </div>
        ))
      )}
    </div>
  )
}

const inputStyle: React.CSSProperties = {
  padding: '10px',
  borderRadius: '8px',
  border: '1px solid var(--tg-theme-hint-color, #ccc)',
  background: 'var(--tg-theme-bg-color, #fff)',
  color: 'var(--tg-theme-text-color, #000)',
  fontSize: '14px',
  width: '100%',
  boxSizing: 'border-box',
}

const btnStyle: React.CSSProperties = {
  width: '100%',
  padding: '10px',
  borderRadius: '8px',
  border: 'none',
  background: 'var(--tg-theme-button-color, #2481cc)',
  color: 'var(--tg-theme-button-text-color, #fff)',
  cursor: 'pointer',
  fontSize: '15px',
  marginBottom: '16px',
}
