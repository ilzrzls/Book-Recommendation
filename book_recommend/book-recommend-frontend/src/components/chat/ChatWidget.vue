<template>
  <!-- ================================================================
       悬浮入口：可拖拽Q版紫发猫耳少年 AI 助手挂件
       素材：AI_interface/interface/1~13.png 序列帧
       ================================================================ -->
  <div
    v-if="!visible"
    ref="triggerRef"
    class="cat-trigger"
    :class="{ 'cat-dragging': isDragging, 'cat-hover': isHover }"
    :style="{ left: posX + 'px', top: posY + 'px' }"
    @mousedown="onDragStart"
    @touchstart.prevent="onDragStart"
    @mouseenter="isHover = true"
    @mouseleave="isHover = false"
    @click="onTriggerClick"
  >
    <!-- 序列帧小猫动画（透明底PNG，无外圈） -->
    <img
      :src="`/AI_interface/interface/${currentFrame}.png`"
      alt="图图"
      class="cat-sprite"
      draggable="false"
    />

    <!-- 提示文字 -->
    <span class="cat-tooltip">AI 图图｜和图图遨游书海</span>
  </div>

  <!-- ================================================================
       聊天弹窗（保留全部原有功能，仅头像替换为 head.png）
       ================================================================ -->
  <Teleport to="body">
    <Transition name="tutu-modal">
      <div v-if="visible" class="tutu-overlay" @click.self="visible = false">
        <div class="tutu-dialog">
          <!-- 左侧边栏 -->
          <aside class="tutu-sidebar">
            <!-- 大头像：强制使用 head.png -->
            <div class="sidebar-avatar">
              <img src="/AI_interface/head.png" alt="图图" class="avatar-img" />
            </div>
            <h3 class="sidebar-name">图图</h3>
            <p class="sidebar-desc">阅读智能助手</p>
            <nav class="sidebar-actions">
              <button class="sb-btn-new" @click="newSession">＋ 新对话</button>
            </nav>
            <div class="history-section">
              <h4 class="history-title">💬 历史对话 ({{ sessions.length }})</h4>
              <div class="history-list">
                <div v-for="s in pinnedSessions" :key="s.id" class="history-item pinned" :class="{active: s.id === sessionId}" @click="selectSession(s.id)">
                  <span class="hi-pin">📌</span><span class="hi-title">{{ s.title }}</span>
                  <button class="hi-btn" @click.stop="togglePin(s.id)">📌</button>
                  <button class="hi-btn" @click.stop="editTitle(s)">✎</button>
                  <button class="hi-del" @click.stop="deleteSession(s.id)">✕</button>
                </div>
                <div v-for="s in unpinnedSessions" :key="s.id" class="history-item" :class="{active: s.id === sessionId}" @click="selectSession(s.id)">
                  <span class="hi-title">{{ s.title }}</span>
                  <button class="hi-btn" @click.stop="togglePin(s.id)">📌</button>
                  <button class="hi-btn" @click.stop="editTitle(s)">✎</button>
                  <button class="hi-del" @click.stop="deleteSession(s.id)">✕</button>
                </div>
                <button v-if="sessions.length > 0" class="clear-all-btn" @click="clearAllHistory">清空全部历史</button>
              </div>
            </div>
            <!-- 快捷提问 -->
            <div class="preset-section">
              <h4 class="preset-section-title">💡 快捷提问</h4>
              <div class="preset-groups">
                <div class="preset-group" v-for="group in presetGroups" :key="group.label">
                  <div class="pg-label" @click="togglePresetGroup(group.label)" :class="{ expanded: expandedGroup === group.label }">
                    <span>{{ group.icon }} {{ group.label }}</span>
                    <span class="pg-arrow">{{ expandedGroup === group.label ? '▾' : '▸' }}</span>
                  </div>
                  <div class="pg-items" v-show="expandedGroup === group.label">
                    <button v-for="q in group.items" :key="q" @click="send(q)">{{ q }}</button>
                  </div>
                </div>
              </div>
            </div>
          </aside>

          <!-- 右侧聊天主区 -->
          <div class="tutu-main">
            <div class="tutu-titlebar">
              <span>图图{{ bookTitle ? ' · 《' + bookTitle + '》' : '' }}</span>
              <button @click="visible = false" class="tb-close">✕</button>
            </div>
            <!-- 欢迎页 -->
            <template v-if="messages.length === 0">
              <div class="welcome-area">
                <div class="welcome-icon">
                  <img src="/AI_interface/head.png" alt="图图" class="welcome-head-img" />
                </div>
                <h2 class="welcome-title">嗨，我是图图 👋</h2>
                <p class="welcome-sub" v-if="bookTitle">你正在读《{{ bookTitle }}》，想了解什么？</p>
                <p class="welcome-sub" v-else>你的专属阅读助手，荐好书、解剧情、整笔记</p>
                <div class="preset-cards">
                  <div class="preset-card" v-for="group in presetGroups" :key="group.label">
                    <div class="pc-label">{{ group.icon }} {{ group.label }}</div>
                    <button v-for="q in group.items" :key="q" @click="send(q)">{{ q }}</button>
                  </div>
                </div>
              </div>
            </template>
            <!-- 消息列表 -->
            <div class="tutu-messages" ref="msgRef" v-if="messages.length > 0">
              <div v-for="(msg, i) in messages" :key="i" :class="['tutu-msg', msg.role]">
                <!-- AI 头像：强制使用 head.png -->
                <div v-if="msg.role === 'assistant'" class="msg-avatar-mini">
                  <img src="/AI_interface/head.png" alt="图图" class="msg-avatar-img" />
                </div>
                <div class="msg-bubble">
                  <span v-html="renderMsg(msg.content)"></span>
                  <div v-if="msg.role === 'assistant' && i === messages.length - 1 && !loading" class="followup-chips">
                    <span class="followup-label">💡 你可能还想问</span>
                    <div class="followup-row">
                      <button v-for="q in followupQuestions" :key="q" @click="send(q)">{{ q }}</button>
                    </div>
                  </div>
                </div>
                <el-avatar v-if="msg.role === 'user'" :size="28" :src="getAvatarUrl(userStore.userInfo?.avatar, userStore.username)" />
              </div>
              <!-- 加载中：AI 头像也用 head.png -->
              <div v-if="loading" class="tutu-msg assistant">
                <div class="msg-avatar-mini typing-avatar">
                  <img src="/AI_interface/head.png" alt="图图" class="msg-avatar-img" />
                </div>
                <div class="msg-bubble typing-dots"><span></span><span></span><span></span></div>
              </div>
            </div>
            <!-- 输入栏 -->
            <div class="tutu-input-bar">
              <textarea v-model="input" placeholder="和图图聊聊..." rows="1" @keydown.enter.exact.prevent="send()" @input="autoGrow" ref="inputRef" :disabled="loading"></textarea>
              <button @click="send()" :disabled="!input.trim() || loading" class="send-btn">
                <svg viewBox="0 0 24 24" width="20" height="20"><path d="M2 21l21-9L2 3v7l15 2-15 2v7z" fill="currentColor"/></svg>
              </button>
            </div>
          </div>
          <!-- 移动端 -->
          <div class="tutu-mobile-tabs">
            <button @click="quickSend(presetGroups[0].items[0])">📚 书单</button>
            <button @click="quickSend(presetGroups[1].items[0])">🔍 解析</button>
            <button @click="quickSend(presetGroups[2].items[0])">📝 笔记</button>
            <button @click="newSession">🗑️ 新对话</button>
          </div>
        </div>
      </div>
    </Transition>
    <!-- 编辑标题弹窗 -->
    <Teleport to="body">
      <div v-if="titleEdit.visible" class="tutu-mini-overlay" @click.self="titleEdit.visible = false">
        <div class="tutu-mini-dialog">
          <p>编辑会话标题</p>
          <input v-model="titleEdit.text" @keyup.enter="confirmEditTitle" placeholder="输入新标题" maxlength="30" />
          <div class="mini-btns"><button @click="titleEdit.visible = false">取消</button><button @click="confirmEditTitle" class="btn-ok">确认</button></div>
        </div>
      </div>
    </Teleport>
  </Teleport>
