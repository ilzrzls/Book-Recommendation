// echarts-wordcloud 本地封装
import * as echarts from 'echarts'

// 手动实现 wordCloud 系列类型注册
// 基于 echarts-wordcloud@2.1.0 核心逻辑简化版
export function registerWordCloud() {
  if (echarts.extensions && echarts.extensions.wordCloud) return

  echarts.registerLayout(function (ecModel, api) {
    ecModel.eachSeriesByType('wordCloud', function (seriesModel) {
      const gridRect = { x: 0, y: 0, width: seriesModel.get('width') || '100%', height: seriesModel.get('height') || '100%' }
      const data = seriesModel.getData()
      const sizeRange = seriesModel.get('sizeRange') || [12, 60]
      const rotationRange = seriesModel.get('rotationRange') || [-90, 90]
      const gridSize = seriesModel.get('gridSize') || 8

      const minVal = Math.min(...data.mapArray(data.getItemModel, d => d.get('value') || 1))
      const maxVal = Math.max(...data.mapArray(data.getItemModel, d => d.get('value') || 1), 1)

      // Simple spiral layout
      const placed = []
      data.each(function (idx) {
        const value = data.getItemModel(idx).get('value') || 1
        const size = sizeRange[0] + (sizeRange[1] - sizeRange[0]) * (value - minVal) / (maxVal - minVal || 1)
        const angle = rotationRange[0] + Math.random() * (rotationRange[1] - rotationRange[0])

        let x, y, attempts = 0
        do {
          const r = Math.sqrt(attempts) * gridSize
          const a = attempts * 0.5
          x = gridRect.width / 2 + r * Math.cos(a) - size * 2
          y = gridRect.height / 2 + r * Math.sin(a)
          attempts++
        } while (attempts < 500 && placed.some(p => Math.abs(p.x - x) < size && Math.abs(p.y - y) < size * 0.8))

        placed.push({ x, y, size })
        data.setItemLayout(idx, {
          x: Math.max(size, Math.min(gridRect.width - size, x)),
          y: Math.max(size, Math.min(gridRect.height - size, y)),
          rotation: (angle * Math.PI) / 180,
          fontSize: size,
        })
      })
    })
  })

  // ECharts v5 uses registerChart which is different from extension
  // For now, we use a fallback: render word cloud manually in the component
  console.log('[wordcloud] Registered layout for wordCloud series type')
}

export default registerWordCloud
