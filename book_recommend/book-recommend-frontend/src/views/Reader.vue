<template>
  <div class="reader-app" :style="themeStyles">
    <header class="rd-header">
      <button class="rd-btn" @click="goBack">← 返回</button>
      <span class="rd-title">{{ bookTitle }}</span>
      <div class="rd-header-right">
        <span class="rd-page-info">{{ displayPage }} / {{ totalPages || '?' }}</span>
        <button class="rd-btn" @click="showSettings=!showSettings">⚙</button>
        <button class="rd-btn" @click="showBookmarks=!showBookmarks">🔖</button>
        <button class="rd-btn" @click="showAnnotations=!showAnnotations">🖊</button>
        <button class="rd-btn" @click="showToc=!showToc">☰</button>
      </div>
    </header>

    <div class="rd-body">
      <Transition name="slide">
        <aside v-if="showToc" class="rd-toc"><h3>目录</h3><div class="toc-list">
          <div v-for="(ch,idx) in chapters" :key="ch.order" :class="['toc-ch',{active:idx===currentChapter}]" @click="jumpToChapter(idx)"><span class="toc-num">{{ idx+1 }}.</span><span>{{ ch.name }}</span></div>
        </div></aside>
      </Transition>

      <main class="rd-main" ref="mainRef" @click="onClickPage" @wheel.prevent="onWheelPage" @mouseup="onTextSelect" @keydown="onKeyDown">
        <!-- 加载动画 -->
        <div v-if="loading" class="rd-loading">
          <div class="rd-loading-inner">
            <div class="rd-loading-spinner"><svg viewBox="0 0 50 50"><circle cx="25" cy="25" r="20" fill="none" stroke="#D4A24C" stroke-width="3" stroke-dasharray="90,150" class="rd-spinner-circle"/></svg></div>
            <div class="rd-loading-text">正在加载图书内容...</div>
            <div class="rd-loading-bar-wrap"><div class="rd-loading-bar" :style="{width: loadProgress+'%'}"></div></div>
            <div class="rd-loading-pct">{{ loadProgress }}%</div>
            <div class="rd-loading-sub">{{ loadedChapters }}/{{ chapters.length }} 章已加载</div>
          </div>
        </div>
        <div v-else-if="measuring" class="rd-loading">{{ `正在排版... ${measureProgress}%` }}</div>
        <template v-else-if="pages.length">
          <div class="rd-page-box" :style="{height: pageH+'px'}">
            <div v-if="isChapterStart" class="rd-ctitle">{{ currentChapterName }}</div>
            <p v-for="(t,i) in highlightedParas" :key="i" :class="['rd-para', { 'rd-para-cont': i === 0 && isContinuationFirst }]" v-html="t"></p>
          </div>
          <!-- 底部进度条 -->
          <div class="rd-progress-bar-wrap"><div class="rd-progress-bar" :style="{width: calculatedProgress+'%'}"></div><span class="rd-progress-txt">{{ calculatedProgress }}%</span></div>
        </template>
        <div v-else class="rd-empty">该书籍暂无内容</div>
      </main>

      <!-- 设置面板 -->
      <aside v-if="showSettings" class="rd-panel rd-settings-panel"><h3>阅读设置</h3>
        <div class="set-group"><label>字体</label><select v-model="settings.fontFamily" @change="onSettingChange">
          <option value="'PingFang SC','Microsoft YaHei',sans-serif">系统默认</option>
          <option value="'Noto Serif SC','SimSun',serif">宋体</option>
          <option value="'楷体','KaiTi',serif">楷体</option>
          <option value="'Georgia','Times New Roman',serif">英文衬线</option>
        </select></div>
        <div class="set-group"><label>字号 {{settings.fontSize}}px</label><input type="range" v-model.number="settings.fontSize" min="14" max="26" @input="onSettingChange"></div>
        <div class="set-group"><label>字重 {{settings.fontWeight}}</label><input type="range" v-model.number="settings.fontWeight" min="300" max="700" step="100" @input="onSettingChange"></div>
        <div class="set-group"><label>主题</label><div class="theme-grid">
          <button v-for="t in themes" :key="t.name" :class="['theme-btn',{active:settings.theme===t.name}]" :style="{background:t.bg,color:t.color}" @click="settings.theme=t.name;saveSettings()">{{t.label}}</button>
        </div></div>
      </aside>

      <!-- 书签 -->
      <aside v-if="showBookmarks" class="rd-panel rd-bookmarks-panel"><h3>书签</h3>
        <button class="rd-btn-outline sm" @click="addBookmark">+ 当前页</button><div class="panel-scroll">
        <div v-if="!currentBookBookmarks.length" class="rd-empty-sm">暂无书签</div>
        <div v-for="bm in currentBookBookmarks" :key="bm.id" class="bm-item" @click="goToPage(bm.globalPage)"><span class="bm-ch">{{bm.chapterName}}</span><span class="bm-text">{{bm.text||'第'+(bm.globalPage+1)+'页'}}</span><button class="bm-del" @click.stop="deleteBookmark(bm.id)">✕</button></div>
        </div></aside>

      <!-- 批注+高亮侧栏（合并展示） -->
      <aside v-if="showAnnotations" class="rd-panel rd-ann-panel"><h3>批注 & 高亮</h3><div class="panel-scroll">
        <div v-if="!combinedRecords.length" class="rd-empty-sm">选中文字后添加批注或高亮</div>
        <div v-for="rec in combinedRecords" :key="rec.key" class="ann-card">
          <!-- 高亮行 -->
          <div v-if="rec.highlight" class="ann-card-header">
            <span class="hl-swatch" :style="{background:rec.highlight.color}"></span>
            <span class="ann-q">「{{rec.text.slice(0,30)}}{{rec.text.length>30?'…':''}}」</span>
            <span class="ann-pg">第{{rec.highlight.globalPage+1}}页</span>
            <button class="rd-icon-btn" @click.stop="jumpToHL(rec.highlight)" title="跳转">📍</button>
            <button class="rd-icon-btn" @click.stop="deleteHighlight(rec.highlight.id)" title="删除高亮">✕</button>
          </div>
          <!-- 批注行 -->
          <div v-if="rec.annotation" class="ann-card-header" @click="rec.annotation._expanded=!rec.annotation._expanded">
            <span class="ann-icon">💬</span>
            <span class="ann-q">「{{rec.text.slice(0,30)}}{{rec.text.length>30?'…':''}}」</span>
            <span class="ann-pg">第{{rec.annotation.globalPage+1}}页</span>
            <button class="rd-icon-btn" @click.stop="jumpToAnno(rec.annotation)" title="跳转">📍</button>
            <button class="rd-icon-btn" @click.stop="deleteAnnotation(rec.annotation.id)" title="删除批注">✕</button>
          </div>
          <!-- 展开批注内容 -->
          <div v-if="rec.annotation?._expanded" class="ann-card-body">
            <div v-if="rec.annotation._editing" class="ann-edit-area">
              <div class="rtf-toolbar mini">
                <button @mousedown.prevent @click="execCmd('bold')"><b>B</b></button>
                <button @mousedown.prevent @click="execCmd('italic')"><i>I</i></button>
                <button @mousedown.prevent @click="execCmd('underline')"><u>U</u></button>
                <button @mousedown.prevent @click="changeFontSize(-1)" title="缩小字号">A-</button>
                <button @mousedown.prevent @click="changeFontSize(1)" title="增大字号">A+</button>
                <span v-for="cp in COLOR_PRESETS" :key="cp" class="cp-swatch" :style="{background:cp}" @mousedown.prevent @click="execCmd('foreColor',cp)" title="文字颜色"></span>
                <input type="color" @change="execCmd('foreColor',$event.target.value)" value="#333">
              </div>
              <div :ref="el=>setEditRef(el,rec.annotation.id)" class="rtf-editor small" contenteditable @input="rec.annotation.note=$event.target.innerHTML" v-html="rec.annotation._editBackup"></div>
              <div style="margin-top:6px">
                <button class="rd-btn-sm primary" @click="saveAnnotationEdit(rec.annotation)">保存</button>
                <button class="rd-btn-sm" @click="cancelAnnotationEdit(rec.annotation)">取消</button>
              </div>
            </div>
            <div v-else class="ann-note-display" v-html="rec.annotation.note || '(无批注内容)'"></div>
            <div class="ann-card-actions" v-if="!rec.annotation._editing">
              <button class="rd-btn-sm" @click="editAnnotation(rec.annotation)">✏</button>
              <button class="rd-btn-sm" @click="jumpToAnno(rec.annotation)">📍</button>
              <button class="rd-btn-sm danger" @click="deleteAnnotation(rec.annotation.id)">🗑</button>
            </div>
          </div>
        </div>
        </div></aside>
    </div>

    <!-- 返回浮动钮 -->
    <Teleport to="body">
      <div v-if="returnPage!==null" class="rd-return-float" @click="goReturnPage">← 返回 (第{{returnPage+1}}页)</div>
      <div class="rd-write-float" @click="goWrite" title="本书创作">✏️</div>
    </Teleport>

    <!-- 选中/高亮 浮动弹窗 (点击屏幕其他区域消失，不翻页) -->
    <Teleport to="body">
      <div v-if="popup.visible" class="rd-selection-menu" :style="popup.style" @click.stop>
        <!-- 模式1：刚选中文字 -->
        <template v-if="popup.mode==='selection'">
          <div class="sel-hl-row">
            <span class="sel-hl-label">荧光笔</span>
            <button v-for="c in HL_COLORS" :key="c.code" class="sel-hl-btn" :style="{background:c.code}" :title="c.name" @click="addHighlight(c.code)"></button>
            <button class="sel-hl-btn hl-cancel" title="取消高亮" @click="removeHighlightForSelection"></button>
          </div>
          <button class="sel-anno-btn" @click="openAnnotationEditor">💬 添加批注</button>
        </template>
        <!-- 模式2：点击已有高亮 -->
        <template v-if="popup.mode==='highlight'">
          <div class="sel-hl-row">
            <span class="sel-hl-label">改色</span>
            <button v-for="c in HL_COLORS" :key="c.code" class="sel-hl-btn" :style="{background:c.code}" :title="c.name" @click="changeHighlightColor(c.code)"></button>
            <button class="sel-hl-btn hl-cancel" title="取消高亮" @click="removeClickedHighlight"></button>
          </div>
          <button class="sel-anno-btn" @click="openAnnotationEditorForHL">💬 添加批注</button>
        </template>
      </div>
    </Teleport>

    <!-- 批注编辑器弹窗 -->
    <Teleport to="body">
      <div v-if="annoEditor.visible" class="rd-modal-overlay" @click.self="closeAnnotationEditor">
        <div class="rd-modal rd-anno-modal">
          <h3>添加批注</h3>
          <p class="anno-quote-ref">「{{annoEditor.quote.slice(0,100)}}{{annoEditor.quote.length>100?'…':''}}」</p>
          <div class="rtf-toolbar">
            <button @mousedown.prevent @click="execCmd('bold')"><b>B</b></button>
            <button @mousedown.prevent @click="execCmd('italic')"><i>I</i></button>
            <button @mousedown.prevent @click="execCmd('underline')"><u>U</u></button>
            <span class="tb-sep">|</span>
            <button @mousedown.prevent @click="changeFontSize(-1)" title="缩小字号">A-</button>
            <button @mousedown.prevent @click="changeFontSize(1)" title="增大字号">A+</button>
            <span class="tb-sep">|</span>
            <span v-for="cp in COLOR_PRESETS" :key="cp" class="cp-swatch" :style="{background:cp}" @mousedown.prevent @click="execCmd('foreColor',cp)" title="文字颜色"></span>
            <input type="color" @change="execCmd('foreColor',$event.target.value)" value="#333">
          </div>
          <div ref="annoEditorRef" class="rtf-editor" contenteditable @keydown.enter=""></div>
          <div class="rd-modal-btns">
            <button class="rd-btn-primary" @click="saveAnnotation">保存批注</button>
            <button class="rd-btn-outline" @click="closeAnnotationEditor">取消</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 登录弹窗 -->
    <Teleport to="body"><div v-if="showLoginModal" class="rd-modal-overlay"><div class="rd-modal"><h3>当前为试读阶段</h3><p>登录后可阅读全文</p>
      <div class="rd-modal-btns"><button class="rd-btn-primary" @click="goLogin">登录</button><button class="rd-btn-outline" @click="goRegister">注册</button></div>
      <button class="rd-modal-close" @click="showLoginModal=false">✕</button></div></div></Teleport>
  </div>
