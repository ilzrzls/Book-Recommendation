<template>
  <div class="search-page">
    <div class="search-header">
      <h2>搜索结果</h2>
      <p v-if="keyword || searchTags" class="search-info">
        搜索<span v-if="keyword">「{{ keyword }}」</span><span v-if="searchTags"> 标签「{{ searchTags }}」</span>，找到 {{ bookStore.searchTotal }} 本书
      </p>
    </div>

    <!-- Search input -->
    <div class="search-input-row">
      <el-input
        v-model="keyword"
        placeholder="输入书名、作者或标签搜索..."
        size="large"
        clearable
        @keyup.enter="doSearch"
      >
        <template #append>
          <el-button type="primary" @click="doSearch">搜索</el-button>
        </template>
      </el-input>
    </div>

    <!-- Results -->
    <div class="search-results" v-loading="bookStore.loading">
      <div v-if="bookStore.searchResults.length > 0" class="result-grid">
        <BookCard
          v-for="book in bookStore.searchResults"
          :key="book.id"
          :book="book"
        />
      </div>
      <el-empty v-else-if="!bookStore.loading && keyword" description="未找到匹配的图书，试试其他关键词" />

      <!-- Pagination -->
      <div v-if="bookStore.searchTotal > 10" class="pagination">
        <el-pagination
          v-model:current-page="page"
          :page-size="10"
          :total="bookStore.searchTotal"
          layout="prev, pager, next"
          @current-change="handlePageChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useBookStore } from '../stores/book'
import BookCard from '../components/common/BookCard.vue'

const route = useRoute()
const router = useRouter()
const bookStore = useBookStore()

const keyword = ref(route.query.keyword || '')
const searchTags = ref(route.query.tags || '')
const priceFilter = ref(route.query.price || '')
const page = ref(1)

function doSearch() {
  const kw = keyword.value.trim()
  if (kw || searchTags.value || priceFilter.value) {
    const q = {}
    if (kw) q.keyword = kw
    if (searchTags.value) q.tags = searchTags.value
    if (priceFilter.value) q.price = priceFilter.value
    router.replace({ query: q })
    page.value = 1
    const allTags = buildTagString()
    bookStore.search(kw, page.value, 10, allTags)
  }
}

function buildTagString() {
  const tags = []
  if (searchTags.value) tags.push(searchTags.value)
  if (priceFilter.value === 'free') tags.push('免费')
  else if (priceFilter.value === 'paid') tags.push('付费')
  return tags.join(',')
}

function handlePageChange(p) {
  page.value = p
  bookStore.search(keyword.value, p, 10, buildTagString())
}

watch(() => [route.query.keyword, route.query.tags, route.query.price], ([newKw, newTags, newPrice]) => {
  if (newKw !== keyword.value) keyword.value = newKw || ''
  if (newTags !== searchTags.value) searchTags.value = newTags || ''
  if (newPrice !== priceFilter.value) priceFilter.value = newPrice || ''
  page.value = 1
  bookStore.search(keyword.value, 1, 10, buildTagString())
})

onMounted(() => {
  if (keyword.value || searchTags.value || priceFilter.value) {
    bookStore.search(keyword.value, 1, 10, buildTagString())
  }
})
</script>

<style scoped>
.search-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.search-header {
  margin-bottom: 20px;
}
.search-header h2 {
  font-size: 24px;
  color: #2C3E50;
}
.search-info {
  font-size: 14px;
  color: #999;
  margin-top: 4px;
}

.search-input-row {
  margin-bottom: 24px;
  max-width: 600px;
}

.result-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 20px;
}

.pagination {
  margin-top: 30px;
  display: flex;
  justify-content: center;
}

@media (max-width: 768px) {
  .result-grid {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 12px;
  }
}
</style>
