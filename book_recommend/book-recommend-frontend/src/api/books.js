import request from './request'

export const booksAPI = {
  async search(keyword = '', page = 1, size = 10, tags = '') {
    const params = { keyword, page, size }
    if (tags) params.tags = tags
    return request.get('/books/search', { params })
  },
  async getDetail(id) {
    return request.get(`/books/${id}`)
  },
  async getFeed() {
    return request.get('/books/feed')
  },
  async getSimilar(id) {
    return request.get(`/books/${id}/similar`)
  },
  async getHot() {
    return request.get('/books/hot')
  },
  async getNew() {
    return request.get('/books/new')
  },
  async getTop() {
    return request.get('/books/top')
  },
  async getFreeRank() {
    return request.get('/books/free-rank')
  },
  async getPaidRank() {
    return request.get('/books/paid-rank')
  },
  async getModernLiterature() {
    return request.get('/books/modern-literature')
  },
}
