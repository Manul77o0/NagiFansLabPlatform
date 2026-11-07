import axios from 'axios'

export const api = axios.create({
  withCredentials: true,
})

export async function getCurrentUser() {
  const response = await api.get('/api/users/me/')
  const user = response.data
  if (!user || typeof user !== 'object' || Array.isArray(user)
      || typeof user.id !== 'number' || typeof user.displayname !== 'string'
      || typeof user.level !== 'number') {
    throw new Error('Invalid current user response')
  }
  return user
}