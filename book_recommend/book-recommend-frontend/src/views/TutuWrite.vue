<template>
  <div class="tw-page">
    <div class="tw-layout">
      <!-- 左侧：会话列表 -->
      <aside class="tw-sidebar">
        <div class="tw-sidebar-header">
          <img src="/AI_interface/head.png" alt="图图" class="tw-sidebar-avatar" />
          <h3 class="tw-sidebar-title">图图写作</h3>
        </div>
        <button class="tw-new-btn" @click="newSession">+ 新建创作</button>
        <div class="tw-mode-row">
          <span class="tw-mode-tag" :class="{active:activeTab==='free'}" @click="switchTab('free')">自由创作</span>
          <span class="tw-mode-tag" :class="{active:activeTab==='bound'}" @click="switchTab('bound')">选书创作</span>
          <span class="tw-mode-tag" :class="{active:activeTab==='draft'}" @click="switchTab('draft')">草稿箱</span>
        </div>
        <div v-if="activeTab==='bound'" class="tw-book-pick">
          <button class="tw-pick-btn" @click="showBookPick=!showBookPick">
            {{ boundBooks.length ? '已选 '+boundBooks.length+' 本书' : '选择书籍...' }}
          </button>
          <div v-if="showBookPick" class="tw-pick-drop">
            <div class="tw-pick-tabs">
              <span :class="{active:bookPickTab==='search'}" @click="bookPickTab='search'">搜索</span>
              <span :class="{active:bookPickTab==='shelf'}" @click="loadShelfBooks()">我的书架</span>
            </div>
            <template v-if="bookPickTab==='search'">
              <el-input v-model="bookSearch" placeholder="搜索书名..." size="small" clearable class="tw-pick-search" />
              <div class="tw-pick-list">
                <el-checkbox-group v-model="boundBooks">
                  <el-checkbox v-for="b in filteredAllBooks" :key="b.id" :label="b.id" :value="b.id">{{ b.title }}</el-checkbox>
                </el-checkbox-group>
              </div>
            </template>
            <template v-else>
              <div class="tw-pick-list">
                <div v-for="g in shelfBookGroups" :key="g.name" class="tw-shelf-group">
                  <div class="tw-shelf-group-name">{{ g.name }}</div>
                  <el-checkbox-group v-model="boundBooks">
                    <el-checkbox v-for="b in g.books" :key="b.id" :label="b.id" :value="b.id">{{ b.title }}</el-checkbox>
                  </el-checkbox-group>
                </div>
                <div v-if="!shelfBookGroups.length" class="tw-empty-hint">暂无书籍</div>
              </div>
            </template>
            <el-button size="small" type="primary" @click="showBookPick=false">确定</el-button>
          </div>
        </div>
        <div v-if="activeTab!=='draft'" class="tw-session-list">
          <div v-for="s in sessions" :key="s.id" class="tw-session-item" :class="{active:s.id===sessionId, pinned:s.pinned}"
               @click="loadSession(s.id)">
            <span class="tw-session-title">{{ s.title || '未命名' }}</span>
            <span class="tw-session-actions" @click.stop>
              <button class="tw-session-btn" @click="togglePin(s)" :title="s.pinned?'取消置顶':'置顶'">📌</button>
              <button class="tw-session-btn" @click="renameSession(s)">✏️</button>
              <button class="tw-session-btn tw-session-del" @click="deleteSession(s)">🗑</button>
            </span>
          </div>
        </div>
        <div v-else class="tw-session-list">
          <div v-for="d in drafts" :key="d.id" class="tw-session-item" :class="{active:d.id===currentDraftId}"
               @click="openDraft(d)">
            <span class="tw-session-title">{{ d.title || '未命名草稿' }}</span>
          </div>
          <div v-if="!drafts.length" class="tw-empty-hint">暂无草稿</div>
        </div>
      </aside>

      <!-- 右侧：对话区 / 草稿编辑器 -->
      <div class="tw-main">
        <template v-if="activeTab!=='draft'">
          <div v-if="messages.length===0" class="tw-presets">
            <div class="tw-preset-label">{{ activeTab==='bound' ? '书籍专属预设' : '通用预设' }}</div>
            <div class="tw-preset-tags">
              <span v-for="p in currentPresets" :key="p" class="tw-preset-tag" @click="quickSend(p)">{{ p }}</span>
            </div>
          </div>

          <div class="tw-messages" ref="msgRef">
            <div v-for="(msg,i) in messages" :key="i" class="tw-msg-row" :class="msg.role">
              <img v-if="msg.role==='assistant'" src="/AI_interface/head.png" class="tw-msg-avatar" />
              <div class="tw-msg-bubble" :class="msg.role">
                <div class="tw-msg-content">{{ msg.content }}</div>
                <div v-if="msg.role==='assistant'" class="tw-msg-actions">
                  <button @click="rewriteMsg('polish')">润色</button>
                  <button @click="rewriteMsg('expand')">扩写</button>
                  <button @click="rewriteMsg('condense')">精简</button>
                  <button class="tw-save-inline" @click="openSaveDialog">保存</button>
                  <button class="tw-save-inline tw-save-draft-btn" @click="saveToDraft(msg)">保存到草稿箱</button>
                </div>
              </div>
              <el-avatar v-if="msg.role==='user'" :size="32" :src="userAvatar" class="tw-msg-avatar" />
            </div>
            <div v-if="loading" class="tw-msg-row assistant">
              <img src="/AI_interface/head.png" class="tw-msg-avatar" />
              <div class="tw-msg-bubble assistant tw-loading-bubble">
                <span class="tw-typing">正在写作</span>
                <span class="tw-dot-anim"><i>.</i><i>.</i><i>.</i></span>
              </div>
            </div>
          </div>

          <div class="tw-input-bar">
            <textarea v-model="input" placeholder="描述你想创作的内容..." @keydown.enter.exact="send" ref="inputRef" :disabled="loading" />
            <button class="tw-send-btn" @click="send" :disabled="!input.trim() || loading">发送</button>
          </div>
        </template>

        <!-- 草稿编辑器 -->
        <template v-else>
          <div v-if="!editingDraft" class="tw-presets">
            <div class="tw-preset-label">选择左侧草稿开始编辑</div>
          </div>
          <div v-else class="tw-draft-editor">
            <div class="tw-draft-editor-header">
              <div class="tw-draft-title-row">
                <el-input v-model="editingDraft.title" placeholder="草稿标题" maxlength="50" size="default" @input="onDraftChanged" class="tw-draft-title-input" />
                <span class="tw-draft-save-status" :class="{saved:draftSaved}">{{ draftSaved ? '已保存' : '未保存' }}</span>
              </div>
            </div>
            <div class="tw-draft-editor-body">
              <textarea v-model="editingDraft.content" placeholder="开始写作..." @input="onDraftChanged" class="tw-draft-content-area" />
            </div>
            <div class="tw-draft-editor-footer">
              <el-button @click="saveDraft" :disabled="draftSaved">保存草稿</el-button>
              <el-button type="primary" @click="openDraftSaveToShelf" :disabled="!canUpdateShelf"
                :title="editingDraft.bookId && !shelfDirty ? '内容未修改，无需更新' : ''">
                {{ editingDraft.bookId ? '更新至书架' : '保存到书架' }}
              </el-button>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- 保存作品弹窗 -->
    <Teleport to="body">
      <div v-if="saveDialog.visible" class="tw-modal-overlay" @click.self="saveDialog.visible=false">
        <div class="tw-modal tw-modal-wide"><h4>保存作品</h4>
          <el-form label-width="60px" size="small">
            <el-form-item label="书名"><el-input v-model="saveDialog.title" placeholder="输入作品名称" maxlength="50" /></el-form-item>
            <el-form-item label="封面">
              <div class="tw-cover-row">
                <img v-if="saveDialog.coverUrl" :src="saveDialog.coverUrl" class="tw-cover-preview" />
                <div v-else class="tw-cover-empty" @click="triggerCoverUpload">点击上传</div>
                <input ref="coverInput" type="file" accept="image/*" style="display:none" @change="handleCoverUpload" />
              </div>
            </el-form-item>
            <el-form-item label="书架">
              <el-select v-model="saveDialog.shelfName" placeholder="选择书架" style="width:100%" filterable allow-create popper-append-to-body popper-class="tw-save-dlg-popper">
                <el-option v-for="s in saveDialog.shelves" :key="s" :label="s" :value="s" />
              </el-select>
            </el-form-item>
          </el-form>
          <div class="tw-modal-btns">
            <el-button @click="saveDialog.visible=false">取消</el-button>
            <el-button type="primary" @click="confirmSave" :disabled="!saveDialog.title.trim()">保存</el-button>
          </div>
        </div>
      </div>
    </Teleport>
    <!-- 重命名弹窗 -->
    <Teleport to="body">
      <div v-if="renameDialog.visible" class="tw-modal-overlay" @click.self="renameDialog.visible=false">
        <div class="tw-modal"><h4>修改标题</h4>
          <el-input v-model="renameDialog.title" maxlength="30" @keyup.enter="confirmRename" />
          <div class="tw-modal-btns">
            <el-button @click="renameDialog.visible=false">取消</el-button>
            <el-button type="primary" @click="confirmRename">确定</el-button>
          </div>
        </div>
      </div>
    </Teleport>
    <!-- 保存到草稿箱弹窗 -->
    <Teleport to="body">
      <div v-if="saveToDraftDialog.visible" class="tw-modal-overlay" @click.self="saveToDraftDialog.visible=false">
        <div class="tw-modal"><h4>保存到草稿箱</h4>
          <el-radio-group v-model="saveToDraftDialog.targetDraftId" style="display:flex;flex-direction:column;gap:6px;">
            <el-radio value="new">新建草稿</el-radio>
            <el-radio v-for="d in drafts" :key="d.id" :value="d.id">{{ d.title || '未命名草稿' }}</el-radio>
          </el-radio-group>
          <div class="tw-modal-btns">
            <el-button @click="saveToDraftDialog.visible=false">取消</el-button>
            <el-button type="primary" @click="confirmSaveToDraft">确定</el-button>
          </div>
        </div>
      </div>
    </Teleport>
    <!-- 登录提示弹窗 -->
    <Teleport to="body">
      <div v-if="showLoginDialog" class="tw-modal-overlay" @click.self="showLoginDialog=false">
        <div class="tw-modal"><h4>请先登录</h4>
          <p style="color:#888;font-size:14px;">登录后即可使用写作功能</p>
          <div class="tw-modal-btns">
            <el-button @click="showLoginDialog=false">取消</el-button>
            <el-button type="primary" @click="showLoginDialog=false;router.push('/login')">去登录</el-button>
          </div>
        </div>
      </div>
    </Teleport>
    <!-- 未保存退出确认弹窗 -->
    <Teleport to="body">
      <div v-if="unsavedExitDialog.visible" class="tw-modal-overlay" @click.self="unsavedExitDialog.visible=false">
        <div class="tw-modal"><h4>未保存的更改</h4>
          <p style="color:#888;font-size:14px;">当前草稿有未保存的更改，确定要离开吗？</p>
          <div class="tw-modal-btns">
            <el-button @click="unsavedExitDialog.visible=false">取消</el-button>
            <el-button type="primary" @click="confirmUnsavedExit">确定离开</el-button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '../stores/user'
