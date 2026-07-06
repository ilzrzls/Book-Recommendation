import request from './request'

export const userAPI = {
  async getProfile() {
    return request.get('/user/profile')
  },
  async getComments() {
    return request.get('/user/comments')
  },
  async submitRating(bookId, score) {
    return request.post('/user/rating', { book_id: bookId, score })
  },
  async recordClick(bookId) {
    return request.post('/user/click', { book_id: bookId })
  },
}
