import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import * as echarts from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { useEffect, useRef } from 'react'

echarts.use([LineChart, GridComponent, TooltipComponent, CanvasRenderer])

export interface Point {
  label: string
  value: number
}

/** Display-only chart. Values are rendered as given; no financial totals are computed in the browser. */
export default function TimeSeriesChart({ data, ariaLabel }: { data: Point[]; ariaLabel: string }) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!ref.current) return
    const chart = echarts.init(ref.current)
    chart.setOption({
      grid: { left: 40, right: 16, top: 16, bottom: 28 },
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: data.map((p) => p.label) },
      yAxis: { type: 'value' },
      series: [{ type: 'line', smooth: true, areaStyle: { opacity: 0.1 }, data: data.map((p) => p.value) }],
    })
    const onResize = () => chart.resize()
    window.addEventListener('resize', onResize)
    return () => {
      window.removeEventListener('resize', onResize)
      chart.dispose()
    }
  }, [data])

  return <div ref={ref} role="img" aria-label={ariaLabel} className="h-64 w-full" />
}