import { getAvatarUrl } from '../utils/avatar'
import request from '../api/request'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const activeTab = ref('free')
const sessionId = ref(null)
const input = ref('')
const loading = ref(false)
const messages = ref([])
const sessions = ref([])
const msgRef = ref(null)
const inputRef = ref(null)

const userAvatar = computed(() => getAvatarUrl(userStore.userInfo?.avatar, userStore.username))

const showBookPick = ref(false)
const boundBooks = ref([])
const bookSearch = ref('')
const allBooks = ref([])
const bookPickTab = ref('search')
const shelfBookGroups = ref([])

const renameDialog = ref({ visible: false, sessionId: null, title: '' })
const saveDialog = ref({ visible: false, title: '', shelfName: '我的创作', shelves: [], coverUrl: '', fromDraft: false })
const coverInput = ref(null)

// 草稿箱
const editingDraft = ref(null)
const currentDraftId = ref(null)
const draftSaved = ref(true)
const shelfDirty = ref(false)
const drafts = ref([])
const unsavedExitDialog = ref({ visible: false, targetMode: '' })

const canUpdateShelf = computed(() => {
  if (!editingDraft.value) return false
  if (!editingDraft.value.bookId) return true
  return shelfDirty.value
})

// 保存到草稿箱弹窗
const saveToDraftDialog = ref({ visible: false, targetDraftId: 'new' })
const saveToDraftData = ref(null)

