import request from './request'

export const authAPI = {
  async login(username, password) {
    return request.post('/auth/login', { username, password })
  },
  async register(username, password) {
    return request.post('/auth/register', { username, password })
  },
  async getProfile() {
    return request.get('/auth/profile')
  },
  async updateProfile(data) {
    return request.put('/user/profile', data)
  },
  async logout() {
    return request.post('/auth/logout')
  }
}
