<template>
  <div class="chart-view" ref="chartRef" :style="{ height: height + 'px' }"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  chartData: { type: Object, required: true },
  height: { type: Number, default: 300 },
})

const chartRef = ref(null)
let chartInstance = null

function initChart() {
  if (!chartRef.value) return
  if (chartInstance) {
    chartInstance.dispose()
  }
  chartInstance = echarts.init(chartRef.value)
  const option = buildOption()
  chartInstance.setOption(option)
}

function buildOption() {
  const data = props.chartData
  const baseOption = {
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    animation: true,
    animationDuration: 500,
  }

  switch (data.type) {
    case 'line':
      return {
        ...baseOption,
        tooltip: { trigger: 'axis' },
        title: data.title ? { text: data.title, left: 'center', textStyle: { fontSize: 14 } } : undefined,
        xAxis: { type: 'category', data: data.categories || data.xAxis || data.labels || [], axisLabel: { rotate: data.rotate || 0 } },
        yAxis: { type: 'value' },
        series: (data.series || [data]).map(s => ({
          type: 'line',
          name: s.name || '',
          data: s.data || s.values || [],
          smooth: s.smooth !== false,
          lineStyle: { width: 2 },
          areaStyle: s.area ? { opacity: 0.1 } : undefined,
          symbol: 'circle',
          symbolSize: 6,
        })),
        legend: data.series?.length > 1 ? { bottom: 0, data: data.series.map(s => s.name) } : undefined,
      }

    case 'bar':
      return {
        ...baseOption,
        title: data.title ? { text: data.title, left: 'center', textStyle: { fontSize: 14 } } : undefined,
        xAxis: { type: 'category', data: data.categories || data.xAxis || data.labels || [], axisLabel: { rotate: data.rotate || 0 } },
        yAxis: { type: 'value' },
        series: (data.series || [data]).map(s => ({
          type: 'bar',
          name: s.name || '',
          data: s.data || s.values || [],
          barMaxWidth: 40,
          itemStyle: { borderRadius: [4, 4, 0, 0] },
        })),
        legend: data.series?.length > 1 ? { bottom: 0, data: data.series.map(s => s.name) } : undefined,
      }

    case 'pie':
      return {
        ...baseOption,
        tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
        title: data.title ? { text: data.title, left: 'center', textStyle: { fontSize: 14 } } : undefined,
        series: [{
          type: 'pie',
          radius: ['0%', '60%'],
          center: ['50%', '55%'],
          data: (data.data || data.series?.[0]?.data || []).map((item, i) => ({
            name: item.name || item.label || item[0] || `По${i+1}`,
            value: item.value || item[1] || item,
          })),
          label: { formatter: '{b}: {d}%' },
          emphasis: {
            itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0,0,0,0.5)' },
          },
        }],
      }

    case 'heatmap':
      return {
        ...baseOption,
        tooltip: { position: 'top', formatter: (p) => `${p.value[0]}, ${p.value[1]}: ${p.value[2]}` },
        xAxis: { type: 'category', data: data.xAxis || data.categories || [], splitArea: { show: true } },
        yAxis: { type: 'category', data: data.yAxis || data.labels || [], splitArea: { show: true } },
        visualMap: { min: data.min || 0, max: data.max || 100, calculable: true, orient: 'horizontal', left: 'center', bottom: '0%' },
        series: [{
          type: 'heatmap',
          data: data.data || [],
          label: { show: data.showLabel },
          emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.5)' } },
        }],
      }

    default:
      return baseOption
  }
}

function handleResize() {
  chartInstance?.resize()
}

watch(() => props.chartData, () => {
  nextTick(() => initChart())
}, { deep: true })

onMounted(() => {
  nextTick(() => {
    initChart()
    window.addEventListener('resize', handleResize)
  })
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
})
</script>

<style scoped>
.chart-view {
  width: 100%;
  min-height: 200px;
}
</style>