</template>

<script setup>
// ═══════════════════════════════════════════════════════════════
// 一、拖拽逻辑 (PC鼠标 + 手机触屏)
// ═══════════════════════════════════════════════════════════════
import { ref, computed, reactive, nextTick, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../../stores/user'
import { getAvatarUrl } from '../../utils/avatar'
import request from '../../api/request'

const props = defineProps({ bookId: { type: Number, default: null }, bookTitle: { type: String, default: '' } })
const router = useRouter(); const userStore = useUserStore()
const visible = ref(false); const sessionId = ref(null); const input = ref('')
const loading = ref(false); const messages = ref([]); const msgRef = ref(null); const inputRef = ref(null)
const triggerRef = ref(null); const isHover = ref(false)

// 拖拽状态
const isDragging = ref(false)
const dragStartX = ref(0); const dragStartY = ref(0)
const posX = ref(0); const posY = ref(0)
let hasMoved = false
const uidSuffix = computed(() => userStore.userInfo?.id || 'anon')
const POS_KEY = computed(() => 'tutu_cat_pos_' + uidSuffix.value)

function loadPosition() {
  try {
    const s = JSON.parse(localStorage.getItem(POS_KEY.value))
    if (s && typeof s.x === 'number') { posX.value = s.x; posY.value = s.y; return }
  } catch {}
  posX.value = window.innerWidth - 130; posY.value = 80
}
loadPosition()
function savePosition() { localStorage.setItem(POS_KEY.value, JSON.stringify({ x: posX.value, y: posY.value })) }
watch(uidSuffix, () => loadPosition())

function onDragStart(e) {
  const pt = e.touches ? e.touches[0] : e
  dragStartX.value = pt.clientX; dragStartY.value = pt.clientY; hasMoved = false
  document.addEventListener('mousemove', onDragMove); document.addEventListener('mouseup', onDragEnd)
  document.addEventListener('touchmove', onDragMove, { passive: false }); document.addEventListener('touchend', onDragEnd)
}
function onDragMove(e) {
  const pt = e.touches ? e.touches[0] : e
  const dx = pt.clientX - dragStartX.value; const dy = pt.clientY - dragStartY.value
  if (Math.abs(dx) < 2 && Math.abs(dy) < 2) return
  hasMoved = true; isDragging.value = true
  posX.value += dx; posY.value += dy
  const el = triggerRef.value; const w = el ? el.offsetWidth : 100; const h = el ? el.offsetHeight : 100
  posX.value = Math.max(0, Math.min(window.innerWidth - w, posX.value))
  posY.value = Math.max(0, Math.min(window.innerHeight - h, posY.value))
  dragStartX.value = pt.clientX; dragStartY.value = pt.clientY
}
function onDragEnd() {
  isDragging.value = false; savePosition()
  document.removeEventListener('mousemove', onDragMove); document.removeEventListener('mouseup', onDragEnd)
  document.removeEventListener('touchmove', onDragMove); document.removeEventListener('touchend', onDragEnd)
}
function onTriggerClick() { if (hasMoved) { hasMoved = false; return }; open() }

// ═══════════════════════════════════════════════════════════════
// 二、序列帧动画 (1~13.png 循环轮播)
// ═══════════════════════════════════════════════════════════════
const FRAME_COUNT = 13
const currentFrame = ref(1)
let frameTimer = null
const IDLE_INTERVAL = 380   // 待机帧间隔 (ms)，比之前慢一点

function startFrameAnim() {
  stopFrameAnim()
  frameTimer = setInterval(() => {
    currentFrame.value = currentFrame.value >= FRAME_COUNT ? 1 : currentFrame.value + 1
  }, IDLE_INTERVAL)
}
function stopFrameAnim() { if (frameTimer) { clearInterval(frameTimer); frameTimer = null } }

onMounted(() => { startFrameAnim() })
onBeforeUnmount(() => { stopFrameAnim() })

// ═══════════════════════════════════════════════════════════════
// 三、弹窗交互（保留全部原有功能）
// ═══════════════════════════════════════════════════════════════
const expandedGroup = ref(null)
const presetGroups = [
  { icon: '📚', label: '书单推荐', items: ['推荐高分治愈文学','悬疑推理好书清单','适合学生的经典名著','睡前短篇读物推荐','职场成长书籍推荐','科幻奇幻口碑合集','小众散文诗集推荐'] },
  { icon: '🔍', label: '书籍解析', items: ['梳理这本书完整剧情','分析书中人物形象','解读作品核心主旨','对比两本书的异同','摘录书中经典金句'] },
  { icon: '📝', label: '阅读工具', items: ['整理读书笔记模板','制定一周阅读计划','同类书籍拓展推荐','生僻字词典故查询'] },
]
function togglePresetGroup(l) { expandedGroup.value = expandedGroup.value === l ? null : l }

// 历史对话
const sessions = ref([])
const SESS_KEY = computed(() => 'tutu_chat_sessions_' + uidSuffix.value)
function loadSessions() { try { sessions.value = JSON.parse(localStorage.getItem(SESS_KEY.value) || '[]') } catch { sessions.value = [] } }
function saveSessions() { localStorage.setItem(SESS_KEY.value, JSON.stringify(sessions.value)) }
function autoTitle(ms) {
  const um = ms.filter(m => m.role === 'user').slice(0, 2)
  if (!um.length) return '新对话'
  const j = um.map(m => m.content).join(' ').replace(/\s/g, '')
  return j.slice(0, 25) + (j.length > 25 ? '…' : '')
}
function upsertSession(id, title, ms) {
  const idx = sessions.value.findIndex(s => s.id === id)
  const ex = idx >= 0 ? sessions.value[idx] : {}
  const e = { id, title: (ex.title && ex.title !== '新对话') ? ex.title : (title || autoTitle(ms)), updated_at: new Date().toISOString().slice(0,19), messageCount: ms.length, pinned: ex.pinned || false }
  if (idx >= 0) sessions.value[idx] = e; else sessions.value.unshift(e); saveSessions()
}
function deleteSession(id) { sessions.value = sessions.value.filter(s => s.id !== id); saveSessions(); if (sessionId.value === id) { sessionId.value = null; messages.value = [] } }
function clearAllHistory() { sessions.value = []; saveSessions(); sessionId.value = null; messages.value = [] }
async function selectSession(id) {
  const s = sessions.value.find(x => x.id === id); if (!s) return; sessionId.value = id
  // 优先从后端加载已清洗的消息，回退到 localStorage
  let loaded = false
  try {
    const res = await request.get('/chat/sessions/' + id + '/messages')
    if (res.code === 200 && res.data.messages?.length) {
      messages.value = res.data.messages
      localStorage.setItem('tutu_msgs_' + uidSuffix.value + '_' + id, JSON.stringify(messages.value))
      loaded = true
    }
  } catch {}
  if (!loaded) {
    try { const st = localStorage.getItem('tutu_msgs_' + uidSuffix.value + '_' + id); if (st) messages.value = JSON.parse(st) } catch { messages.value = [] }
  }
  nextTick(() => { if (msgRef.value) msgRef.value.scrollTop = msgRef.value.scrollHeight })
}
function togglePin(id) { const s = sessions.value.find(x => x.id === id); if (!s) return; s.pinned = !s.pinned; saveSessions() }
const titleEdit = reactive({ visible: false, sessionId: null, text: '' })
function editTitle(s) { titleEdit.visible = true; titleEdit.sessionId = s.id; titleEdit.text = s.title }
function confirmEditTitle() { const s = sessions.value.find(x => x.id === titleEdit.sessionId); if (!s) return; s.title = titleEdit.text.trim() || s.title; saveSessions(); titleEdit.visible = false }
const pinnedSessions = computed(() => sessions.value.filter(s => s.pinned))
const unpinnedSessions = computed(() => sessions.value.filter(s => !s.pinned))

// 智能追问
const followupQuestions = computed(() => {
  const ms = messages.value; if (!ms.length) return []
  const ut = ms.filter(m => m.role === 'user').map(m => m.content)
  const last = ut[ut.length - 1] || ''; const all = ut.join(' '); const qs = []
  const patterns = [
    { keys: ['推荐','好书','书单','清单','值得','必读','入门'], qs: ['有评分更高的同类书吗？','推荐一些冷门但好看的','适合初学者的还有哪些？'] },
    { keys: ['科幻','奇幻','悬疑','推理','武侠','历史小说'], qs: ['这个类别还有哪些经典必读？','有类似题材但不同作者的推荐吗？'] },
    { keys: ['文学','散文','诗歌','哲学','心理','经济'], qs: ['这个领域有哪些入门必读？','能推荐这个领域的进阶书单吗？'] },
    { keys: ['剧情','情节','结局','故事','讲了','写了什么'], qs: ['能详细梳理一下故事线吗？','能分析一下主要人物性格吗？'] },
    { keys: ['作者','作家','写作','背景','生平'], qs: ['该作者还有什么代表作？','能介绍作者的生平和创作背景吗？'] },
    { keys: ['笔记','读书笔记','整理','总结','摘录','金句'], qs: ['能帮我整理章节摘要吗？','这本书有哪些经典段落？'] },
    { keys: ['阅读','看书','计划','目标','速度'], qs: ['如何制定一个合理的阅读计划？','每天读多少页比较合适？'] },
    { keys: ['评分','评价','口碑','热度','畅销','排行'], qs: ['今年有哪些高分新书？','评分最高的是哪几本？'] },
    { keys: ['对比','比较','区别','异同','哪个好'], qs: ['能再详细对比一下吗？','同主题下还有哪些值得推荐？'] },
    { keys: ['电影','电视剧','改编','影视','翻拍'], qs: ['还有哪些被成功改编为影视的书？','这个原著和改编版区别大吗？'] },
  ]
  for (const { keys, qs: pq } of patterns) {
    if (keys.some(k => last.includes(k))) pq.forEach(q => { if (!qs.includes(q)) qs.push(q) })
    else if (keys.some(k => all.includes(k))) pq.forEach(q => { if (!qs.includes(q)) qs.push(q) })
  }
  const bm = all.match(/《([^》]+)》/g)
  if (bm?.length) ['这本书的核心思想是什么？','有类似主题的其他书推荐吗？'].forEach(q => { if (!qs.includes(q)) qs.push(q) })
  if (ut.length >= 2) ['能结合我的阅读偏好精准推荐几本吗？'].forEach(q => { if (!qs.includes(q)) qs.push(q) })
  if (ut.length >= 4) ['换个话题，推荐其他类型的书','帮我总结一下我们聊了哪些书'].forEach(q => { if (!qs.includes(q)) qs.push(q) })
  if (qs.length < 4) {
    if (props.bookTitle) {
      [`《${props.bookTitle}》的核心思想是什么？`,'能推荐几本类似的书吗？'].forEach(q => { if (!qs.includes(q)) qs.push(q) })
    } else {
      const pools = [['有哪些评分最高的书值得一读？','推荐几本近期热门的书','推荐适合睡前阅读的书'],['能推荐几本经典文学名著吗？','有没有让人欲罢不能的悬疑小说？','推荐几本能提升思维的书'],['最近流行什么类型的书？','能推荐让人醍醐灌顶的书吗？','适合通勤路上读的书有哪些？']]
      pools[ut.length % pools.length].forEach(q => { if (!qs.includes(q)) qs.push(q) })
    }
  }
  return qs.slice(0, 5)
})

watch(messages, (val) => { if (sessionId.value) { localStorage.setItem('tutu_msgs_' + uidSuffix.value + '_' + sessionId.value, JSON.stringify(val)); upsertSession(sessionId.value, '', val) } }, { deep: true })

function open() { visible.value = true; nextTick(() => { if (msgRef.value) msgRef.value.scrollTop = msgRef.value.scrollHeight }) }
async function send(text) {
  const msg = (text || input.value).trim(); if (!msg || loading.value) return
  if (!userStore.isLoggedIn) { messages.value.push({ role: 'assistant', content: '请先登录后再使用AI助手功能。' }); return }
  input.value = ''; messages.value.push({ role: 'user', content: msg }); loading.value = true
  nextTick(() => { if (msgRef.value) msgRef.value.scrollTop = msgRef.value.scrollHeight })
  try {
    const res = await request.post('/chat/send', { session_id: sessionId.value, book_id: props.bookId, message: msg })
    if (res.code === 200) { sessionId.value = res.data.session_id; messages.value.push({ role: 'assistant', content: res.data.reply }) }
    else messages.value.push({ role: 'assistant', content: '抱歉，服务异常' })
  } catch { messages.value.push({ role: 'assistant', content: '网络请求失败，请稍后重试。' }) }
  loading.value = false; nextTick(() => { if (msgRef.value) msgRef.value.scrollTop = msgRef.value.scrollHeight })
}
function quickSend(t) { send(t) }
function newSession() { sessionId.value = null; messages.value = []; expandedGroup.value = null }
function autoGrow() { const el = inputRef.value; if (el) { el.style.height = 'auto'; el.style.height = Math.min(el.scrollHeight, 100) + 'px' } }
function renderMsg(text) {
  return text
    // 删除所有 （book:数字） 和 (book:数字) 残留（全角/半角括号通杀）
    .replace(/[（(]book[:：]\d+[）)]/g, '')
    // 删除所有 【 】 [ ] 括号
    .replace(/[【】\[\]]/g, '')
    // 书籍链接 → 金色可点击链接（仅保留《书名》）
    .replace(/《(.*?)》\(book:(\d+)\)/g, '<a href=\"/book/$2\" class=\"tutu-book-link\"><strong style=\"color:#D4731A;border-bottom:1.5px solid #D4731A\">《$1》</strong></a>')
    // 《书名》无链接版本 → 金色文字
    .replace(/《(.*?)》/g, '<strong style=\"color:#D4731A\">《$1》</strong>')
    // Markdown
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\*(.*?)\*/g, '<em>$1</em>').replace(/\n/g, '<br>')
}
function handleMsgClick(e) { const link = e.target.closest('.tutu-book-link'); if (link) { e.preventDefault(); router.push(link.getAttribute('href')) } }
watch(visible, (v) => { nextTick(() => { if (v && msgRef.value) msgRef.value.addEventListener('click', handleMsgClick) }) })
loadSessions()
</script>

