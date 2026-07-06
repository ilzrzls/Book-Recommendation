import request from './request'

export const commentsAPI = {
  async getByBook(bookId) {
    return request.get(`/comments/book/${bookId}`)
  },
  async create(bookId, content) {
    return request.post('/comments', { book_id: bookId, content })
  },
  async like(commentId) {
    return request.post(`/comments/${commentId}/like`)
  },
}
