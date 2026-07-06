// Mock 用户数据
// TODO: 替换为真实后端 API 调用

const MOCK_USER = {
  id: 1,
  username: 'admin',
  email: 'admin@bookrecommend.com',
  avatar: 'https://picsum.photos/seed/admin_avatar/80/80',
}

const MOCK_PROFILE = {
  id: 1,
  username: 'admin',
  email: 'admin@bookrecommend.com',
  avatar: 'https://picsum.photos/seed/admin_avatar/80/80',
  tags: ['科幻', '推理', '中国文学', '心理学', '历史'],
  liked_authors: ['刘慈欣', '余华', '东野圭吾', '加西亚·马尔克斯'],
  reading_stats: {
    this_week: { reading_minutes: 320, completed_books: 1 },
    this_month: { reading_minutes: 1420, completed_books: 4 },
    total_days: 156,
    daily_history: [
      { date: '06-19', minutes: 45 },
      { date: '06-20', minutes: 120 },
      { date: '06-21', minutes: 30 },
      { date: '06-22', minutes: 90 },
      { date: '06-23', minutes: 15 },
      { date: '06-24', minutes: 60 },
      { date: '06-25', minutes: 80 },
    ],
  },
}

export async function mockLogin(username, password) {
  await delay(300)
  if (username === 'admin' && password === '123456') {
    return {
      code: 200,
      message: '登录成功',
      data: {
        access_token: 'mock_token_abc123',
        token_type: 'bearer',
        user: MOCK_USER,
      }
    }
  }
  // Simulate error for wrong credentials
  return {
    code: 401,
    message: '用户名或密码错误',
    data: null,
  }
}

export async function mockRegister(username, password, email) {
  await delay(300)
  return {
    code: 200,
    message: '注册成功',
    data: {
      user: { id: 99, username, email, avatar: `https://picsum.photos/seed/${username}/80/80` }
    }
  }
}

export async function mockUserProfile() {
  await delay(200)
  return { code: 200, message: 'success', data: MOCK_PROFILE }
}

export const mockUser = {
  async getProfile() {
    return mockUserProfile()
  },
  async submitRating(bookId, score) {
    await delay(200)
    return { code: 200, message: '评分提交成功', data: { book_id: bookId, score } }
  },
  async recordClick(bookId) {
    await delay(100)
    return { code: 200, message: '行为记录成功', data: { book_id: bookId } }
  },
}

function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms))
}