// 登录保护
const showLoginDialog = ref(false)

function requireLogin() {
  if (!userStore.isLoggedIn) {
    showLoginDialog.value = true
    return false
  }
  return true
}

function onDraftChanged() {
  draftSaved.value = false
  shelfDirty.value = true
}

function openSaveDialog() {
  saveDialog.value.title = sessions.value.find(s => s.id === sessionId.value)?.title || ''
  saveDialog.value.shelfName = '我的创作'
  saveDialog.value.shelves = ['我的创作']
  saveDialog.value.coverUrl = ''
  // 仅加载创作书架（type=writing），不可选主页书架
  request.get('/shelves', { params: { type: 'writing' } }).then(r => {
    if (r.code === 200) {
      const names = (r.data.shelves || []).map(s => s.name)
      saveDialog.value.shelves = names.length ? names : ['我的创作']
    }
  }).catch(() => {})
  saveDialog.value.visible = true
}

function triggerCoverUpload() { coverInput.value?.click() }

async function handleCoverUpload(e) {
  const file = e.target.files?.[0]
  if (!file) return
  const fd = new FormData(); fd.append('file', file)
  try {
    const res = await request.post('/tutuWrite/upload-cover', fd)
    if (res.code === 200) saveDialog.value.coverUrl = res.data.cover_url
  } catch { ElMessage.error('封面上传失败') }
}

