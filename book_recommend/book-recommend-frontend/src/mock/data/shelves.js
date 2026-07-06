// Mock 书架数据 — 完整 CRUD
// TODO: 替换为真实后端 API 调用

function delay(ms) { return new Promise(resolve => setTimeout(resolve, ms)) }

let _nextShelfId = 100
let _nextItemId = 1000

const SHELVES = [
  {
    id: 1, name: '想读', type: 'want_read', count: 4,
    items: [
      {id:101,book:{id:1,title:'三体',cover:'https://picsum.photos/seed/book1/200/280',author:'刘慈欣',rating:9.3},added_at:'2024-06-20 10:00:00',reading_progress:0},
      {id:102,book:{id:3,title:'百年孤独',cover:'https://picsum.photos/seed/book3/200/280',author:'加西亚·马尔克斯',rating:9.2},added_at:'2024-06-18 15:30:00',reading_progress:0},
      {id:103,book:{id:7,title:'1984',cover:'https://picsum.photos/seed/book7/200/280',author:'乔治·奥威尔',rating:9.3},added_at:'2024-06-15 09:00:00',reading_progress:0},
      {id:104,book:{id:14,title:'人类简史',cover:'https://picsum.photos/seed/book14/200/280',author:'尤瓦尔·赫拉利',rating:9.1},added_at:'2024-06-10 20:00:00',reading_progress:0},
    ]
  },
  {
    id: 2, name: '在读', type: 'reading', count: 3,
    items: [
      {id:201,book:{id:9,title:'三体II：黑暗森林',cover:'https://picsum.photos/seed/book9/200/280',author:'刘慈欣',rating:9.4},added_at:'2024-06-01 12:00:00',reading_progress:45},
      {id:202,book:{id:29,title:'思考，快与慢',cover:'https://picsum.photos/seed/book29/200/280',author:'丹尼尔·卡尼曼',rating:8.2},added_at:'2024-06-05 18:30:00',reading_progress:28},
      {id:203,book:{id:19,title:'局外人',cover:'https://picsum.photos/seed/book19/200/280',author:'阿尔贝·加缪',rating:9.0},added_at:'2024-06-12 08:00:00',reading_progress:72},
    ]
  },
  {
    id: 3, name: '已读', type: 'read', count: 4,
    items: [
      {id:301,book:{id:2,title:'活着',cover:'https://picsum.photos/seed/book2/200/280',author:'余华',rating:9.4},added_at:'2024-05-15 10:00:00',reading_progress:100},
      {id:302,book:{id:11,title:'嫌疑人X的献身',cover:'https://picsum.photos/seed/book11/200/280',author:'东野圭吾',rating:9.0},added_at:'2024-05-10 14:00:00',reading_progress:100},
      {id:303,book:{id:5,title:'小王子',cover:'https://picsum.photos/seed/book5/200/280',author:'安托万·德·圣-埃克苏佩里',rating:9.1},added_at:'2024-04-28 16:00:00',reading_progress:100},
      {id:304,book:{id:12,title:'追风筝的人',cover:'https://picsum.photos/seed/book12/200/280',author:'卡勒德·胡赛尼',rating:8.9},added_at:'2024-04-20 11:00:00',reading_progress:100},
    ]
  },
]

function _now() {
  return new Date().toISOString().slice(0, 19).replace('T', ' ')
}