</template>

<script setup>
import { ref, computed, reactive, watch, onMounted, onBeforeUnmount, nextTick, shallowRef } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { useBookStore } from '../stores/book'
import request from '../api/request'
import { shelvesAPI } from '../api/shelves'
const route = useRoute(); const router = useRouter(); const userStore = useUserStore(); const bookStore = useBookStore()

// ── 基础 ──
const bookId = ref(0); const bookTitle = ref(''); const chapters = ref([]); const isUserCreated = ref(false)
const loading = ref(false); const measuring = ref(false); const measureProgress = ref(0)
const loadProgress = ref(0); const loadedChapters = ref(0); const totalCharsAllBook = ref(0)
const readingSeconds = ref(0); let readingTimer = null; let saveTimer = null
const SAVE_INTERVAL = 30

// 字体感知进度：基于字符数，不受字号调整影响
const calculatedProgress = computed(() => {
  if (!totalCharsAllBook.value || !pages.value.length) return 0
  let charsRead = 0
  for (let i = 0; i < globalPage.value && i < pages.value.length; i++) {
    charsRead += (pages.value[i]?.texts || []).join('').length
  }
  charsRead += (currentPageTexts.value || []).join('').length
  return Math.min(100, Math.round(charsRead / totalCharsAllBook.value * 100))
})
const showToc = ref(false); const showSettings = ref(false); const showAnnotations = ref(false)
const showBookmarks = ref(false); const globalPage = ref(0)
const pages = shallowRef([]); const currentPageTexts = ref([])
const currentChapter = ref(0); const currentChapterName = ref('')
const mainRef = ref(null); const pageH = ref(600)
const totalPages = computed(() => pages.value.length)
const displayPage = computed(() => totalPages.value > 0 ? globalPage.value + 1 : 0)
const isLoggedIn = computed(() => !!userStore.isLoggedIn)
const uid = computed(() => userStore.userInfo?.id || 0)  // 用户隔离：0=未登录
const isChapterStart = computed(() => pages.value.length ? pages.value[globalPage.value]?.isFirst : false)
const isContinuationFirst = computed(() => pages.value.length ? pages.value[globalPage.value]?.continuationFirst : false)
const showLoginModal = ref(false); const TRIAL_PAGES = 10; const rawChapters = ref({})
const reachedEnd = ref(false); const returnPage = ref(null)

