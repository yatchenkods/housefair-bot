import type { Product } from '../types/api'

interface Props {
  product: Product
  onDelete?: (id: number) => void
}

export function ProductCard({ product, onDelete }: Props) {
  return (
    <div
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
      <div>
        <span style={{ fontWeight: 500 }}>{product.name}</span>
        <span style={{ marginLeft: '8px', color: 'var(--tg-theme-hint-color, #666)', fontSize: '13px' }}>
          {product.quantity} {product.unit}
        </span>
        {product.expiry_date && (
          <div style={{ fontSize: '12px', color: '#e08000', marginTop: '2px' }}>
            Срок: {product.expiry_date}
          </div>
        )}
      </div>
      {onDelete && (
        <button
          onClick={() => onDelete(product.id)}
          style={{
            background: 'transparent',
            border: 'none',
            cursor: 'pointer',
            color: '#e53e3e',
            fontSize: '18px',
          }}
        >
          🗑
        </button>
      )}
    </div>
  )
}