async function confirmSave() {
  try {
    const isDraft = saveDialog.value.fromDraft
    let content, payload

    if (isDraft) {
      // 从草稿箱保存
      content = editingDraft.value.content
      payload = {
        title: saveDialog.value.title.trim(),
        content: content,
        cover_url: saveDialog.value.coverUrl,
        shelf_name: saveDialog.value.shelfName,
        tag_ids: [],
        draft_id: currentDraftId.value
      }
      if (editingDraft.value.bookId) {
        payload.book_id = editingDraft.value.bookId
      }
    } else {
      // 从 AI 对话保存
      content = messages.value.map(m => {
        const role = m.role === 'user' ? '用户' : '图图'
        return `【${role}】${m.content}`
      }).join('\n\n')
      payload = {
        title: saveDialog.value.title.trim(),
        content: content,
        cover_url: saveDialog.value.coverUrl,
        shelf_name: saveDialog.value.shelfName,
        tag_ids: []
      }
    }

    const res = await request.post('/tutuWrite/save-to-shelf', payload)
    if (res.code === 200) {
      try {
        const uid = userStore.userInfo?.id || '0'
        const bid = res.data.book_id
        localStorage.removeItem(`rd_rc_v5_${uid}_${bid}`)
        for (let i = localStorage.length - 1; i >= 0; i--) {
          const key = localStorage.key(i)
          if (key && key.startsWith(`rd_pg5_${uid}_${bid}_`)) {
            localStorage.removeItem(key)
          }
        }
      } catch {}
      if (isDraft) {
        shelfDirty.value = false
        if (res.data.book_id) {
          editingDraft.value.bookId = res.data.book_id
        }
      }
      ElMessage({ message: `《${saveDialog.value.title}》已保存到「${saveDialog.value.shelfName}」`, type: 'success', duration: 1500 })
      saveDialog.value.visible = false
      saveDialog.value.fromDraft = false
    }
  } catch { ElMessage.error('保存失败') }
}

const filteredAllBooks = computed(() => {
  if (!bookSearch.value) return allBooks.value
  return allBooks.value.filter(b => b.title.includes(bookSearch.value))
})

const freePresets = ['写一篇短篇小说','写一篇散文','写一篇读后感','写一篇随笔','写一篇议论文','写一篇应试作文']
const boundPresets = ['写番外','续写结局','改写XX情节','写人物小传','写书评赏析','提取人物关系','分析世界观']
const currentPresets = computed(() => activeTab.value==='bound' ? boundPresets : freePresets)