<style scoped>
/* ═══════════════════════════════════════════════════════════════
   小猫挂件样式（透明底PNG，无外圈/光晕/呼吸）
   ═══════════════════════════════════════════════════════════════ */
.cat-trigger {
  position: fixed; z-index: 9999;
  width: 200px; height: 200px; cursor: grab; user-select: none;
  display: flex; align-items: center; justify-content: center;
  transition: transform 0.15s; background: transparent;
}
.cat-trigger:active { cursor: grabbing; }
.cat-trigger.cat-dragging { cursor: grabbing; transition: none; }

/* 点击弹跳 */
.cat-trigger:not(.cat-dragging):active { animation: cat-bounce 0.35s ease; }
@keyframes cat-bounce {
  0% { transform: scale(1); }
  30% { transform: scale(1.1); }
  60% { transform: scale(0.92); }
  100% { transform: scale(1); }
}

/* 小猫精灵图（透明底，无外框） */
.cat-sprite { width: 100%; height: 100%; object-fit: contain; display: block; pointer-events: none; background: transparent !important; }

/* 提示 */
.cat-tooltip {
  position: absolute; bottom: 10px; left: 50%; transform: translateX(-50%);
  background: rgba(255,255,255,0.75); color: #2C3E50; font-size: 12px; font-weight: 600;
  padding: 5px 14px; border-radius: 14px; white-space: nowrap; pointer-events: none;
  backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.6);
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
}
/* ═══════════════════════════════════════════════════════════════
   弹窗样式（保留原有设计）
   ═══════════════════════════════════════════════════════════════ */
