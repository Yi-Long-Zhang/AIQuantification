<template>
  <div class="kline-wrapper">
    <div class="chart-toolbar">
      <el-radio-group v-model="interval" size="small" @change="loadData">
        <el-radio-button value="15m">15m</el-radio-button>
        <el-radio-button value="1h">1h</el-radio-button>
        <el-radio-button value="1d">日</el-radio-button>
        <el-radio-button value="1w">周</el-radio-button>
      </el-radio-group>
      <div class="toolbar-right">
        <el-switch v-model="showMACD" size="small" active-text="MACD" />
        <el-switch v-model="showRSI" size="small" active-text="RSI" style="margin-left:8px" />
        <span class="symbol-label">{{ symbol }}</span>
      </div>
    </div>
    <div ref="chartContainer" class="chart-container" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import {
  createChart, CrosshairMode,
  type IChartApi, type ISeriesApi,
  type CandlestickData, type HistogramData, type LineData,
  ColorType
} from 'lightweight-charts'
import { marketAPI } from '@/api/market'

const props = defineProps<{ symbol: string; market?: string; livePrice?: number | null }>()

const interval = ref('1d')
const showMACD = ref(true)
const showRSI = ref(false)
const chartContainer = ref<HTMLElement | null>(null)

let chart: IChartApi | null = null
let candleSeries: ISeriesApi<'Candlestick'> | null = null
let volumeSeries: ISeriesApi<'Histogram'> | null = null
let smaSeries: ISeriesApi<'Line'> | null = null
let macdHistogram: ISeriesApi<'Histogram'> | null = null
let macdLineSeries: ISeriesApi<'Line'> | null = null
let macdSignalSeries: ISeriesApi<'Line'> | null = null
let rsiSeries: ISeriesApi<'Line'> | null = null

onMounted(() => loadData())
onUnmounted(() => chart?.remove())

watch(() => props.livePrice, (newPrice) => {
  if (newPrice && candleSeries) {
    try {
      candleSeries.update({ close: newPrice })
    } catch { /* ignore if time not in series */ }
  }
})

watch([showMACD, showRSI], () => loadData())

const loadData = async () => {
  try {
    const res = await marketAPI.getKlines(props.symbol, props.market || 'us_stock', interval.value, '1y')
    const raw = (res as any)?.data || (res as any)
    const data = Array.isArray(raw) ? raw : []
    if (!data.length) return

    const candles: CandlestickData[] = []
    const volumes: HistogramData[] = []
    const smaData: LineData[] = []
    const macd: { time: string; dif: number; dea: number; bar: number }[] = []
    const rsiData: LineData[] = []

    let sum20 = 0; let ema12 = 0; let ema26 = 0; let dea = 0
    const gains: number[] = []; const losses: number[] = []

    data.forEach((d: any, i: number) => {
      const time = String(d.Date || d.date || d.time || '').slice(0, 10)
      const open = Number(d.Open || d.open || 0)
      const high = Number(d.High || d.high || 0)
      const low = Number(d.Low || d.low || 0)
      const close = Number(d.Close || d.close || 0)
      const volume = Number(d.Volume || d.volume || 0)
      if (!time) return

      candles.push({ time, open, high, low, close })
      volumes.push({ time, value: volume, color: close >= open ? 'rgba(0,200,0,0.3)' : 'rgba(200,0,0,0.3)' })

      // SMA20
      sum20 += close
      if (i >= 20) sum20 -= Number(data[i - 20].Close || data[i - 20].close || 0)
      if (i >= 19) smaData.push({ time, value: sum20 / 20 })

      // MACD
      ema12 = i === 0 ? close : close * 2 / 13 + ema12 * 11 / 13
      ema26 = i === 0 ? close : close * 2 / 27 + ema26 * 25 / 27
      const dif = ema12 - ema26
      dea = i === 0 ? dif : dif * 2 / 10 + dea * 8 / 10
      macd.push({ time, dif: Number(dif.toFixed(4)), dea: Number(dea.toFixed(4)), bar: (dif - dea) * 2 })

      // RSI
      const chg = i > 0 ? Number(data[i].Close || data[i].close || 0) - Number(data[i - 1].Close || data[i - 1].close || 0) : 0
      gains.push(chg > 0 ? chg : 0); losses.push(chg < 0 ? -chg : 0)
      if (i >= 14) {
        const avgGain = gains.slice(-14).reduce((a, b) => a + b, 0) / 14
        const avgLoss = losses.slice(-14).reduce((a, b) => a + b, 0) / 14
        const rs = avgLoss === 0 ? 100 : avgGain / avgLoss
        rsiData.push({ time, value: Number((100 - 100 / (1 + rs)).toFixed(2)) })
      }
    })

    buildChart(candles, volumes, smaData, macd, rsiData)
  } catch (e) { console.error('Load kline error:', e) }
}

