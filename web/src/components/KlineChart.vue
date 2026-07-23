<template>
  <div class="kline-wrapper">
    <div class="chart-toolbar">
      <el-radio-group v-model="interval" size="small" @change="loadData">
        <el-radio-button value="15m">15m</el-radio-button>
        <el-radio-button value="1h">1h</el-radio-button>
        <el-radio-button value="1d">日</el-radio-button>
        <el-radio-button value="1w">周</el-radio-button>
      </el-radio-group>
      <span class="symbol-label">{{ symbol }}</span>
    </div>
    <div ref="chartContainer" class="chart-container" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { createChart, type IChartApi, type ISeriesApi, type CandlestickData, type HistogramData, type LineData, ColorType } from 'lightweight-charts'
import { marketAPI } from '@/api/market'

const props = defineProps<{ symbol: string; market?: string }>()

const interval = ref('1d')
const chartContainer = ref<HTMLElement | null>(null)
let chart: IChartApi | null = null
let candleSeries: ISeriesApi<'Candlestick'> | null = null
let volumeSeries: ISeriesApi<'Histogram'> | null = null
let smaSeries: ISeriesApi<'Line'> | null = null

onMounted(() => loadData())

onUnmounted(() => {
  chart?.remove()
})

const loadData = async () => {
  try {
    const res = await marketAPI.getKlines(props.symbol, props.market || 'us_stock', interval.value, '1y')
    const raw = (res as any)?.data || (res as any)
    const data = Array.isArray(raw) ? raw : []
    if (!data.length) return

    const candles: CandlestickData[] = []
    const volumes: HistogramData[] = []
    const smaValues: LineData[] = []

    let sum = 0
    data.forEach((d: any, i: number) => {
      const time = d.Date || d.date || d.time || ''
      const open = Number(d.Open || d.open || 0)
      const high = Number(d.High || d.high || 0)
      const low = Number(d.Low || d.low || 0)
      const close = Number(d.Close || d.close || 0)
      const volume = Number(d.Volume || d.volume || 0)

      if (time) {
        candles.push({ time: String(time).slice(0, 10), open, high, low, close })
        volumes.push({ time: String(time).slice(0, 10), value: volume, color: close >= open ? 'rgba(0,255,0,0.3)' : 'rgba(255,0,0,0.3)' })
        sum += close
        if (i >= 19) {
          if (i >= 20) sum -= Number(data[i - 20].Close || data[i - 20].close || 0)
          smaValues.push({ time: String(time).slice(0, 10), value: sum / 20 })
        }
      }
    })

    initChart(candles, volumes, smaValues)
  } catch (e) {
    console.error('Load kline error:', e)
  }
}

const initChart = (candles: CandlestickData[], volumes: HistogramData[], smaValues: LineData[]) => {
  if (!chartContainer.value) return
  chart?.remove()

  chart = createChart(chartContainer.value, {
    layout: { background: { type: ColorType.Solid, color: '#0d1117' }, textColor: '#c9d1d9' },
    grid: { vertLines: { color: '#21262d' }, horzLines: { color: '#21262d' } },
    width: chartContainer.value.clientWidth,
    height: 400,
  })

  candleSeries = chart.addCandlestickSeries({
    upColor: '#3fb950', downColor: '#da3633',
    borderUpColor: '#3fb950', borderDownColor: '#da3633',
    wickUpColor: '#3fb950', wickDownColor: '#da3633',
  })
  candleSeries.setData(candles)

  volumeSeries = chart.addHistogramSeries({
    priceFormat: { type: 'volume' },
    priceScaleId: 'volume',
  })
  volumeSeries.setData(volumes)
  chart.priceScale('volume').applyOptions({ scaleMargins: { top: 0.85, bottom: 0 } })

  smaSeries = chart.addLineSeries({ color: '#58a6ff', lineWidth: 1 })
  smaSeries.setData(smaValues)

  chart.timeScale().fitContent()
}
</script>

<style scoped>
.kline-wrapper {
  background: #0d1117;
  border: 1px solid #30363d;
  border-radius: 6px;
  overflow: hidden;
}
.chart-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid #30363d;
}
.symbol-label {
  color: #58a6ff;
  font-weight: 600;
  font-size: 14px;
}
.chart-container {
  width: 100%;
  height: 400px;
}
</style>
