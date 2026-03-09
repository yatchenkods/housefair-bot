import type { Chore } from '../types/api'

interface Props {
  chore: Chore
  onDone?: (id: number) => void
  onDelete?: (id: number) => void
}

export function ChoreCard({ chore, onDone, onDelete }: Props) {
  const isOverdue = chore.status === 'overdue'
  const isDone = chore.status === 'completed'

  return (
    <div
      style={{
        padding: '12px',
        marginBottom: '8px',
        borderRadius: '8px',
        background: 'var(--tg-theme-secondary-bg-color, #f5f5f5)',
        borderLeft: `4px solid ${isOverdue ? '#e53e3e' : isDone ? '#38a169' : '#4299e1'}`,
        opacity: isDone ? 0.7 : 1,
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 600 }}>{chore.title}</div>
          {chore.description && (
            <div style={{ fontSize: '13px', color: 'var(--tg-theme-hint-color, #666)', marginTop: '4px' }}>
              {chore.description}
            </div>
          )}
          {chore.category && (
            <div style={{ fontSize: '12px', marginTop: '4px', color: '#4299e1' }}>#{chore.category}</div>
          )}
          {chore.due_date && (
            <div style={{ fontSize: '12px', marginTop: '4px', color: isOverdue ? '#e53e3e' : '#666' }}>
              До: {new Date(chore.due_date).toLocaleDateString('ru-RU')}
            </div>
          )}
        </div>
        <div style={{ display: 'flex', gap: '8px', marginLeft: '8px' }}>
          {!isDone && onDone && (
            <button
              onClick={() => onDone(chore.id)}
              style={{
                background: '#38a169',
                color: '#fff',
                border: 'none',
                borderRadius: '6px',
                padding: '4px 8px',
                cursor: 'pointer',
                fontSize: '14px',
              }}
            >
              ✓
            </button>
          )}
          {onDelete && (
            <button
              onClick={() => onDelete(chore.id)}
              style={{
                background: '#e53e3e',
                color: '#fff',
                border: 'none',
                borderRadius: '6px',
                padding: '4px 8px',
                cursor: 'pointer',
                fontSize: '14px',
              }}
            >
              ✕
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