// ── 设置 ──
const themes = [
  { name: 'warm', label: '护眼黄', bg: '#F5F0DF', color: '#3d3226' },
  { name: 'green', label: '淡绿', bg: '#E8F0E3', color: '#2d3a28' },
  { name: 'dark', label: '夜间', bg: '#1e2429', color: '#c8ccd0' },
  { name: 'white', label: '纯白', bg: '#fdfdfd', color: '#222' },
]
const defaultSettings = { fontFamily: "'PingFang SC','Microsoft YaHei',sans-serif", fontSize: 18, fontWeight: 400, theme: 'warm' }
const settings = reactive({ ...defaultSettings })
const themeStyles = computed(() => {
  const t = themes.find(x => x.name === settings.theme) || themes[0]
  return { '--rd-bg': t.bg, '--rd-color': t.color, '--rd-font': settings.fontFamily, '--rd-size': settings.fontSize + 'px', '--rd-weight': settings.fontWeight }
})
function loadSettings() { try { const s = JSON.parse(localStorage.getItem(`reader_settings_${uid.value}`)); if (s) Object.assign(settings, s) } catch { } }
function saveSettings() { localStorage.setItem(`reader_settings_${uid.value}`, JSON.stringify({ ...settings })) }
async function onSettingChange() { saveSettings(); await measureAndBuildPages(); remapAllUserData(); loadCurrentPage() }

// ── 缓存 ──
const CACHE_PREFIX = 'rd_rc_v5_'
function cacheKey(bid) { return `${CACHE_PREFIX}${uid.value}_${bid}` }
function cacheRaw(bid, data) { try { localStorage.setItem(cacheKey(bid), JSON.stringify(data)) } catch { } }
function loadCachedRaw(bid) { try { return JSON.parse(localStorage.getItem(cacheKey(bid))) } catch { return null } }
function pageCacheKey() {
  const pw = mainRef.value ? Math.min(700, mainRef.value.clientWidth - 112) : 700
  const ph = mainRef.value ? mainRef.value.clientHeight : 600
  return `rd_pg5_${uid.value}_${bookId.value}_${settings.fontSize}_${settings.fontWeight}_${pw}_${ph}`
}

// ══════════════════════ 荧光笔高亮 ══════════════════════
const HL_COLORS = [
  { code: '#FFEB3B', name: '黄色' }, { code: '#8BC34A', name: '绿色' },
  { code: '#4FC3F7', name: '蓝色' }, { code: '#F48FB1', name: '粉色' }, { code: '#FFB74D', name: '橙色' },
]
const COLOR_PRESETS = ['#333333','#D4A24C','#e74c3c','#4FC3F7','#8BC34A','#9C27B0']

const highlights = ref([])
function hlKey() { return `rd_highlights_v2_${uid.value}` }
function loadHighlights() { try { highlights.value = JSON.parse(localStorage.getItem(hlKey()) || '[]') } catch { } }
function saveHighlights() { localStorage.setItem(hlKey(), JSON.stringify(highlights.value.map(h => {
  const {_expanded,_editing,_editBackup,...rest} = h; return rest
}))) }

function addHighlight(colorCode) {
  const text = getSelText() || popup.text; if (!text) return
  const existing = highlights.value.find(h => h.bookId === bookId.value && h.globalPage === globalPage.value && h.text === text)
  if (existing) { existing.color = colorCode; saveHighlights() }
  else { highlights.value.push({ id: Date.now(), text, color: colorCode, globalPage: globalPage.value, chapterName: currentChapterName.value, bookId: bookId.value }); saveHighlights() }
  popup.text = text
  window.getSelection()?.removeAllRanges()
}
function removeHighlightForSelection() {
  const text = getSelText() || popup.text; if (!text) return
  highlights.value = highlights.value.filter(h => !(h.globalPage === globalPage.value && h.text === text))
  saveHighlights(); popup.text = text
  window.getSelection()?.removeAllRanges()
}
function removeClickedHighlight() {
  if (popup.hlId) {
    const hl = highlights.value.find(h => h.id === popup.hlId)
    if (hl) popup.text = hl.text
    highlights.value = highlights.value.filter(h => h.id !== popup.hlId); saveHighlights()
  }
  popup.mode = 'selection'; popup.hlId = null
}
function changeHighlightColor(colorCode) {
  const hl = highlights.value.find(h => h.id === popup.hlId)
  if (hl) { hl.color = colorCode; saveHighlights() }
  if (hl) popup.text = hl.text
}
function deleteHighlight(id) { highlights.value = highlights.value.filter(h => h.id !== id); saveHighlights() }
function jumpToHL(hl) { returnPage.value = globalPage.value; goToPage(hl.globalPage); showAnnotations.value = false }

function handleMarkClick(e) {
  const markText = e.target.textContent
  const hl = highlights.value.find(h => h.globalPage === globalPage.value && h.text === markText)
  if (hl) {
    window.getSelection()?.removeAllRanges()
    const pos = { left: Math.min(e.clientX - 80, window.innerWidth - 240) + 'px', top: (e.clientY - 50) + 'px' }
    setTimeout(() => {
      popup.visible = true; popup.mode = 'highlight'; popup.hlId = hl.id; popup.text = markText
      popup.style = pos
    }, 150)
  }
}

// ── 批注 ──
const annotations = ref([])
const annoEditor = reactive({ visible: false, quote: '' })
const annoEditorRef = ref(null)
const editRefs = {}
function setEditRef(el, id) { if (el) editRefs[id] = el }
function annKey() { return `rd_ann_v5_${uid.value}` }
function loadAnnotations() { try { annotations.value = JSON.parse(localStorage.getItem(annKey()) || '[]') } catch { } annotations.value.forEach(a => { a._expanded = false; a._editing = false; a._editBackup = '' }) }
function saveAnnotations() { localStorage.setItem(annKey(), JSON.stringify(annotations.value.map(({_expanded,_editing,_editBackup,...a}) => a))) }

function openAnnotationEditor() {
  const text = getSelText() || popup.text; if (!text) return
  annoEditor.quote = text.slice(0, 500); annoEditor.visible = true
  nextTick(() => { if (annoEditorRef.value) { annoEditorRef.value.innerHTML = ''; annoEditorRef.value.focus() } })
}
function openAnnotationEditorForHL() {
  const hl = highlights.value.find(h => h.id === popup.hlId)
  if (hl) { annoEditor.quote = hl.text.slice(0, 500); annoEditor.visible = true }
  nextTick(() => { if (annoEditorRef.value) { annoEditorRef.value.innerHTML = ''; annoEditorRef.value.focus() } })
}
function closeAnnotationEditor() { annoEditor.visible = false }
function saveAnnotation() {
  const note = annoEditorRef.value?.innerHTML || ''
  if (!note.trim() && !annoEditor.quote) return
  annotations.value.push({ id: Date.now(), quote: annoEditor.quote, note, globalPage: globalPage.value, chapterName: currentChapterName.value, bookId: bookId.value })
  saveAnnotations(); closeAnnotationEditor()
}
function toggleAnnotationDetail(a) { a._expanded = !a._expanded; a._editing = false }
function editAnnotation(a) { a._editBackup = a.note; a._editing = true; nextTick(() => { const el = editRefs[a.id]; if (el) { el.innerHTML = a.note; el.focus() } }) }
function saveAnnotationEdit(a) { const el = editRefs[a.id]; if (el) a.note = el.innerHTML; a._editing = false; saveAnnotations() }
function cancelAnnotationEdit(a) { a.note = a._editBackup; a._editing = false }
function deleteAnnotation(id) { annotations.value = annotations.value.filter(a => a.id !== id); saveAnnotations() }
function jumpToAnno(a) { returnPage.value = globalPage.value; goToPage(a.globalPage); showAnnotations.value = false }
function goReturnPage() { if (returnPage.value !== null) goToPage(returnPage.value); returnPage.value = null }
function goWrite() { router.push('/write?book_id=' + bookId.value) }