function switchTab(m) {
  // 如果从草稿箱切出且有未保存更改
  if (activeTab.value === 'draft' && m !== 'draft' && !draftSaved.value) {
    unsavedExitDialog.value = { visible: true, targetMode: m }
    return
  }
  activeTab.value = m
  if (m === 'draft') {
    loadDrafts()
    editingDraft.value = null
    currentDraftId.value = null
    draftSaved.value = true
    shelfDirty.value = false
  } else {
    boundBooks.value = []
    newSession()
  }
}

function confirmUnsavedExit() {
  unsavedExitDialog.value.visible = false
  draftSaved.value = true
  shelfDirty.value = false
  const m = unsavedExitDialog.value.targetMode
  activeTab.value = m
  if (m !== 'draft') {
    boundBooks.value = []
    newSession()
  }
}

function newSession() { sessionId.value = null; messages.value = []; input.value = '' }

async function loadSession(id) {
  sessionId.value = id
  try {
    const res = await request.get('/tutuWrite/sessions/' + id + '/messages')
    if (res.code === 200) messages.value = res.data.messages
  } catch { messages.value = [] }
}

function quickSend(msg) { input.value = msg; send() }

async function send() {
  if (!requireLogin()) return
  const msg = input.value.trim()
  if (!msg) return
  input.value = ''
  messages.value.push({ role: 'user', content: msg })
  loading.value = true
  nextTick(() => { if (msgRef.value) msgRef.value.scrollTop = msgRef.value.scrollHeight })
  try {
    const res = await request.post('/tutuWrite/send', {
      session_id: sessionId.value, message: msg, mode: activeTab.value, book_ids: boundBooks.value
    })
    if (res.code === 200) {
      sessionId.value = res.data.session_id
      messages.value.push({ role: 'assistant', content: res.data.reply })
      // 自动生成标题：取第一条用户消息前20字
      if (messages.value.filter(m => m.role === 'user').length === 1) {
        const autoTitle = msg.slice(0, 20).replace(/\n/g, ' ')
        request.put('/tutuWrite/sessions/' + sessionId.value, { title: autoTitle }).then(() => {
          const s = sessions.value.find(x => x.id === sessionId.value)
          if (s) s.title = autoTitle
        }).catch(() => {})
      }
    }
  } catch { messages.value.push({ role: 'assistant', content: '网络请求失败' }) }
  loading.value = false
  nextTick(() => { if (msgRef.value) msgRef.value.scrollTop = msgRef.value.scrollHeight })
  loadSessions()
}

function rewriteMsg(action) {
  input.value = {polish:'请润色上文，优化措辞',expand:'请扩写上文，增加细节',condense:'请精简上文，压缩冗余'}[action]
  send()
}

async function loadSessions() {
  try {
    const res = await request.get('/tutuWrite/sessions')
    if (res.code === 200) {
      sessions.value = (res.data.sessions || []).map(s => ({ ...s, pinned: false }))
    }
  } catch {}
}

function togglePin(s) { s.pinned = !s.pinned }
function renameSession(s) {
  renameDialog.value = { visible: true, sessionId: s.id, title: s.title || '' }
}
async function confirmRename() {
  const t = renameDialog.value.title.trim()
  if (!t) return
  try { await request.put('/tutuWrite/sessions/' + renameDialog.value.sessionId, { title: t }) } catch {}
  renameDialog.value.visible = false
  loadSessions()
}
async function deleteSession(s) {
  try {
    await ElMessageBox.confirm('确定删除该创作会话？', '删除', { type: 'warning' })
    await request.delete('/tutuWrite/sessions/' + s.id)
    if (sessionId.value === s.id) newSession()
    loadSessions()
  } catch {}
}

// ─── 草稿箱 ───
async function loadDrafts() {
  try {
    const res = await request.get('/tutuWrite/draft-box')
    if (res.code === 200) drafts.value = res.data.drafts || []
  } catch {}
}

async function openDraft(d) {
  try {
    const res = await request.get('/tutuWrite/draft-box/' + d.id)
    if (res.code === 200) {
      editingDraft.value = { ...res.data, id: d.id }
      currentDraftId.value = d.id
      draftSaved.value = true
      shelfDirty.value = false
    }
  } catch {}
}

