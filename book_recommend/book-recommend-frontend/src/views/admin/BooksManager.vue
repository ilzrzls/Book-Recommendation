<template>
  <div class="books-manager">
    <div class="page-header">
      <h2>📚 图书管理</h2>
    </div>

    <!-- Search + 新增按钮 -->
    <div class="toolbar">
      <el-input v-model="keyword" placeholder="搜索书名..." style="width:300px" clearable @keyup.enter="search" @clear="search" />
      <el-button @click="search">搜索</el-button>
      <el-button type="primary" class="add-btn" @click="openDialog()">+ 新增图书</el-button>
    </div>

    <!-- Table -->
    <el-table :data="books" v-loading="loading" stripe style="width:100%" :row-class-name="rowClassName">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="title" label="书名" min-width="160" show-overflow-tooltip />
      <el-table-column prop="author" label="作者" width="120" show-overflow-tooltip />
      <el-table-column prop="publisher" label="出版社" width="120" show-overflow-tooltip />
      <el-table-column prop="score" label="评分" width="70" />
      <el-table-column prop="status" label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.status === 1 ? 'success' : 'danger'" size="small">
            {{ row.status === 1 ? '上架' : '下架' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openDialog(row)">编辑</el-button>
          <el-popconfirm title="确定下架该图书？" @confirm="handleDelete(row.id)">
            <template #reference>
              <el-button size="small" type="danger" :disabled="row.status === 0">下架</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- Pagination -->
    <div class="pagination-wrap">
      <el-pagination :current-page="page" :page-size="size" :total="total"
        layout="total, prev, pager, next" @current-change="(p) => { page = p; loadBooks() }" />
    </div>

    <!-- Create/Edit Dialog -->
    <el-dialog v-model="dialog.visible" :title="dialog.isEdit ? '编辑图书' : '新增图书'" width="600px" destroy-on-close>
      <el-form :model="dialog.form" label-width="80px">
        <el-form-item label="书名">
          <el-input v-model="dialog.form.title" />
        </el-form-item>
        <el-form-item label="ISBN">
          <el-input v-model="dialog.form.isbn" />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="作者">
              <el-input v-model="dialog.form.author" placeholder="多个用 / 分隔" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="出版社">
              <el-input v-model="dialog.form.publisher" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="8">
            <el-form-item label="出版年">
              <el-input-number v-model="dialog.form.publish_year" :min="1000" :max="2099" controls-position="right" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="页数">
              <el-input-number v-model="dialog.form.total_pages" :min="1" controls-position="right" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="评分">
              <el-input-number v-model="dialog.form.score" :min="0" :max="10" :step="0.1" controls-position="right" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="封面">
          <div class="cover-upload-row">
            <el-input v-model="dialog.form.cover" placeholder="输入URL 或 上传图片文件" style="flex:1" />
            <input ref="coverFileRef" type="file" accept="image/jpeg,image/png,image/webp" style="display:none" @change="handleCoverUpload" />
            <el-button @click="coverFileRef.click()" :loading="coverUploading">
              <el-icon><Upload /></el-icon> 上传
            </el-button>
          </div>
          <img v-if="dialog.form.cover" :src="dialog.form.cover" class="cover-preview" />
        </el-form-item>
        <el-form-item label="简介">
          <el-input v-model="dialog.form.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog.visible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { adminAPI } from '../../api/admin'
import { ElMessage } from 'element-plus'
import request from '../../api/request'

const route = useRoute()
const books = ref([])
const loading = ref(false)
const page = ref(1)
const size = ref(20)
const total = ref(0)
const keyword = ref('')
const highlightId = ref(null)
const coverFileRef = ref(null)
const coverUploading = ref(false)

const dialog = reactive({
  visible: false, isEdit: false,
  form: { id: null, title: '', isbn: '', author: '', publisher: '', publish_year: null, total_pages: null, score: 0, cover: '', description: '' }
})

function resetForm() {
  dialog.form = { id: null, title: '', isbn: '', author: '', publisher: '', publish_year: null, total_pages: null, score: 0, cover: '', description: '' }
}

async function handleCoverUpload(e) {
  const file = e.target.files?.[0]
  if (!file) return
  if (!['image/jpeg','image/png','image/webp'].includes(file.type)) {
    ElMessage.error('仅支持 JPG、PNG、WebP 格式'); e.target.value = ''; return
  }
  if (file.size > 5 * 1024 * 1024) { ElMessage.error('图片不能超过 5MB'); e.target.value = ''; return }
  coverUploading.value = true
  try {
    const fd = new FormData(); fd.append('file', file)
    const res = await request.post('/admin/books/upload-cover', fd)
    if (res.code === 200) {
      dialog.form.cover = res.data.cover_url
      ElMessage.success('封面上传成功')
    } else {
      ElMessage.error(res.message || '上传失败')
    }
  } catch { ElMessage.error('上传失败') }
  coverUploading.value = false; e.target.value = ''
}

function openDialog(row) {
  if (row) {
    dialog.isEdit = true
    dialog.form = { ...row }
  } else {
    dialog.isEdit = false
    resetForm()
  }
  dialog.visible = true
}

async function loadBooks() {
  loading.value = true
  const res = await adminAPI.getBooks(page.value, size.value, keyword.value)
  if (res.code === 200) {
    books.value = res.data.items
    total.value = res.data.total
  }
  loading.value = false
}

function search() { page.value = 1; loadBooks() }

async function handleSave() {
  const d = dialog.form
  if (dialog.isEdit) {
    const res = await adminAPI.updateBook(d.id, d)
    if (res.code === 200) ElMessage.success('图书已更新')
  } else {
    const res = await adminAPI.createBook(d)
    if (res.code === 200) ElMessage.success('图书已创建')
  }
  dialog.visible = false
  loadBooks()
}

async function handleDelete(id) {
  const res = await adminAPI.deleteBook(id)
  if (res.code === 200) ElMessage.success('已下架')
  loadBooks()
}

function rowClassName({ row }) {
  if (highlightId.value && row.id === parseInt(highlightId.value)) return 'highlight-row'
  return ''
}

function handleHighlightFromKG() {
  const hl = route.query.highlight
  const kw = route.query.keyword
  if (hl) {
    highlightId.value = hl
    if (kw) keyword.value = decodeURIComponent(kw)
    loadBooks()
    setTimeout(() => {
      const el = document.querySelector('.highlight-row')
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }, 400)
    setTimeout(() => { highlightId.value = null }, 5000)
  }
}

onMounted(() => {
  handleHighlightFromKG()
  if (!highlightId.value) loadBooks()
})
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.page-header h2 { font-size: 17px; color: #2C3E50; margin: 0; }
.toolbar { display: flex; gap: 6px; margin-bottom: 8px; align-items: center; }
.add-btn { margin-left: 160px; }
.pagination-wrap { margin-top: 10px; display: flex; justify-content: flex-end; }
.cover-upload-row { display: flex; gap: 8px; align-items: center; }
.cover-preview { width: 100px; height: 140px; object-fit: cover; border-radius: 6px; margin-top: 8px; border: 1px solid #eee; }

/* 知识图谱跳转高亮 */
:deep(.highlight-row) {
  animation: highlight-flash 0.6s ease-in-out 3;
  background-color: #fef3e2 !important;
}
:deep(.highlight-row > td) {
  background-color: #fef3e2 !important;
  border-bottom: 2px solid #D4A24C !important;
}
@keyframes highlight-flash {
  0%, 100% { background-color: #fef3e2; }
  50% { background-color: #ffe4b5; box-shadow: inset 0 0 12px rgba(212,162,76,0.3); }
}
</style>