// 侧栏合并展示：同页同文字的批注+高亮合并为一条
const combinedRecords = computed(() => {
  const map = new Map()
  for (const h of highlights.value) {
    if (h.bookId && h.bookId !== bookId.value) continue
    const key = `${h.globalPage}_${h.text}`; const rec = map.get(key) || { key, text: h.text }; rec.highlight = h; map.set(key, rec)
  }
  for (const a of annotations.value) {
    if (a.bookId && a.bookId !== bookId.value) continue
    const key = `${a.globalPage}_${a.quote}`; const rec = map.get(key) || { key, text: a.quote }; rec.annotation = a; map.set(key, rec)
  }
  return [...map.values()]
})

// ── 浮动弹窗 ──
const popup = reactive({ visible: false, mode: 'selection', style: {}, hlId: null, text: '' })
function getSelText() { const sel = window.getSelection(); return (sel && !sel.isCollapsed) ? sel.toString().trim() : '' }
function dismissPopup() { popup.visible = false; popup.hlId = null }
let selectionTimer = null

// 监听选区变化（替代 mouseup），与 click 事件完全解耦
function onTextSelect() {
  clearTimeout(selectionTimer)
  selectionTimer = setTimeout(() => {
    const sel = window.getSelection()
    const text = (sel && !sel.isCollapsed) ? sel.toString().trim() : ''
    if (!text) { if (popup.mode === 'selection') dismissPopup(); return }
    const range = sel.getRangeAt(0)
    const rect = range.getBoundingClientRect()
    const left = Math.min(rect.right - 80, window.innerWidth - 240)
    const top = rect.bottom + 5
    popup.visible = true; popup.mode = 'selection'; popup.hlId = null; popup.text = text
    popup.style = { left: left + 'px', top: top + 'px' }
  }, 150)
}

function execCmd(cmd, val) {
  // 确保编辑器有焦点再执行命令
  const el = annoEditorRef.value || document.querySelector('.rtf-editor[contenteditable]')
  if (el && document.activeElement !== el) el.focus()
  document.execCommand('styleWithCSS', false, true)
  document.execCommand(cmd, false, val || undefined)
}
function changeFontSize(delta) {
  // 逐步调整：获取当前选区字号，在 1~7 范围内增减
  const el = annoEditorRef.value || document.querySelector('.rtf-editor[contenteditable]')
  if (el && document.activeElement !== el) el.focus()
  let cur = 3
  try { const v = document.queryCommandValue('fontSize'); if (v && /^\d+$/.test(v)) cur = parseInt(v) } catch {}
  const next = Math.max(1, Math.min(7, cur + delta))
  document.execCommand('styleWithCSS', false, true)
  document.execCommand('fontSize', false, String(next))
}

// ── 高亮渲染（支持跨段落匹配：分页重建后文字可能被切到不同段落） ──
function trimIndent(text) {
  // 去掉段首的全角空格，统一由 CSS text-indent 控制缩进
  return text.replace(/^[　]+/, '')
}
const highlightedParas = computed(() => {
  const pageTexts = currentPageTexts.value; if (!pageTexts.length) return []
  const pageHL = highlights.value.filter(h => h.globalPage === globalPage.value)
  if (!pageHL.length) return pageTexts.map(t => escapeHtml(trimIndent(t)))

  // 为每个高亮定位其文本在当前页的分布（单段落→快速路径，跨段落→拼接匹配）
  const placements = []
  for (const h of pageHL) {
    const singleIdx = pageTexts.findIndex(t => t.includes(h.text))
    if (singleIdx >= 0) {
      placements.push({ h, paras: [{ idx: singleIdx, text: h.text }] })
      continue
    }
    // 跨段落查找：拼接当前页所有段落，定位高亮文字的起止
    const concat = pageTexts.join('')
    const pos = concat.indexOf(h.text)
    if (pos < 0) continue  // 本页找不到（页边界偏移）
    // 将字符偏移映射回各段落
    let remaining = h.text, cursor = pos
    const spans = []
    for (let i = 0; i < pageTexts.length && remaining.length > 0; i++) {
      const pLen = pageTexts[i].length
      if (cursor < pLen || (cursor === 0 && i === 0 && pos >= 0)) {
        // 重新计算当前段落在拼接字符串中的起始位置
        const paraStart = pageTexts.slice(0, i).join('').length
        const localStart = Math.max(0, pos - paraStart)
        const localEnd = Math.min(pLen, pos + h.text.length - paraStart)
        if (localEnd > localStart) {
          spans.push({ idx: i, start: localStart, end: localEnd })
        }
        cursor = paraStart + pLen
      }
    }
    if (spans.length) placements.push({ h, crossSpans: spans })
  }

  return pageTexts.map((para, pi) => {
    const raw = trimIndent(para)
    // 收集本段落的所有标记区间
    const marks = []
    for (const plc of placements) {
      if (plc.paras) {
        const m = plc.paras.find(p => p.idx === pi)
        if (m) {
          let idx = raw.indexOf(m.text)
          while (idx >= 0) {
            marks.push({ start: idx, end: idx + m.text.length, color: plc.h.color })
            idx = raw.indexOf(m.text, idx + 1)
          }
        }
      }
      if (plc.crossSpans) {
        const s = plc.crossSpans.find(sp => sp.idx === pi)
        if (s) marks.push({ start: s.start, end: s.end, color: plc.h.color })
      }
    }
    if (!marks.length) return escapeHtml(raw)

    // 合并重叠/相邻区间，按起始位置排序
    marks.sort((a, b) => a.start - b.start)
    const merged = []
    for (const m of marks) {
      const last = merged[merged.length - 1]
      if (last && m.start <= last.end + 1 && m.color === last.color) {
        last.end = Math.max(last.end, m.end)
      } else {
        merged.push({ ...m })
      }
    }

    // 构建带 mark 的 HTML
    let result = '', prev = 0
    for (const m of merged) {
      result += escapeHtml(raw.slice(prev, m.start))
      result += `<mark style="background-color:${m.color};padding:1px 0;border-radius:2px;cursor:pointer">${escapeHtml(raw.slice(m.start, m.end))}</mark>`
      prev = m.end
    }
    result += escapeHtml(raw.slice(prev))
    return result
  })
})