async function saveDraft() {
  if (!requireLogin()) return
  if (!editingDraft.value) return
  try {
    await request.put('/tutuWrite/draft-box/' + currentDraftId.value, {
      title: editingDraft.value.title,
      content: editingDraft.value.content
    })
    draftSaved.value = true
    // shelfDirty is NOT reset here — only reset on save-to-shelf
    ElMessage({ message: '草稿已保存', type: 'success', duration: 1200 })
    loadDrafts()
  } catch { ElMessage.error('保存草稿失败') }
}

async function saveToDraft(msg) {
  if (!requireLogin()) return
  saveToDraftData.value = msg
  saveToDraftDialog.value.targetDraftId = 'new'
  await loadDrafts()
  saveToDraftDialog.value.visible = true
}

async function confirmSaveToDraft() {
  const content = saveToDraftData.value?.content || saveToDraftData.value
  const targetDraftId = saveToDraftDialog.value.targetDraftId
  try {
    if (targetDraftId === 'new' || !targetDraftId) {
      await request.post('/tutuWrite/draft-box', { title: (typeof content === 'string' ? content : '').slice(0, 20), content })
    } else {
      const res = await request.get('/tutuWrite/draft-box/' + targetDraftId)
      const existing = (res.data.content || '')
      await request.put('/tutuWrite/draft-box/' + targetDraftId, { content: existing + '\n\n---\n\n' + content })
    }
    ElMessage({ message: '已保存到草稿箱', type: 'success', duration: 1200 })
    saveToDraftDialog.value.visible = false
  } catch { ElMessage.error('保存到草稿箱失败') }
}

async function openDraftSaveToShelf() {
  if (!requireLogin()) return
  if (!editingDraft.value) return
  // 打开书架选择弹窗（仅创作书架）
  saveDialog.value.title = editingDraft.value.title
  saveDialog.value.shelfName = '我的创作'
  saveDialog.value.shelves = ['我的创作']
  saveDialog.value.coverUrl = ''
  saveDialog.value.fromDraft = true
  request.get('/shelves', { params: { type: 'writing' } }).then(r => {
    if (r.code === 200) {
      const names = (r.data.shelves || []).map(s => s.name)
      saveDialog.value.shelves = names.length ? names : ['我的创作']
    }
  }).catch(() => {})
  saveDialog.value.visible = true
}

// ─── 书架书籍加载 ───
async function loadShelfBooks() {
  bookPickTab.value = 'shelf'
  try {
    const res = await request.get('/shelves')
    const groups = []
    ;(res.data.shelves || []).forEach(shelf => {
      if (shelf.items && shelf.items.length) {
        groups.push({ name: shelf.name, books: shelf.items.map(it => ({ id: it.book.id, title: it.book.title })) })
      }
    })
    shelfBookGroups.value = groups
  } catch {}
}

onMounted(async () => {
  await loadSessions()
  try {
    const r = await request.get('/books/search', { params: { size: 250 } })
    if (r.code === 200) allBooks.value = (r.data.items || []).map(b => ({ id: b.id, title: b.title }))
  } catch {}
  if (route.query.book_id) { activeTab.value = 'bound'; boundBooks.value = [Number(route.query.book_id)] }
})
</script>

<style scoped>
.tw-page { max-width: 1100px; margin: 0 auto; padding: 0; height: calc(100vh - 120px); }
.tw-layout { display: flex; height: 100%; gap: 0; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 12px rgba(0,0,0,0.08); }

