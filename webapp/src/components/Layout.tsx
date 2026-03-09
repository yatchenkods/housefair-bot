import { NavLink, Outlet } from 'react-router-dom'

const tabs = [
  { to: '/', label: '🏠', title: 'Главная' },
  { to: '/chores', label: '✅', title: 'Задачи' },
  { to: '/products', label: '🥕', title: 'Продукты' },
  { to: '/shopping', label: '🛒', title: 'Покупки' },
  { to: '/stats', label: '📊', title: 'Статистика' },
]

export function Layout() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100dvh' }}>
      <main style={{ flex: 1, overflowY: 'auto', padding: '16px' }}>
        <Outlet />
      </main>
      <nav
        style={{
          display: 'flex',
          borderTop: '1px solid var(--tg-theme-hint-color, #ccc)',
          background: 'var(--tg-theme-bg-color, #fff)',
        }}
      >
        {tabs.map((tab) => (
          <NavLink
            key={tab.to}
            to={tab.to}
            end={tab.to === '/'}
            style={({ isActive }) => ({
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              padding: '8px 4px',
              textDecoration: 'none',
              fontSize: '20px',
              color: isActive
                ? 'var(--tg-theme-button-color, #2481cc)'
                : 'var(--tg-theme-hint-color, #999)',
            })}
          >
            <span>{tab.label}</span>
            <span style={{ fontSize: '10px', marginTop: '2px' }}>{tab.title}</span>
          </NavLink>
        ))}
      </nav>
    </div>
  )
}
