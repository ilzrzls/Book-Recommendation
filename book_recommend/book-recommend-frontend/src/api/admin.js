import request from './request'

export const adminAPI = {
  // ── 系统概览 ──
  async getOverview() {
    return request.get('/admin/overview')
  },
  async getActivity(mode = 'weekly', offset = 0) {
    return request.get('/admin/activity', { params: { mode, offset } })
  },
  // ── 仪表盘 ──
  async getGraphStats() {
    return request.get('/admin/graph/stats')
  },
  async getGraphData(params = {}) {
    return request.get('/admin/graph/data', { params })
  },

  // ── 图书管理 ──
  async getBooks(page = 1, size = 20, keyword = '') {
    return request.get('/admin/books', { params: { page, size, keyword } })
  },
  async createBook(data) {
    return request.post('/admin/books', data)
  },
  async updateBook(id, data) {
    return request.put(`/admin/books/${id}`, data)
  },
  async deleteBook(id) {
    return request.delete(`/admin/books/${id}`)
  },

  // ── 用户管理 ──
  async getUsers(page = 1, size = 20, keyword = '', status = '') {
    return request.get('/admin/users', { params: { page, size, keyword, status } })
  },
  async updateUserStatus(id, status) {
    return request.put(`/admin/users/${id}/status`, { status })
  },

  // ── 评论管理 ──
  async getComments(page = 1, size = 20, bookId = null, status = '', keyword = '') {
    return request.get('/admin/comments', { params: { page, size, book_id: bookId, status, keyword } })
  },
  async deleteComment(id) {
    return request.delete(`/admin/comments/${id}`)
  },
  async pinComment(id, pinned) {
    return request.put(`/admin/comments/${id}/pin`, { pinned })
  },

}
