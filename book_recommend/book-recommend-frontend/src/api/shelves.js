import request from './request'

export const shelvesAPI = {
  // 获取书架列表
  async getShelves() {
    return request.get('/shelves')
  },

  // 添加图书到书架
  async addItem(bookId, shelfType) {
    return request.post('/shelves/items', { book_id: bookId, shelf_type: shelfType })
  },

  // 创建新书架
  async createShelf(name) {
    return request.post('/shelves', { name })
  },

  // 编辑书架名称
  async updateShelf(shelfId, name) {
    return request.put(`/shelves/${shelfId}`, { name })
  },

  // 删除书架
  async deleteShelf(shelfId) {
    return request.delete(`/shelves/${shelfId}`)
  },

  // 从书架移除图书（按 book_id）
  async removeBook(bookId) {
    return request.post('/shelves/items/remove', { book_id: bookId })
  },
  // 从书架移除图书（按 item_id）
  async removeItem(itemId) {
    return request.delete(`/shelves/items/${itemId}`)
  },

  // 更新书架中的图书（进度 / 移动）
  async updateItem(itemId, data) {
    return request.put(`/shelves/items/${itemId}`, data)
  },

  // 更新阅读状态（兼容旧接口）
  async updateStatus(itemId, status) {
    return request.put(`/shelves/items/${itemId}/status`, { status })
  },
}