// ══════════════════════ 分页引擎 ══════════════════════
function escapeHtml(s) { return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;') }
const PARA_STYLE = () => `font-family:${settings.fontFamily};font-size:${settings.fontSize}px;font-weight:${settings.fontWeight};line-height:2;margin:0 0 0.5em;text-indent:2em`
const TITLE_STYLE = 'font-size:20px;font-weight:bold;margin:0 0 18px;padding-bottom:8px;border-bottom:1px solid rgba(0,0,0,.15);text-align:center'

function fillOnePage(measureDiv, paragraphs, startIdx, pageH, includeTitle, titleName) {
  measureDiv.innerHTML = ''
  if (includeTitle) { const t = document.createElement('div'); t.style.cssText = TITLE_STYLE; t.textContent = titleName; measureDiv.appendChild(t) }
  const texts = []
  for (let i = startIdx; i < paragraphs.length; i++) {
    const p = document.createElement('p'); p.style.cssText = PARA_STYLE(); p.textContent = paragraphs[i]; measureDiv.appendChild(p)
    if (measureDiv.scrollHeight > pageH) { measureDiv.removeChild(p); return { texts, overflowIdx: i, overflowText: paragraphs[i] } }
    texts.push(paragraphs[i])
  }
  return { texts, overflowIdx: paragraphs.length, overflowText: null }
}
function splitLongPara(measureDiv, text, pageH, includeTitle, titleName) {
  measureDiv.innerHTML = ''
  if (includeTitle) { const t = document.createElement('div'); t.style.cssText = TITLE_STYLE; t.textContent = titleName; measureDiv.appendChild(t) }
  let lo = 1, hi = text.length, best = 0; const p = document.createElement('p'); p.style.cssText = PARA_STYLE(); measureDiv.appendChild(p)
  while (lo <= hi) { const mid = Math.floor((lo+hi)/2); p.textContent = text.slice(0,mid); if (measureDiv.scrollHeight <= pageH) { best=mid; lo=mid+1 } else hi=mid-1 }
  measureDiv.removeChild(p); const cut = Math.max(1,best); return { first: text.slice(0,cut), remaining: text.slice(cut) }
}

async function measureAndBuildPages() {
  if (!Object.keys(rawChapters.value).length) return
  measuring.value = true; measureProgress.value = 0; await nextTick(); await new Promise(r => requestAnimationFrame(r))
  const cachedKey = pageCacheKey()
  let cached = null
  try { cached = JSON.parse(localStorage.getItem(cachedKey)) } catch {}
  // 迁移：尝试不含 uid 的旧 key，避免因 uid 隔离导致缓存失效引起分页不一致
  if (!cached?.length && uid.value > 0) {
    const oldKey = cachedKey.replace(`_${uid.value}_`, '_')
    try {
      const old = JSON.parse(localStorage.getItem(oldKey))
      if (old?.length) { cached = old; try { localStorage.setItem(cachedKey, JSON.stringify(old)) } catch {} }
    } catch {}
  }
  if (cached?.length) { if (mainRef.value) pageH.value = Math.max(300, mainRef.value.clientHeight - 60 - 24); pages.value = cached; measuring.value = false; measureProgress.value = 100; return }
  if (!mainRef.value) { measuring.value = false; return }
  const measureDiv = document.createElement('div')
  measureDiv.style.cssText = `width:${Math.min(700,(mainRef.value.clientWidth||800)-112)}px;max-width:700px;visibility:hidden;pointer-events:none;position:absolute;left:0;top:0`
  mainRef.value.appendChild(measureDiv)
  const _pageH = Math.max(300, mainRef.value.clientHeight - 48 - 36); pageH.value = _pageH
  const orders = Object.keys(rawChapters.value).map(Number).sort((a,b)=>a-b); const result = []
  for (let ci = 0; ci < orders.length; ci++) {
    const ch = rawChapters.value[orders[ci]]; const paragraphs = (ch.content||'').split('\n').filter(p=>p.trim())
    if (!paragraphs.length) continue
    let localPage=0, idx=0, contFirst=false
    while (idx < paragraphs.length) {
      const isFirst = localPage===0; const r = fillOnePage(measureDiv,paragraphs,idx,_pageH,isFirst,ch.name)
      if (r.texts.length===0 && r.overflowText) {
        const s = splitLongPara(measureDiv,r.overflowText,_pageH,isFirst,ch.name)
        if (s.first) { result.push({texts:[s.first],chapterIdx:orders[ci],chapterName:ch.name,isFirst,continuationFirst:contFirst}); localPage++; contFirst=false }
        if (s.remaining) { paragraphs[r.overflowIdx]=s.remaining; contFirst=true } else { idx=r.overflowIdx+1; contFirst=false }
      } else { result.push({texts:[...r.texts],chapterIdx:orders[ci],chapterName:ch.name,isFirst,continuationFirst:contFirst}); localPage++; idx=r.overflowIdx; contFirst=false }
    }
    measureProgress.value=Math.round(((ci+1)/orders.length)*100); if (ci%5===4) await new Promise(r=>setTimeout(r,0))
  }
  mainRef.value.removeChild(measureDiv)
  try { localStorage.setItem(cachedKey, JSON.stringify(result)) } catch { }
  pages.value = result
  const allPaged = result.flatMap(p=>p.texts).join(''); const allRaw = Object.values(rawChapters.value).flatMap(ch=>(ch.content||'').split('\n').filter(p=>p.trim())).join('')
  if (allPaged!==allRaw) { console.error('%c[Reader] ❌ 分页丢失！','color:red') } else { console.log(`%c[Reader] ✅ 分页完整 (${allPaged.length}字/${result.length}页)`,'color:green') }
  measuring.value=false; measureProgress.value=100
}
function remapAllUserData() {
  // 字体/页面尺寸变化后，分页边界偏移 → 重新计算高亮和批注的 globalPage
  if (!pages.value.length || !bookId.value) return
  const pageInfo = pages.value.map(p => ({
    chapterName: p.chapterName,
    allText: p.texts.join('')
  }))

  function findBestPage(text, chapterName) {
    // 优先在同章节中匹配
    for (let i = 0; i < pageInfo.length; i++) {
      if (pageInfo[i].chapterName === chapterName && pageInfo[i].allText.includes(text)) return i
    }
    // 回退：全文匹配
    for (let i = 0; i < pageInfo.length; i++) {
      if (pageInfo[i].allText.includes(text)) return i
    }
    return -1
  }

  let hlChanged = false, annChanged = false

  // 高亮重映射
  for (const h of highlights.value) {
    if (h.bookId && h.bookId !== bookId.value) continue
    const best = findBestPage(h.text, h.chapterName)
    if (best >= 0 && best !== h.globalPage) {
      h.globalPage = best; h.bookId = h.bookId || bookId.value; hlChanged = true
    }
  }
  if (hlChanged) saveHighlights()

  // 批注重映射（quote 字段对应选中文字）
  for (const a of annotations.value) {
    if (a.bookId && a.bookId !== bookId.value) continue
    const best = findBestPage(a.quote, a.chapterName)
    if (best >= 0 && best !== a.globalPage) {
      a.globalPage = best; a.bookId = a.bookId || bookId.value; annChanged = true
    }
  }
  if (annChanged) saveAnnotations()

  // 书签重映射（text 字段为当前页首段前60字锚点）
  let bmChanged = false
  for (const bm of bookmarks.value) {
    if (bm.bookId && bm.bookId !== bookId.value) continue
    if (!bm.text) { bm.bookId = bm.bookId || bookId.value; continue }  // 旧书签无锚点文字，无法精确定位
    const best = findBestPage(bm.text, bm.chapterName)
    if (best >= 0 && best !== bm.globalPage) {
      bm.globalPage = best; bm.bookId = bm.bookId || bookId.value; bmChanged = true
    }
  }
  if (bmChanged) saveBookmarks()
}
function loadCurrentPage() {
  if (!pages.value.length) return; const gp=Math.min(globalPage.value,pages.value.length-1); globalPage.value=gp
  currentPageTexts.value=pages.value[gp].texts; currentChapter.value=pages.value[gp].chapterIdx; currentChapterName.value=pages.value[gp].chapterName
  nextTick(()=>{const box=mainRef.value?.querySelector('.rd-page-box');if(box){const rh=box.scrollHeight,diff=rh-pageH.value;if(diff>1)console.warn(`[Reader] ⚠️ 页${gp+1} 溢出${diff.toFixed(0)}px`)}})
}

// ── 导航 ──
function prevPage() { if (globalPage.value>0) goPage(globalPage.value-1) }
function nextPage() { if (globalPage.value<totalPages.value-1) { goPage(globalPage.value+1); if (globalPage.value>=totalPages.value-1) reachedEnd.value=true } }
function goPage(t) { if (!isLoggedIn.value&&t>=TRIAL_PAGES) { showLoginModal.value=true; return } globalPage.value=t; loadCurrentPage() }
function onClickPage(e) {
  // 1. 点击 <mark> 高亮文字 → 显示高亮编辑弹窗，不翻页
  if (e.target.tagName === 'MARK') { handleMarkClick(e); return }

  // 2. 弹窗开着时 → 单击弹窗外任意处关闭，不翻页
  if (popup.visible) {
    if (e.target.closest('.rd-selection-menu')) return
    dismissPopup(); return
  }

  // 3. 有选中文字 → 不翻页
  const sel2 = window.getSelection(); if (sel2 && !sel2.isCollapsed && sel2.toString().trim()) return

  // 4. 正常翻页
  const r = e.currentTarget.getBoundingClientRect(); if (e.clientY-r.top<r.height/2) prevPage(); else nextPage()
}
function onWheelPage(e) { if (e.deltaY>0) nextPage(); else prevPage() }
function jumpToChapter(i) { const o=chapters.value[i]?.order; const fp=pages.value.findIndex(p=>p.chapterIdx===o); if(fp>=0) goPage(fp) }
function goToPage(gp) { goPage(gp); showBookmarks.value=false }
function goBack(){if(isUserCreated.value){router.push('/profile')}else{router.back()}}

// ── 登录回跳 ──
// 关闭侧栏时清除返回按钮（用户不需要返回）
watch(showAnnotations, (v) => { if (!v) returnPage.value = null })
function goLogin() { sessionStorage.setItem('reader_return',JSON.stringify({bookId:bookId.value,page:globalPage.value})); router.push('/login') }
function goRegister() { sessionStorage.setItem('reader_return',JSON.stringify({bookId:bookId.value,page:globalPage.value})); router.push('/register') }

// ── 书签 ──
const bookmarks=ref([])
const currentBookBookmarks = computed(() => bookmarks.value.filter(b => !b.bookId || b.bookId === bookId.value))
function bmKey() { return `rd_bookmarks_v4_${uid.value}` }
function loadBookmarks() { try { bookmarks.value=JSON.parse(localStorage.getItem(bmKey())||'[]') } catch { } }
function saveBookmarks() { localStorage.setItem(bmKey(),JSON.stringify(bookmarks.value)) }
function addBookmark() {
  if(bookmarks.value.find(b=>b.globalPage===globalPage.value&&b.bookId===bookId.value)) return
  // 取当前页第一段前60字作为定位锚点，字体变化后靠文字重新定位
  const anchor = (currentPageTexts.value[0] || '').slice(0, 60)
  bookmarks.value.push({id:Date.now(),globalPage:globalPage.value,chapterName:currentChapterName.value,text:anchor,bookId:bookId.value})
  saveBookmarks()
}
function deleteBookmark(id) { bookmarks.value=bookmarks.value.filter(b=>b.id!==id); saveBookmarks() }

// ── 阅读计时 ──
function startReadingTimer() {
  if (readingTimer) return
  readingTimer = setInterval(() => {
    if (document.visibilityState === 'visible') readingSeconds.value++
  }, 1000)
}
async function saveReadingTime() {
  if (readingSeconds.value <= 0 || !isLoggedIn.value) return
  try {
    await request.post('/user/reading-time', { book_id: bookId.value, duration_seconds: readingSeconds.value })
    readingSeconds.value = 0
  } catch {}
}
async function saveProgressToBackend() {
  if (!isLoggedIn.value || !pages.value.length) return
  try {
    await request.post('/user/progress', { book_id: bookId.value, current_page: globalPage.value, progress_pct: calculatedProgress.value })
  } catch {}
}

// ── 键盘/窗口 ──
function onKeyDown(e) { if(['INPUT','TEXTAREA'].includes(document.activeElement?.tagName)||document.activeElement?.isContentEditable) return; if(e.key==='ArrowLeft'||e.key==='ArrowUp') prevPage(); else if(e.key==='ArrowRight'||e.key==='ArrowDown') nextPage() }
let resizeTimer=null
function onResize() { clearTimeout(resizeTimer); resizeTimer=setTimeout(async()=>{try{localStorage.removeItem(pageCacheKey())}catch{}await measureAndBuildPages();remapAllUserData();loadCurrentPage()},400) }

onMounted(async()=>{
  // 阅读器独占：防止外层页面滚动
  document.documentElement.style.overflow = 'hidden'
  document.body.style.overflow = 'hidden'
  document.body.style.height = '100%'
  loadSettings(); loadBookmarks(); loadAnnotations(); loadHighlights()
  bookId.value=Number(route.params.id)
  try{const r=await request.get(`/books/${bookId.value}`);if(r.code===200){bookTitle.value=r.data.title;bookStore.currentBook=r.data;if(r.data.description&&r.data.description.startsWith('用户创作')){isUserCreated.value=true}}}catch{}
  let cached=isUserCreated.value?null:loadCachedRaw(bookId.value)
  if(!cached){
    const BATCH_SIZE = 6
    loading.value=true; loadProgress.value=0; loadedChapters.value=0
    try{const r=await request.get(`/books/${bookId.value}/chapters`);if(r.code===200){chapters.value=r.data.chapters;totalCharsAllBook.value=r.data.total_chars||0}}catch{}
    const chList = chapters.value
    for(let i=0;i<chList.length;i+=BATCH_SIZE){
      const batch=chList.slice(i,i+BATCH_SIZE)
      const results=await Promise.allSettled(batch.map(ch=>request.get(`/books/${bookId.value}/chapters/${ch.order}`)))
      results.forEach((res,j)=>{
        if(res.status==='fulfilled'&&res.value?.code===200){rawChapters.value[batch[j].order]={name:res.value.data.chapter_name,content:res.value.data.content||''}}
        loadedChapters.value++;loadProgress.value=Math.round(loadedChapters.value/chList.length*100)
      })
    }
    if(Object.keys(rawChapters.value).length&&!isUserCreated.value)cacheRaw(bookId.value,Object.entries(rawChapters.value).map(([k,v])=>({order:Number(k),...v})))
    loading.value=false
  }else{chapters.value=cached.map(c=>({order:c.order,name:c.name}));cached.forEach(c=>{rawChapters.value[c.order]=c});totalCharsAllBook.value=cached.reduce((s,c)=>s+(c.content||'').length,0)}
  await measureAndBuildPages(); remapAllUserData()
  let restore=0;const qp=Number(route.query.page);if(qp>0)restore=qp-1;else{const ret=sessionStorage.getItem('reader_return');if(ret){try{const r=JSON.parse(ret);if(r.bookId==bookId.value)restore=r.page||0}catch{}}}
  if(restore>0&&restore<pages.value.length)globalPage.value=restore
  if(!isLoggedIn.value&&globalPage.value>=TRIAL_PAGES){globalPage.value=0;showLoginModal.value=true}
  loadCurrentPage()
  // 自动加入"在读"书架 + 启动阅读计时
  if(isLoggedIn.value){
    if(!isUserCreated.value){try{await request.post('/shelves/items',{book_id:bookId.value,shelf_type:'reading'})}catch{}}
    startReadingTimer()
    saveTimer=setInterval(async()=>{await saveReadingTime();await saveProgressToBackend()},SAVE_INTERVAL*1000)
  }
  document.addEventListener('keydown',onKeyDown);window.addEventListener('resize',onResize)
})
onBeforeUnmount(async ()=>{
  document.removeEventListener('keydown',onKeyDown);window.removeEventListener('resize',onResize)
  if(readingTimer){clearInterval(readingTimer);readingTimer=null}
  if(saveTimer){clearInterval(saveTimer);saveTimer=null}
  saveReadingTime();saveProgressToBackend()
  // 翻到最后一页后退出 → 保存100%进度 + 自动标记为"已读"
  if(reachedEnd.value&&isLoggedIn.value){
    try{await request.post('/user/progress',{book_id:bookId.value,current_page:totalPages.value-1,progress_pct:100})}catch{}
    if(!isUserCreated.value){try{await shelvesAPI.addItem(bookId.value,'read')}catch{}}
  }
  document.documentElement.style.overflow = ''
  document.body.style.overflow = ''
  document.body.style.height = ''
})
</script>

<style scoped>
.reader-app{height:calc(100vh - 56px);max-height:calc(100vh - 56px);margin:-16px -36px 0;overflow:hidden!important;display:flex;flex-direction:column;background:var(--rd-bg,#F5F0DF);color:var(--rd-color,#3d3226)}
.rd-header{display:flex;align-items:center;gap:12px;padding:8px 16px;background:rgba(255,255,255,.92);backdrop-filter:blur(8px);border-bottom:1px solid #e0d8c8;flex-shrink:0;z-index:50}
.rd-title{flex:1;font-size:15px;font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#2C3E50}
.rd-header-right{display:flex;align-items:center;gap:4px}.rd-page-info{font-size:12px;color:#999}
.rd-btn{background:none;border:none;font-size:16px;cursor:pointer;padding:4px 10px;border-radius:6px;color:#555}.rd-btn:hover{background:rgba(0,0,0,.05)}
.rd-body{flex:1;display:flex;position:relative;overflow:hidden!important;min-height:0}
.rd-toc{width:260px;flex-shrink:0;background:rgba(255,255,255,.96);border-right:1px solid #e8dfce;display:flex;flex-direction:column;overflow:hidden}
.rd-toc h3{font-size:15px;margin:0;padding:16px 16px 10px;color:#2C3E50;flex-shrink:0}
.toc-list{flex:1;overflow-y:auto;overflow-x:hidden;padding:0 16px 16px;overscroll-behavior:contain}
.toc-ch{padding:7px 10px;cursor:pointer;border-radius:6px;font-size:13px;color:#555;display:flex;gap:6px}.toc-ch:hover{background:#F5F0EB}.toc-ch.active{background:#FFF8E1;color:#D4A24C;font-weight:600}.toc-num{color:#999;min-width:24px}

.rd-main{flex:1;overflow:hidden!important;position:relative;cursor:pointer;display:flex;flex-direction:column;align-items:center;justify-content:flex-start;padding:28px 56px 20px;min-height:0}
.rd-loading{padding:60px;text-align:center;color:#999;font-size:15px}
.rd-loading-inner{display:flex;flex-direction:column;align-items:center;gap:12px}
.rd-loading-spinner{width:50px;height:50px;animation:rd-spin 1.2s linear infinite}
@keyframes rd-spin{to{transform:rotate(360deg)}}
.rd-spinner-circle{animation:rd-dash 1.5s ease-in-out infinite}
@keyframes rd-dash{0%{stroke-dasharray:1,150;stroke-dashoffset:0}50%{stroke-dasharray:90,150;stroke-dashoffset:-35}100%{stroke-dasharray:90,150;stroke-dashoffset:-124}}
.rd-loading-text{font-size:14px;color:#666}
.rd-loading-bar-wrap{width:220px;height:6px;background:#e8dfce;border-radius:3px;overflow:hidden}
.rd-loading-bar{height:100%;background:linear-gradient(90deg,#D4A24C,#e8c97a);border-radius:3px;transition:width .3s}
.rd-loading-pct{font-size:12px;color:#999}
.rd-loading-sub{font-size:11px;color:#bbb}
.rd-progress-bar-wrap{width:100%;max-width:700px;display:flex;align-items:center;gap:8px;margin-top:16px;flex-shrink:0}
.rd-progress-bar{flex:1;height:3px;background:linear-gradient(90deg,#D4A24C,#e8c97a);border-radius:2px;transition:width .3s}
.rd-progress-txt{font-size:11px;color:#aaa;min-width:36px;text-align:right}
.rd-page-box{width:100%;max-width:700px;overflow:hidden!important;flex-shrink:0}
.rd-ctitle{text-align:center;font-size:20px;font-weight:bold;margin:0 0 18px;padding-bottom:8px;border-bottom:1px solid rgba(0,0,0,.1)}
.rd-para{font-family:var(--rd-font);font-size:var(--rd-size);font-weight:var(--rd-weight);line-height:2;margin:0 0 .5em;text-indent:2em}
.rd-para-cont{text-indent:0 !important}
.rd-para :deep(mark){padding:1px 0;border-radius:2px}
.rd-empty{padding:60px;text-align:center;color:#999}.rd-empty-sm{padding:20px;text-align:center;color:#999;font-size:13px}

.rd-panel{width:280px;flex-shrink:0;background:rgba(255,255,255,.96);border-left:1px solid #e8dfce;display:flex;flex-direction:column;overflow:hidden}
.rd-panel h3{font-size:15px;margin:0;padding:16px 16px 10px;color:#2C3E50;flex-shrink:0}
.rd-settings-panel{overflow-y:auto;padding:0 16px}.panel-scroll{flex:1;overflow-y:auto;padding:0 16px}
.set-group{margin-bottom:14px}.set-group label{display:block;font-size:12px;color:#888;margin-bottom:4px}.set-group select,.set-group input[type=range]{width:100%}
.theme-grid{display:grid;grid-template-columns:1fr 1fr;gap:6px}.theme-btn{padding:8px;border:2px solid transparent;border-radius:8px;font-size:12px;cursor:pointer}.theme-btn.active{border-color:#D4A24C}
.bm-item{padding:8px 10px;border-bottom:1px solid #eee;font-size:12px;position:relative;cursor:pointer}.bm-item:hover{background:#f8f8f8}.bm-ch{font-weight:600;color:#2C3E50;display:block}.bm-page{color:#999}.bm-text{color:#999;font-size:11px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;display:block}
.bm-del{position:absolute;right:8px;top:8px;background:none;border:none;color:#ccc;cursor:pointer}.bm-del:hover{color:#e74c3c}
.rd-btn-outline{padding:6px 16px;background:none;border:1px solid #ccc;color:#555;border-radius:8px;font-size:12px;cursor:pointer}.rd-btn-outline.sm{width:100%;margin-bottom:8px}
.rd-btn-primary{padding:10px 28px;background:#D4A24C;color:#fff;border:none;border-radius:10px;font-size:15px;cursor:pointer}
.rd-btn-sm{padding:3px 10px;border:1px solid #ddd;border-radius:5px;background:#fff;font-size:12px;cursor:pointer;margin-right:4px}.rd-btn-sm:hover{background:#f5f5f5}.rd-btn-sm.primary{background:#D4A24C;color:#fff;border-color:#D4A24C}.rd-btn-sm.danger{color:#e74c3c;border-color:#e74c3c}
.rd-icon-btn{background:none;border:none;font-size:13px;cursor:pointer;padding:2px 4px;color:#aaa;border-radius:4px;flex-shrink:0}.rd-icon-btn:hover{background:#f0f0f0;color:#555}

/* 侧栏 */
.rd-ann-panel{width:300px}
.ann-card{border-bottom:1px solid #eee;padding:6px 0}
.ann-card-header{display:flex;align-items:center;gap:5px;cursor:pointer;padding:4px 0;font-size:12px}.ann-card-header:hover{background:#fafafa}
.ann-q{color:#D4A24C;font-style:italic;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.ann-pg{color:#aaa;font-size:11px;white-space:nowrap}
.ann-icon{font-size:12px;flex-shrink:0}
.ann-card-body{padding:6px 0 6px 8px}
.ann-note-display{font-size:13px;color:#555;line-height:1.7;padding:6px 0;max-height:200px;overflow-y:auto;text-align:left}
.ann-card-actions{display:flex;gap:2px;margin-top:4px}
.ann-edit-area{margin-top:4px}
.anno-quote-ref{color:#D4A24C;font-style:italic;font-size:14px;margin:0 0 12px;text-align:left}
.hl-swatch{width:14px;height:14px;border-radius:3px;flex-shrink:0;border:1px solid rgba(0,0,0,.15)}

/* 选中浮窗 */
.rd-selection-menu{position:fixed;z-index:3000;background:#fff;border-radius:10px;box-shadow:0 4px 20px rgba(0,0,0,.2);padding:8px;min-width:200px}
.sel-hl-row{display:flex;align-items:center;gap:4px;margin-bottom:6px;padding-bottom:6px;border-bottom:1px solid #eee}
.sel-hl-label{font-size:11px;color:#999;margin-right:2px}
.sel-hl-btn{width:22px;height:22px;border-radius:50%;border:2px solid rgba(0,0,0,.1);cursor:pointer}.sel-hl-btn:hover{border-color:#D4A24C;transform:scale(1.15)}
.sel-hl-btn.hl-cancel{background:#fff;border-color:#e74c3c;position:relative}.sel-hl-btn.hl-cancel::after{content:'';position:absolute;top:50%;left:15%;right:15%;height:2px;background:#e74c3c;transform:rotate(-45deg)}
.sel-anno-btn{display:block;width:100%;padding:6px 12px;border:none;background:none;font-size:13px;cursor:pointer;border-radius:6px;text-align:left}.sel-anno-btn:hover{background:#FFF8E1}

/* 富文本 */
.rtf-toolbar{display:flex;align-items:center;gap:2px;padding:6px 8px;background:#f8f8f8;border:1px solid #e0e0e0;border-radius:8px 8px 0 0;flex-wrap:wrap}
.rtf-toolbar button{padding:4px 8px;border:1px solid transparent;border-radius:4px;background:none;cursor:pointer;font-size:13px;min-width:28px}.rtf-toolbar button:hover{background:#eee;border-color:#ccc}
.rtf-toolbar select{font-size:12px;padding:2px;border:1px solid #ddd;border-radius:4px}
.rtf-toolbar input[type=color]{width:24px;height:24px;border:1px solid #ddd;border-radius:4px;cursor:pointer;padding:0}
.rtf-toolbar.mini{padding:3px 4px;gap:1px}.rtf-toolbar.mini button{padding:2px 5px;font-size:11px;min-width:20px}.rtf-toolbar.mini select{font-size:10px}.rtf-toolbar.mini input[type=color]{width:18px;height:18px}
.tb-sep{color:#ddd;margin:0 2px}
.cp-swatch{width:18px;height:18px;border-radius:3px;cursor:pointer;border:1px solid rgba(0,0,0,.15);flex-shrink:0}.cp-swatch:hover{border-color:#D4A24C}
.rtf-toolbar.mini .cp-swatch{width:14px;height:14px}
.rtf-editor{min-height:100px;max-height:250px;overflow-y:auto;border:1px solid #e0e0e0;border-top:none;border-radius:0 0 8px 8px;padding:10px 12px;font-size:14px;line-height:1.7;outline:none;text-align:left}
.rtf-editor.small{min-height:50px;max-height:150px;font-size:13px;padding:6px 8px}
.rd-anno-modal{width:520px;max-width:90vw}

/* 返回浮钮 */
.rd-return-float{position:fixed;bottom:30px;left:50%;transform:translateX(-50%);z-index:4500;background:#D4A24C;color:#fff;padding:10px 24px;border-radius:24px;font-size:14px;cursor:pointer;box-shadow:0 4px 16px rgba(0,0,0,.25)}.rd-return-float:hover{background:#c8933a}
.rd-write-float{position:fixed;bottom:90px;right:24px;z-index:4500;width:48px;height:48px;border-radius:50%;background:#2C3E50;color:#D4A24C;font-size:20px;display:flex;align-items:center;justify-content:center;cursor:pointer;box-shadow:0 4px 16px rgba(0,0,0,.25);transition:all .2s}.rd-write-float:hover{transform:scale(1.1);background:#1a2a4a}

/* 弹窗 */
.rd-modal-overlay{position:fixed;inset:0;z-index:4000;background:rgba(0,0,0,.5);display:flex;align-items:center;justify-content:center}
.rd-modal{background:#fff;border-radius:16px;padding:32px 40px;text-align:center;position:relative;box-shadow:0 16px 48px rgba(0,0,0,.3)}
.rd-modal h3{margin:0 0 8px;font-size:18px}.rd-modal p{color:#888;margin:0 0 20px}
.rd-modal-btns{display:flex;gap:12px;justify-content:center;margin-top:14px}
.rd-modal-close{position:absolute;top:10px;right:14px;background:none;border:none;font-size:18px;color:#999;cursor:pointer}

.slide-enter-active,.slide-leave-active{transition:transform .3s ease}.slide-enter-from,.slide-leave-to{transform:translateX(-100%)}
@media(max-width:700px){.rd-main{padding:20px 16px}.rd-toc,.rd-panel,.rd-ann-panel{position:absolute;top:0;bottom:0;z-index:40}.rd-toc{left:0}.rd-panel,.rd-ann-panel{right:0}}
</style>