.tutu-overlay { position: fixed; inset: 0; z-index: 10000; background: rgba(26,54,80,0.45); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; }
.tutu-dialog { width: 1000px; max-width: 98vw; height: 730px; max-height: 95vh; background: #FDFBF7; border-radius: 20px; display: flex; overflow: hidden; box-shadow: 0 24px 64px rgba(26,54,80,0.3); }
.tutu-modal-enter-active { animation: tdIn 0.25s ease; }
.tutu-modal-leave-active { animation: tdIn 0.18s ease reverse; }
@keyframes tdIn { from { opacity:0; transform:scale(0.95) } to { opacity:1; transform:scale(1) } }

.tutu-sidebar { width: 250px; flex-shrink: 0; background: #F8F3E8; padding: 22px 16px; display: flex; flex-direction: column; align-items: center; border-right: 1px solid #e8dfce; overflow-y: auto; }
.sidebar-avatar { width: 60px; height: 60px; border-radius: 50%; overflow: hidden; border: 2.5px solid #D4A24C; margin-bottom: 8px; flex-shrink: 0; }
.avatar-img { width: 100%; height: 100%; object-fit: cover; display: block; }
.sidebar-name { font-size: 16px; font-weight: 700; color: #2C3E50; margin: 0; }
.sidebar-desc { font-size: 11px; color: #999; margin: 2px 0 12px; }
.sidebar-actions { width: 100%; display: flex; flex-direction: column; gap: 4px; flex-shrink: 0; }
.sb-btn-new { width: 100%; padding: 8px 12px; border: 1.5px dashed #D4A24C; border-radius: 10px; background: transparent; color: #D4A24C; font-size: 14px; cursor: pointer; transition: all 0.2s; font-weight: 600; }
.sb-btn-new:hover { background: #D4A24C; color: #fff; border-style: solid; }
.history-section { width: 100%; margin-top: 12px; border-top: 1px solid #e8dfce; padding-top: 10px; }
.history-title { font-size: 13px; font-weight: 600; color: #888; margin: 0 0 6px; }
.history-list { max-height: 150px; overflow-y: auto; }
.history-item { display: flex; align-items: center; gap: 4px; padding: 5px 6px; cursor: pointer; border-radius: 6px; font-size: 13px; }
.history-item:hover { background: #fff; }
.history-item.active { background: #FFF8E1; }
.hi-title { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #555; }
.hi-del { background: none; border: none; color: #ccc; cursor: pointer; font-size: 12px; padding: 1px 3px; border-radius: 3px; }
.hi-del:hover { color: #e74c3c; background: #fde8e8; }
.hi-pin { font-size: 12px; flex-shrink: 0; }
.hi-btn { background: none; border: none; color: #ccc; cursor: pointer; font-size: 12px; padding: 1px 3px; border-radius: 3px; flex-shrink: 0; }
.hi-btn:hover { color: #D4A24C; background: #FFF8E1; }
.history-item.pinned { background: #FFF8E1; }
.clear-all-btn { width: 100%; margin-top: 6px; padding: 5px; border: 1px solid #f0c8c0; background: transparent; color: #c0392b; font-size: 12px; cursor: pointer; border-radius: 6px; }
.clear-all-btn:hover { background: #fde8e8; }

.preset-section { width: 100%; margin-top: 10px; border-top: 1px solid #e8dfce; padding-top: 10px; }
.preset-section-title { font-size: 13px; font-weight: 600; color: #888; margin: 0 0 6px; }
.preset-groups { display: flex; flex-direction: column; gap: 2px; }
.preset-group { border-radius: 6px; overflow: hidden; }
.pg-label { display: flex; align-items: center; justify-content: space-between; padding: 6px 8px; font-size: 13px; color: #555; cursor: pointer; border-radius: 6px; transition: background 0.15s; user-select: none; }
.pg-label:hover { background: #fff; }
.pg-label.expanded { background: #FFF8E1; color: #8B6914; font-weight: 600; }
.pg-arrow { font-size: 14px; color: #aaa; }
.pg-items { padding: 4px 8px 6px 14px; display: flex; flex-direction: column; gap: 3px; }
.pg-items button { display: block; width: 100%; text-align: left; padding: 4px 8px; border: none; background: transparent; border-radius: 4px; font-size: 13px; color: #777; cursor: pointer; transition: all 0.15s; font-family: inherit; line-height: 1.4; }
.pg-items button:hover { background: #FFF3D6; color: #8B6914; }

/* 右侧主区 */
.tutu-main { flex: 1; display: flex; flex-direction: column; min-width: 0; background: #FEFCF9; }
.tutu-titlebar { display: flex; align-items: center; justify-content: space-between; padding: 10px 18px; font-size: 14px; font-weight: 600; color: #2C3E50; background: #F8F3E8; border-bottom: 1px solid #e8dfce; flex-shrink: 0; }
.tb-close { background: none; border: none; font-size: 18px; color: #999; cursor: pointer; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; }
.tb-close:hover { background: rgba(0,0,0,0.06); color: #333; }

.welcome-area { flex: 1; overflow-y: auto; display: flex; flex-direction: column; align-items: center; padding: 36px 28px 24px; }
.welcome-icon { margin-bottom: 12px; }
.welcome-head-img { width: 68px; height: 68px; border-radius: 50%; object-fit: cover; }
.welcome-title { font-size: 20px; font-weight: 700; color: #1a3650; margin: 0 0 4px; }
.welcome-sub { font-size: 13px; color: #999; margin: 0 0 24px; }
.preset-cards { width: 100%; max-width: 650px; display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.preset-card { background: #fff; border-radius: 14px; padding: 16px; box-shadow: 0 1px 4px rgba(0,0,0,0.04); border: 1px solid #f0ebe0; }
.pc-label { font-size: 12px; font-weight: 700; color: #8B6914; margin-bottom: 10px; }
.preset-card button { display: block; width: 100%; text-align: left; padding: 7px 12px; margin-bottom: 4px; border: none; background: #FAF7F2; border-radius: 8px; font-size: 12.5px; color: #555; cursor: pointer; transition: all 0.15s; line-height: 1.5; }
.preset-card button:last-child { margin-bottom: 0; }
.preset-card button:hover { background: #FFF3D6; color: #8B6914; transform: translateX(3px); }

.tutu-messages { flex: 1; overflow-y: auto; padding: 18px; background: linear-gradient(180deg, #FDFBF7 0%, #F8F4EC 100%); scroll-behavior: smooth; }
.tutu-msg { display: flex; gap: 10px; margin-bottom: 16px; align-items: flex-end; animation: msgIn 0.25s ease; }
@keyframes msgIn { from { opacity:0; transform:translateY(8px) } to { opacity:1; transform:translateY(0) } }
.tutu-msg.user { flex-direction: row-reverse; }
.msg-avatar-mini { flex-shrink: 0; width: 28px; height: 28px; border-radius: 50%; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.1); }
.msg-avatar-img { width: 100%; height: 100%; object-fit: cover; display: block; }
.typing-avatar { animation: avBounce 0.7s ease-in-out infinite; }
@keyframes avBounce { 0%,100% { transform:translateY(0) } 50% { transform:translateY(-5px) } }
.msg-bubble { max-width: 78%; padding: 14px 18px; border-radius: 16px; font-size: 14.5px; line-height: 1.7; word-break: break-word; }
.tutu-msg.assistant .msg-bubble { background: #fff; color: #2C3E50; border-bottom-left-radius: 4px; box-shadow: 0 1px 4px rgba(0,0,0,0.05); border: 1px solid #f0ebe0; }
.tutu-msg.user .msg-bubble { background: linear-gradient(135deg, #EDF4FC, #DBE8F8); color: #1a3650; border-bottom-right-radius: 4px; }
.typing-dots { display:flex; gap:5px; padding:14px 18px; }
.typing-dots span { width:8px; height:8px; border-radius:50%; background:#bcc9d6; animation:dotB 1.4s infinite both; }
.typing-dots span:nth-child(2) { animation-delay:0.2s } .typing-dots span:nth-child(3) { animation-delay:0.4s }
@keyframes dotB { 0%,80%,100% {transform:scale(0.4)} 40% {transform:scale(1)} }
.tutu-book-link { color:#D4731A; font-weight:600; text-decoration:none; border-bottom:1.5px solid #D4731A; cursor:pointer; }

.followup-chips { margin-top: 12px; padding-top: 10px; border-top: 1px solid #f0ebe0; }
.followup-label { font-size: 11px; color: #aaa; display: block; margin-bottom: 8px; }
.followup-row { display: flex; flex-wrap: wrap; gap: 6px; }
.followup-row button { padding: 5px 12px; border: 1px solid #D4A24C; background: #FFF8E1; color: #B07D1A; border-radius: 14px; font-size: 11.5px; cursor: pointer; white-space: nowrap; transition: all 0.15s; }
.followup-row button:hover { background: #D4A24C; color: #fff; }

.tutu-input-bar { display: flex; align-items: flex-end; gap: 10px; padding: 10px 18px; border-top: 1px solid #f0ebe0; flex-shrink: 0; background: #fff; }
.tutu-input-bar textarea { flex: 1; border: 1.5px solid #e8dfce; border-radius: 22px; padding: 10px 18px; font-size: 14px; resize: none; outline: none; background: #F8F4EC; color: #2C3E50; font-family: inherit; line-height:1.5; max-height: 100px; transition: border-color 0.2s, background 0.2s; }
.tutu-input-bar textarea:focus { border-color: #D4A24C; background: #fff; box-shadow: 0 0 0 3px rgba(212,162,76,0.1); }
.send-btn { width: 42px; height: 42px; border-radius: 50%; border: none; background: linear-gradient(135deg, #2C3E50, #3A6B9F); color: #D4A24C; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s; flex-shrink: 0; }
.send-btn:hover:not(:disabled) { transform: scale(1.08); box-shadow: 0 4px 14px rgba(58,107,159,0.35); }
.send-btn:disabled { opacity: 0.35; }

/* 滚动条 */
.tutu-sidebar::-webkit-scrollbar, .tutu-messages::-webkit-scrollbar, .welcome-area::-webkit-scrollbar, .history-list::-webkit-scrollbar { width: 5px; }
.tutu-sidebar::-webkit-scrollbar-track, .tutu-messages::-webkit-scrollbar-track, .welcome-area::-webkit-scrollbar-track, .history-list::-webkit-scrollbar-track { background: transparent; }
.tutu-sidebar::-webkit-scrollbar-thumb, .tutu-messages::-webkit-scrollbar-thumb, .welcome-area::-webkit-scrollbar-thumb, .history-list::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.12); border-radius: 10px; }
.tutu-sidebar, .tutu-messages, .welcome-area, .history-list { scrollbar-width: thin; scrollbar-color: rgba(0,0,0,0.12) transparent; }

/* 编辑标题弹窗 */
.tutu-mini-overlay { position: fixed; inset: 0; z-index: 11000; background: rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center; }
.tutu-mini-dialog { background: #fff; border-radius: 14px; padding: 20px 24px; width: 320px; box-shadow: 0 12px 40px rgba(0,0,0,0.2); }
.tutu-mini-dialog p { margin: 0 0 10px; font-size: 14px; font-weight: 600; color: #2C3E50; }
.tutu-mini-dialog input { width: 100%; padding: 8px 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; outline: none; }
.tutu-mini-dialog input:focus { border-color: #D4A24C; }
.mini-btns { display: flex; gap: 8px; justify-content: flex-end; margin-top: 12px; }
.mini-btns button { padding: 6px 18px; border-radius: 8px; font-size: 13px; cursor: pointer; border: 1px solid #ddd; background: #fff; }
.mini-btns .btn-ok { background: #D4A24C; color: #fff; border-color: #D4A24C; }

.tutu-mobile-tabs { display: none; }
@media (max-width: 700px) {
  .tutu-dialog { flex-direction: column; height: 94vh; width: 100%; max-width: 100%; border-radius: 0; }
  .tutu-sidebar { display: none; }
  .preset-cards { grid-template-columns: 1fr; }
  .tutu-mobile-tabs { display: flex; gap: 6px; padding: 8px 12px; border-top: 1px solid #e8dfce; background: #F8F3E8; overflow-x: auto; flex-shrink: 0; }
  .tutu-mobile-tabs button { padding: 6px 12px; border: 1px solid #D4A24C; background: #fff; border-radius: 14px; font-size: 12px; color: #D4A24C; cursor: pointer; white-space: nowrap; flex-shrink: 0; }
  .cat-trigger { width: 140px; height: 140px; }
  .cat-tooltip { font-size: 10px; padding: 4px 10px; }
}
</style>
