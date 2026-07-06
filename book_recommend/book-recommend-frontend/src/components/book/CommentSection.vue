<template>
  <div class="comment-section">
    <h3 class="section-title">读者评论 ({{ comments.length }})</h3>

    <!-- Comment input -->
    <div class="comment-input" v-if="userStore.isLoggedIn">
      <el-input
        v-model="content"
        type="textarea"
        :rows="3"
        placeholder="写下你的评论...（支持 Markdown 格式）"
        maxlength="2000"
        show-word-limit
      />
      <div class="input-actions">
        <span class="md-hint">支持 Markdown 语法</span>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          发布评论
        </el-button>
      </div>
    </div>
    <div v-else class="login-hint">
      <el-button type="primary" @click="$router.push('/login')">登录后发表评论</el-button>
    </div>

    <!-- Comment list -->
    <div class="comment-list">
      <div v-for="comment in comments" :key="comment.id" class="comment-item">
        <div class="comment-avatar">
          <el-avatar :size="40" :src="getAvatarUrl(comment.user_avatar, comment.user_name)" />
        </div>
        <div class="comment-body">
          <div class="comment-header">
            <span class="comment-user">{{ comment.user_name }}</span>
            <span class="comment-time">{{ comment.created_at }}</span>
          </div>
          <div class="comment-content" v-html="renderMarkdown(comment.content)"></div>
          <div class="comment-footer">
            <span
              class="like-btn"
              :class="{ liked: likedComments.has(comment.id) }"
              @click="handleLike(comment.id)"
            >
              <el-icon><CaretTop /></el-icon> {{ comment.likes }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useUserStore } from '../../stores/user'
import { commentsAPI } from '../../api/comments'
import { ElMessage } from 'element-plus'
import { getAvatarUrl } from '../../utils/avatar'

const props = defineProps({ bookId: { type: Number, required: true } })
const userStore = useUserStore()

const comments = ref([])
const content = ref('')
const submitting = ref(false)
const likedComments = ref(new Set())

async function loadComments(bookId) {
  if (!bookId) return
  const res = await commentsAPI.getByBook(bookId)
  if (res.code === 200) {
    comments.value = res.data.items
  }
}

onMounted(() => loadComments(props.bookId))

// 监听 bookId 变化：从书A切到书B时重新加载评论
watch(() => props.bookId, (newId) => {
  content.value = ''
  likedComments.value = new Set()
  loadComments(newId)
})

async function handleSubmit() {
  if (!content.value.trim()) {
    ElMessage.warning('请输入评论内容')
    return
  }
  submitting.value = true
  try {
    const res = await commentsAPI.create(props.bookId, content.value)
    if (res.code === 200) {
      comments.value.unshift(res.data)
      content.value = ''
      ElMessage.success('评论发布成功')
    }
  } finally {
    submitting.value = false
  }
}

async function handleLike(commentId) {
  if (likedComments.value.has(commentId)) {
    ElMessage.info('你已经点过赞了')
    return
  }
  const res = await commentsAPI.like(commentId)
  if (res.code === 200) {
    likedComments.value.add(commentId)
    const comment = comments.value.find(c => c.id === commentId)
    if (comment) comment.likes++
  }
}

function renderMarkdown(text) {
  // Simple markdown rendering (bold, italic, links)
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>')
}
</script>

<style scoped>
.comment-section {
  margin-top: 30px;
}
.section-title {
  font-size: 18px;
  color: #2C3E50;
  margin-bottom: 16px;
  padding-bottom: 10px;
  border-bottom: 2px solid #D4A24C;
}

.comment-input {
  margin-bottom: 20px;
}
.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}
.md-hint {
  font-size: 12px;
  color: #aaa;
}
.login-hint {
  text-align: center;
  padding: 20px;
  background: #F8F9FA;
  border-radius: 8px;
  margin-bottom: 20px;
}

.comment-item {
  display: flex;
  gap: 12px;
  padding: 16px 0;
  border-bottom: 1px solid #eee;
}
.comment-avatar {
  flex-shrink: 0;
}
.comment-body {
  flex: 1;
}
.comment-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}
.comment-user {
  font-weight: 600;
  color: #2C3E50;
  font-size: 14px;
}
.comment-time {
  font-size: 12px;
  color: #bbb;
}
.comment-content {
  font-size: 14px;
  color: #444;
  line-height: 1.6;
  margin-bottom: 8px;
}
.comment-footer {
  display: flex;
  align-items: center;
}
.like-btn {
  display: flex;
  align-items: center;
  gap: 2px;
  font-size: 13px;
  color: #999;
  cursor: pointer;
  padding: 2px 8px;
  border-radius: 4px;
  transition: all 0.2s;
}
.like-btn:hover, .like-btn.liked {
  color: #E67E22;
  background: #FFF3E0;
}
</style>