/* ── 侧栏 ── */
.tw-sidebar { width: 250px; flex-shrink: 0; background: #F8F3E8; padding: 20px 14px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
.tw-sidebar-header { display: flex; flex-direction: column; align-items: center; gap: 6px; margin-bottom: 4px; }
.tw-sidebar-avatar { width: 56px; height: 56px; border-radius: 50%; border: 2.5px solid #D4A24C; object-fit: cover; }
.tw-sidebar-title { font-size: 16px; font-weight: 700; color: #2C3E50; margin: 0; }
.tw-new-btn { width: 100%; padding: 9px; border: 1.5px dashed #D4A24C; border-radius: 8px; background: transparent; color: #D4A24C; cursor: pointer; font-size: 14px; font-weight: 600; }
.tw-new-btn:hover { background: #D4A24C; color: #fff; border-style: solid; }
.tw-mode-row { display: flex; gap: 0; }
.tw-mode-tag { flex: 1; text-align: center; padding: 6px; font-size: 13px; cursor: pointer; border: 1px solid #ddd; background: #fafafa; color: #888; }
.tw-mode-tag:first-child { border-radius: 6px 0 0 6px; }
.tw-mode-tag:last-child { border-radius: 0 6px 6px 0; }
.tw-mode-tag.active { background: #D4A24C; border-color: #D4A24C; color: #fff; }

.tw-book-pick { position: relative; }
.tw-pick-btn { width: 100%; padding: 7px; border: 1px solid #ddd; border-radius: 6px; background: #fff; cursor: pointer; font-size: 13px; }
.tw-pick-drop { position: absolute; top: 100%; left: 0; right: 0; z-index: 100; background: #fff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 8px; max-height: 320px; overflow-y: auto; box-shadow: 0 4px 16px rgba(0,0,0,0.12); }
.tw-pick-search { margin-bottom: 6px; }
.tw-pick-list { max-height: 200px; overflow-y: auto; font-size: 13px; }

.tw-session-list { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 2px; }
.tw-session-item { display: flex; align-items: center; justify-content: space-between; padding: 7px 8px; cursor: pointer; border-radius: 6px; font-size: 13px; color: #555; }
.tw-session-item:hover { background: #fff; }
.tw-session-item.active { background: #FFF8E1; color: #D4A24C; }
.tw-session-item.pinned { order: -1; background: #FFF8E1; }
.tw-session-title { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tw-session-actions { display: none; gap: 2px; flex-shrink: 0; }
.tw-session-item:hover .tw-session-actions { display: flex; }
.tw-session-btn { background: none; border: none; cursor: pointer; font-size: 12px; padding: 1px 3px; border-radius: 3px; }
.tw-session-btn:hover { background: #eee; }
.tw-session-del:hover { color: #e74c3c; }

/* ── 主区 ── */
.tw-main { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.tw-presets { padding: 16px 20px; border-bottom: 1px solid #eee; }
.tw-preset-label { font-size: 14px; color: #888; margin-bottom: 8px; }
.tw-preset-tags { display: flex; flex-wrap: wrap; gap: 8px; }
.tw-preset-tag { padding: 5px 14px; border-radius: 14px; font-size: 13px; cursor: pointer; background: #FFF8E7; color: #D4A24C; border: 1px solid #f5d5a0; transition: all 0.2s; }
.tw-preset-tag:hover { background: #D4A24C; color: #fff; }

/* ── 消息 ── */
.tw-messages { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 16px; }
.tw-msg-row { display: flex; gap: 10px; align-items: flex-start; }
.tw-msg-row.user { justify-content: flex-end; }
.tw-msg-avatar { width: 30px; height: 30px; border-radius: 50%; flex-shrink: 0; object-fit: cover; }
.tw-msg-bubble { max-width: 78%; padding: 12px 16px; border-radius: 14px; }
.tw-msg-bubble.user { background: #D4A24C; color: #fff; }
.tw-msg-bubble.assistant { background: #f0ede8; color: #333; }
.tw-msg-content {
  font-family: 'KaiTi', '楷体', 'Noto Serif SC', serif;
  font-size: 15px; line-height: 1.6; white-space: pre-wrap;
  margin: 0;
}
.tw-msg-bubble.user .tw-msg-content { font-family: inherit; font-size: 14px; }

.tw-typing { color: #D4A24C; font-size: 15px; font-weight: 600; }
.tw-loading-bubble { min-width: 120px; }
.tw-dot-anim { display: inline; }
.tw-dot-anim i { font-style: normal; font-weight: bold; color: #D4A24C; animation: tw-dot-bounce 1.4s infinite both; }
.tw-dot-anim i:nth-child(1) { animation-delay: 0s; }
.tw-dot-anim i:nth-child(2) { animation-delay: 0.2s; }
.tw-dot-anim i:nth-child(3) { animation-delay: 0.4s; }
@keyframes tw-dot-bounce { 0%,80%,100% { opacity: 0; transform: translateY(0); } 40% { opacity: 1; transform: translateY(-4px); } }

.tw-msg-actions { display: flex; gap: 6px; margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(0,0,0,0.06); }
.tw-msg-actions button { padding: 3px 12px; border: 1px solid #ddd; border-radius: 10px; background: #fff; font-size: 12px; cursor: pointer; color: #888; transition: all 0.2s; }
.tw-msg-actions button:hover { border-color: #D4A24C; color: #D4A24C; }
.tw-save-inline { background: #D4A24C !important; color: #fff !important; border-color: #D4A24C !important; font-weight: 600; }
.tw-save-inline:hover { background: #c8933a !important; color: #fff !important; }

/* ── 输入 ── */
.tw-input-bar { display: flex; gap: 8px; padding: 12px 20px; border-top: 1px solid #eee; align-items: flex-end; }
.tw-input-bar textarea { flex: 1; border: 1px solid #e0e0e0; border-radius: 8px; padding: 10px 14px; font-size: 14px; resize: none; outline: none; min-height: 44px; max-height: 120px; font-family: inherit; }
.tw-send-btn { padding: 10px 22px; border: none; border-radius: 8px; background: #D4A24C; color: #fff; cursor: pointer; font-size: 14px; font-weight: 600; flex-shrink: 0; }
.tw-send-btn:disabled { opacity: 0.4; cursor: not-allowed; }

/* ── 弹窗 ── */
.tw-modal-overlay { position: fixed; inset: 0; z-index: 9999; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; }
.tw-modal { background: #fff; border-radius: 12px; padding: 24px; width: 360px; box-shadow: 0 8px 32px rgba(0,0,0,0.2); }
.tw-modal-wide { width: 440px; }
.tw-cover-row { display: flex; align-items: center; gap: 10px; }
.tw-cover-preview { width: 60px; height: 84px; object-fit: cover; border-radius: 6px; border: 1px solid #eee; }
.tw-cover-empty { width: 60px; height: 84px; border: 2px dashed #ddd; border-radius: 6px; display: flex; align-items: center; justify-content: center; cursor: pointer; font-size: 12px; color: #aaa; }
.tw-cover-empty:hover { border-color: #D4A24C; color: #D4A24C; }
.tw-modal h4 { margin: 0 0 14px; font-size: 16px; color: #2C3E50; }
.tw-modal-btns { display: flex; gap: 8px; justify-content: flex-end; margin-top: 14px; }

/* ── 书签选择器标签 ── */
.tw-pick-tabs { display: flex; gap: 0; margin-bottom: 8px; border-bottom: 1px solid #eee; }
.tw-pick-tabs span { flex: 1; text-align: center; padding: 5px; font-size: 13px; cursor: pointer; color: #888; border-bottom: 2px solid transparent; }
.tw-pick-tabs span.active { color: #D4A24C; border-bottom-color: #D4A24C; font-weight: 600; }
.tw-shelf-group { margin-bottom: 8px; }
.tw-shelf-group-name { font-size: 12px; color: #aaa; margin-bottom: 4px; padding-left: 2px; }
.tw-empty-hint { font-size: 13px; color: #bbb; text-align: center; padding: 16px 0; }

/* ── 草稿编辑器 ── */
.tw-draft-editor { flex: 1; display: flex; flex-direction: column; min-height: 0; }
.tw-draft-editor-header { padding: 16px 20px; border-bottom: 1px solid #eee; }
.tw-draft-title-row { display: flex; align-items: center; gap: 12px; }
.tw-draft-title-input { max-width: 360px; }
.tw-draft-save-status { font-size: 13px; color: #e6a23c; white-space: nowrap; }
.tw-draft-save-status.saved { color: #67c23a; }
.tw-draft-editor-body { flex: 1; padding: 16px 20px; display: flex; }
.tw-draft-content-area { flex: 1; border: 1px solid #e0e0e0; border-radius: 8px; padding: 14px; font-size: 15px; font-family: 'KaiTi','楷体','Noto Serif SC',serif; line-height: 1.8; resize: none; outline: none; }
.tw-draft-content-area:focus { border-color: #D4A24C; }
.tw-draft-editor-footer { display: flex; gap: 8px; justify-content: flex-end; padding: 12px 20px; border-top: 1px solid #eee; }

/* ── 保存到草稿箱按钮 ── */
.tw-save-draft-btn { background: #67c23a !important; border-color: #67c23a !important; }
.tw-save-draft-btn:hover { background: #5daf34 !important; }
</style>

<style>
.tw-save-dlg-popper { z-index: 99999 !important; }
</style>
