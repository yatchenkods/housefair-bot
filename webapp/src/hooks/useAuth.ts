import { useCallback, useEffect, useState } from 'react'
import client from '../api/client'
import type { Member } from '../types/api'
import { useTelegram } from './useTelegram'

export function useAuth() {
  const { initData } = useTelegram()
  const [member, setMember] = useState<Member | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const authenticate = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const existingToken = sessionStorage.getItem('jwt_token')
      if (existingToken) {
        // Verify token still valid by fetching dashboard
        try {
          const memberData = sessionStorage.getItem('member')
          if (memberData) {
            setMember(JSON.parse(memberData))
            setLoading(false)
            return
          }
        } catch {
          sessionStorage.removeItem('jwt_token')
          sessionStorage.removeItem('member')
        }
      }

      const payload = initData || 'user_id=0'
      const res = await client.post('/auth/validate', { init_data: payload })
      sessionStorage.setItem('jwt_token', res.data.token)
      sessionStorage.setItem('member', JSON.stringify(res.data.member))
      setMember(res.data.member)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Auth failed'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }, [initData])

  useEffect(() => {
    authenticate()
  }, [authenticate])

  return { member, loading, error, retry: authenticate }
}
