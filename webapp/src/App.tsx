import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { useAuth } from './hooks/useAuth'
import { Chores } from './pages/Chores'
import { Dashboard } from './pages/Dashboard'
import { Products } from './pages/Products'
import { Shopping } from './pages/Shopping'
import { Stats } from './pages/Stats'

export function App() {
  const { member, loading, error, retry } = useAuth()

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100dvh' }}>
        <div>Загрузка...</div>
      </div>
    )
  }

  if (error || !member) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', height: '100dvh', gap: '16px', padding: '24px', textAlign: 'center' }}>
        <div style={{ fontSize: '48px' }}>🔒</div>
        <div style={{ fontWeight: 600 }}>Нет доступа</div>
        <div style={{ color: 'var(--tg-theme-hint-color, #666)', fontSize: '14px' }}>
          {error || 'Вы не являетесь участником семьи. Попросите администратора добавить вас.'}
        </div>
        <button
          onClick={retry}
          style={{
            padding: '10px 24px',
            borderRadius: '8px',
            border: 'none',
            background: 'var(--tg-theme-button-color, #2481cc)',
            color: 'var(--tg-theme-button-text-color, #fff)',
            cursor: 'pointer',
            fontSize: '15px',
          }}
        >
          Повторить
        </button>
      </div>
    )
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="/chores" element={<Chores />} />
          <Route path="/products" element={<Products />} />
          <Route path="/shopping" element={<Shopping />} />
          <Route path="/stats" element={<Stats />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