const buildChart = (
  candles: CandlestickData[], volumes: HistogramData[], smaData: LineData[],
  macdData: { time: string; dif: number; dea: number; bar: number }[], rsiData: LineData[]
) => {
  if (!chartContainer.value) return
  chart?.remove()

  const containerWidth = chartContainer.value.clientWidth
  const mainHeight = 320
  const subHeight = 120
  const hasSub = showMACD.value || showRSI.value
  const totalHeight = mainHeight + (showMACD.value ? subHeight : 0) + (showRSI.value ? subHeight : 0)

  chart = createChart(chartContainer.value, {
    layout: { background: { type: ColorType.Solid, color: '#0d1117' }, textColor: '#c9d1d9' },
    grid: { vertLines: { color: '#21262d' }, horzLines: { color: '#21262d' } },
    crosshair: { mode: CrosshairMode.Normal },
    width: containerWidth,
    height: totalHeight,
  })

  // Main pane — candlestick
  candleSeries = chart.addCandlestickSeries({
    upColor: '#3fb950', downColor: '#da3633',
    borderUpColor: '#3fb950', borderDownColor: '#da3633',
    wickUpColor: '#3fb950', wickDownColor: '#da3633',
    priceScaleId: 'right',
  })
  candleSeries.setData(candles)
  candleSeries.priceScale().applyOptions({ scaleMargins: hasSub ? { top: 0.1, bottom: 0.4 } : { top: 0.1, bottom: 0.2 } })

  // SMA20 overlay
  smaSeries = chart.addLineSeries({ color: '#58a6ff', lineWidth: 1, priceScaleId: 'right' })
  smaSeries.setData(smaData)

  // Volume
  volumeSeries = chart.addHistogramSeries({ priceFormat: { type: 'volume' }, priceScaleId: 'volume' })
  volumeSeries.setData(volumes)
  chart.priceScale('volume').applyOptions({ scaleMargins: { top: hasSub ? 0.85 : 0.75, bottom: 0 } })

  // MACD sub-chart
  if (showMACD.value) {
    const macdPane = chart.addPane({ height: subHeight })
    macdHistogram = chart.addHistogramSeries({
      priceScaleId: 'macd', pane: macdPane,
    })
    macdHistogram.setData(macdData.map(d => ({
      time: d.time,
      value: d.bar,
      color: d.bar >= 0 ? 'rgba(63,185,80,0.5)' : 'rgba(218,54,51,0.5)',
    })))
    macdLineSeries = chart.addLineSeries({ color: '#d2a943', lineWidth: 1, priceScaleId: 'macd', pane: macdPane })
    macdLineSeries.setData(macdData.map(d => ({ time: d.time, value: d.dif })))
    macdSignalSeries = chart.addLineSeries({ color: '#58a6ff', lineWidth: 1, priceScaleId: 'macd', pane: macdPane })
    macdSignalSeries.setData(macdData.map(d => ({ time: d.time, value: d.dea })))
  }

  // RSI sub-chart
  if (showRSI.value) {
    const rsiPane = chart.addPane({ height: subHeight })
    rsiSeries = chart.addLineSeries({ color: '#bc8cff', lineWidth: 1, priceScaleId: 'rsi', pane: rsiPane })
    rsiSeries.setData(rsiData)
    rsiSeries.priceScale().applyOptions({ autoScale: false, min: 0, max: 100 })
    // Draw 30/70 reference lines
    rsiSeries.createPriceLine({ price: 70, color: '#da3633', lineWidth: 1, lineStyle: 2, axisLabelVisible: true, title: '70' })
    rsiSeries.createPriceLine({ price: 30, color: '#3fb950', lineWidth: 1, lineStyle: 2, axisLabelVisible: true, title: '30' })
  }

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
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 4px;
}
.symbol-label {
  color: #58a6ff;
  font-weight: 600;
  font-size: 14px;
  margin-left: 8px;
}
.chart-container {
  width: 100%;
  min-height: 320px;
}
</style>