export const mockShelves = {
  // ========== 获取书架列表 ==========
  async getShelves() {
    await delay(200)
    return { code: 200, message: 'success', data: { shelves: [...SHELVES] } }
  },

  // ========== 添加图书到书架 ==========
  async addItem(bookId, shelfType) {
    await delay(200)
    const shelf = SHELVES.find(s => s.type === shelfType)
    const names = { want_read: '想读', reading: '在读', read: '已读' }

    // 从 Mock 图书数据中查找真实图书信息
    let book = { id: bookId, title: '未知图书', cover: `https://picsum.photos/seed/book${bookId}/200/280`, author: '未知作者', rating: 8.0 }
    try {
      const { mockBooks } = await import('./books.js')
      const found = mockBooks._find(bookId)
      if (found) {
        book = { id: found.id, title: found.title, cover: found.cover, author: found.author, rating: found.rating }
      }
    } catch (e) { /* fallback to placeholder */ }

    const initialProgress = shelfType === 'read' ? 100 : 0
    const newItem = { id: _nextItemId++, book, added_at: _now(), reading_progress: initialProgress }
    if (shelf) {
      // 避免重复添加同一本书到同一书架
      const exists = shelf.items.some(it => it.book.id === bookId)
      if (!exists) {
        shelf.items.push(newItem)
        shelf.count = shelf.items.length
      }
    }
    return { code: 200, message: '添加成功', data: { ...newItem, shelf_name: names[shelfType] || shelfType, shelf_type: shelfType } }
  },

  // ========== 创建新书架 ==========
  async createShelf(name) {
    await delay(200)
    const newShelf = { id: _nextShelfId++, name, type: `custom_${_nextShelfId}`, count: 0, items: [] }
    SHELVES.push(newShelf)
    return { code: 200, message: '书架创建成功', data: newShelf }
  },

  // ========== 编辑书架名称 ==========
  async updateShelf(shelfId, name) {
    await delay(200)
    const shelf = SHELVES.find(s => s.id === shelfId)
    if (!shelf) return { code: 404, message: '书架不存在', data: null }
    shelf.name = name
    return { code: 200, message: '书架更新成功', data: shelf }
  },

  // ========== 删除书架 ==========
  async deleteShelf(shelfId) {
    await delay(200)
    const idx = SHELVES.findIndex(s => s.id === shelfId)
    if (idx === -1) return { code: 404, message: '书架不存在', data: null }
    const shelf = SHELVES[idx]
    if (['want_read', 'reading', 'read'].includes(shelf.type)) {
      return { code: 400, message: '系统默认书架不可删除', data: null }
    }
    SHELVES.splice(idx, 1)
    return { code: 200, message: '书架删除成功', data: { id: shelfId } }
  },

  // ========== 从书架移除图书 ==========
  async removeItem(itemId) {
    await delay(200)
    for (const shelf of SHELVES) {
      const idx = shelf.items.findIndex(it => it.id === itemId)
      if (idx !== -1) {
        const removed = shelf.items.splice(idx, 1)[0]
        shelf.count = shelf.items.length
        return { code: 200, message: '图书已从书架移除', data: removed }
      }
    }
    return { code: 404, message: '书架项目不存在', data: null }
  },

  // ========== 更新书架中图书（进度 + 移动） ==========
  async updateItem(itemId, { reading_progress, shelf_type } = {}) {
    await delay(200)
    let found = null, sourceShelf = null
    for (const shelf of SHELVES) {
      found = shelf.items.find(it => it.id === itemId)
      if (found) { sourceShelf = shelf; break }
    }
    if (!found) return { code: 404, message: '书架项目不存在', data: null }

    if (reading_progress !== undefined && reading_progress !== null) {
      found.reading_progress = Math.max(0, Math.min(100, reading_progress))
    }
    if (shelf_type !== undefined && shelf_type !== null && sourceShelf) {
      const targetShelf = SHELVES.find(s => s.type === shelf_type)
      if (targetShelf && targetShelf !== sourceShelf) {
        sourceShelf.items = sourceShelf.items.filter(it => it.id !== itemId)
        sourceShelf.count = sourceShelf.items.length
        if (shelf_type === 'read') found.reading_progress = 100
        targetShelf.items.push(found)
        targetShelf.count = targetShelf.items.length
      }
    }
    return { code: 200, message: '更新成功', data: { id: itemId, reading_progress: found.reading_progress } }
  },

  // ========== 更新阅读状态（兼容旧接口） ==========
  async updateStatus(itemId, status) {
    await delay(200)
    return { code: 200, message: '状态更新成功', data: { id: itemId, status, updated_at: _now() } }
  },
}
