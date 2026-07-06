function delay(ms) { return new Promise(resolve => setTimeout(resolve, ms)) }

const COMMENTS = [
  {id:1,user_id:1,user_name:'书虫小明',user_avatar:'https://picsum.photos/seed/avatar1/40/40',content:'非常精彩的一本书！作者的想象力令人叹服，构建了一个宏大而又充满细节的宇宙。读完之后久久不能平静，对人类的未来有了更多思考。',likes:128,created_at:'2024-06-15 14:30:00'},
  {id:2,user_id:2,user_name:'文学爱好者',user_avatar:'https://picsum.photos/seed/avatar2/40/40',content:'花了三个晚上看完，意犹未尽。作者的叙事功底非常扎实，即使是科幻题材也能让人感同身受。强烈推荐！',likes:96,created_at:'2024-06-14 09:15:00'},
  {id:3,user_id:3,user_name:'思考者',user_avatar:'https://picsum.photos/seed/avatar3/40/40',content:'读完这本书，我开始重新思考我们在这个宇宙中的位置。它不仅仅是科幻，更是一部关于文明、道德和人性的哲学著作。',likes:85,created_at:'2024-06-13 22:00:00'},
  {id:4,user_id:4,user_name:'阅读达人',user_avatar:'https://picsum.photos/seed/avatar4/40/40',content:'前半部分铺垫略长，但后半部分简直让人停不下来。建议耐心读下去，你会发现一个全新的世界！',likes:67,created_at:'2024-06-12 16:45:00'},
  {id:5,user_id:5,user_name:'科幻迷',user_avatar:'https://picsum.photos/seed/avatar5/40/40',content:'中国科幻的里程碑之作！刘慈欣以一己之力把中国科幻提升到了世界水平。每个中国人都应该读一读。',likes:210,created_at:'2024-06-11 10:20:00'},
  {id:6,user_id:6,user_name:'书海拾贝',user_avatar:'https://picsum.photos/seed/avatar6/40/40',content:'第二遍读了，依然被震撼到。每次重读都会有新的发现和感悟。这就是好书的魅力所在吧。',likes:52,created_at:'2024-06-10 08:00:00'},
  {id:7,user_id:7,user_name:'闲云野鹤',user_avatar:'https://picsum.photos/seed/avatar7/40/40',content:'朋友推荐的，一开始没抱太大期望，没想到完全超出了预期。世界观设定太棒了！',likes:43,created_at:'2024-06-09 19:30:00'},
  {id:8,user_id:8,user_name:'夜读者',user_avatar:'https://picsum.photos/seed/avatar8/40/40',content:'熬夜看完了，虽然第二天上班很困但非常值得！剧情紧凑，人物塑造鲜明，五星好评！',likes:38,created_at:'2024-06-08 02:15:00'},
]

export const mockComments = {
  async getByBook(bookId) {
    await delay(200)
    const count = Math.min(3 + (bookId % 4), COMMENTS.length)
    return { code: 200, message: 'success', data: { items: COMMENTS.slice(0, count), total: count } }
  },
  async create(bookId, content) {
    await delay(200)
    return {
      code: 200, message: '评论发表成功',
      data: { id: Date.now(), user_id: 1, user_name: '当前用户', user_avatar: 'https://picsum.photos/seed/current_user/40/40', content, likes: 0, created_at: new Date().toISOString().slice(0,19).replace('T',' ') }
    }
  },
  async like(commentId) {
    await delay(100)
    return { code: 200, message: '点赞成功', data: { comment_id: commentId } }
  },
}
