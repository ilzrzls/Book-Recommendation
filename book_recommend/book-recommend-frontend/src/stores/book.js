import { defineStore } from 'pinia'
import { ref } from 'vue'
import { booksAPI } from '../api/books'

export const useBookStore = defineStore('book', () => {
  const feedBooks = ref([])
  const hotBooks = ref([])
  const newBooks = ref([])
  const searchResults = ref([])
  const searchTotal = ref(0)
  const similarBooks = ref([])
  const currentBook = ref(null)
  const loading = ref(false)

  async function fetchFeed() {
    loading.value = true
    try {
      const res = await booksAPI.getFeed()
      if (res.code === 200) {
        feedBooks.value = res.data.items
      }
    } finally {
      loading.value = false
    }
  }

  async function fetchHotBooks() {
    const res = await booksAPI.getHot()
    if (res.code === 200) {
      hotBooks.value = res.data.items
    }
  }

  async function fetchNewBooks() {
    const res = await booksAPI.getNew()
    if (res.code === 200) {
      newBooks.value = res.data.items
    }
  }

  async function fetchBookDetail(id) {
    loading.value = true
    try {
      const res = await booksAPI.getDetail(id)
      if (res.code === 200) {
        currentBook.value = res.data
      }
      return res
    } finally {
      loading.value = false
    }
  }

  async function fetchSimilarBooks(id) {
    const res = await booksAPI.getSimilar(id)
    if (res.code === 200) {
      similarBooks.value = res.data.items
    }
  }

  async function search(keyword, page = 1, size = 10, tags = '') {
    loading.value = true
    try {
      const res = await booksAPI.search(keyword, page, size, tags)
      if (res.code === 200) {
        searchResults.value = res.data.items
        searchTotal.value = res.data.total
      }
      return res
    } finally {
      loading.value = false
    }
  }

  return {
    feedBooks, hotBooks, newBooks, searchResults, searchTotal,
    similarBooks, currentBook, loading,
    fetchFeed, fetchHotBooks, fetchNewBooks, fetchBookDetail, fetchSimilarBooks, search,
  }
})
