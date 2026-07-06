import { mockBooks } from './books'

const REASONS = [
  '因为你喜欢{author}的作品',
  '与你最近阅读的风格相似',
  '喜欢「{tag}」标签的读者也在读',
  '与你口味相似的书友强烈推荐',
  '基于你的阅读历史智能推荐',
  '本周最受好评的图书之一',
  '这本书扩展了你的阅读边界',
  '近期社区讨论热烈的作品',
]

function delay(ms) { return new Promise(resolve => setTimeout(resolve, ms)) }

export const mockRecommendations = {
  async getFeed() {
    await delay(300)
    // Return 20 books with reason field
    const feedIds = [1,9,15,40,11,18,23,2,24,14,3,33,5,7,12,19,29,8,6,10]
    const items = feedIds.map((id, i) => {
      const book = mockBooks._find(id)
      if (!book) return null
      const reason = REASONS[i % REASONS.length]
        .replace('{author}', book.author)
        .replace('{tag}', book.tags[0]?.name || '')
      return { ...mockBooks._toBase(book), reason }
    }).filter(Boolean)
    return { code: 200, message: 'success', data: { items, total: items.length } }
  },

  async getSimilar(bookId) {
    await delay(300)
    const similarMap = {
      1: [9,15,40,30,22,7],
      2: [24,8,45,4,35,6],
      3: [33,48,19,36,10,42],
      11: [18,23,42,20,7,19],
    }
    const ids = similarMap[bookId] || [5,12,14,20,26,32]
    const reasons = ['相似的叙事风格','同类型经典','主题相近','读者常常一起阅读','相似的故事背景','题材相近']
    const items = ids.map((id, i) => {
      const book = mockBooks._find(id)
      return book ? { ...mockBooks._toBase(book), reason: reasons[i] } : null
    }).filter(Boolean)
    return { code: 200, message: 'success', data: { items } }
  },

  async getHot() {
    await delay(200)
    const hotIds = [1,2,12,6,3,9,5,18,14,7]
    const items = hotIds.map(id => {
      const book = mockBooks._find(id)
      return book ? mockBooks._toBase(book) : null
    }).filter(Boolean)
    return { code: 200, message: 'success', data: { items } }
  },

  async getNew() {
    await delay(200)
    const newIds = [23,43,52,50,51,27,30,46,21,39]
    const items = newIds.map(id => {
      const book = mockBooks._find(id)
      return book ? mockBooks._toBase(book) : null
    }).filter(Boolean)
    return { code: 200, message: 'success', data: { items } }
  },
}
