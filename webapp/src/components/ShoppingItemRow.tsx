import type { ShoppingItem } from '../types/api'

interface Props {
  item: ShoppingItem
  onToggle: (id: number) => void
  onDelete: (id: number) => void
}

export function ShoppingItemRow({ item, onToggle, onDelete }: Props) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        padding: '10px 12px',
        marginBottom: '6px',
        borderRadius: '8px',
        background: 'var(--tg-theme-secondary-bg-color, #f5f5f5)',
        opacity: item.is_bought ? 0.6 : 1,
      }}
    >
      <input
        type="checkbox"
        checked={item.is_bought}
        onChange={() => onToggle(item.id)}
        style={{ marginRight: '12px', width: '18px', height: '18px', cursor: 'pointer' }}
      />
      <span
        style={{
          flex: 1,
          textDecoration: item.is_bought ? 'line-through' : 'none',
          color: item.is_bought ? 'var(--tg-theme-hint-color, #999)' : 'inherit',
        }}
      >
        {item.name}
      </span>
      <button
        onClick={() => onDelete(item.id)}
        style={{
          background: 'transparent',
          border: 'none',
          cursor: 'pointer',
          color: '#e53e3e',
          fontSize: '16px',
          padding: '0 4px',
        }}
      >
        🗑
      </button>
    </div>
  )
}
