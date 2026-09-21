import { describe, it, expect } from 'vitest'
import { parsePodMetricsList, parseNodeMetricsList } from './k8sMetrics'

describe('k8sMetrics parsing', () => {
  it('sums container usage per pod, keyed ns/name', () => {
    const raw = { items: [
      { metadata: { name: 'p1', namespace: 'default' },
        containers: [{ usage: { cpu: '100m', memory: '10Mi' } }, { usage: { cpu: '200m', memory: '20Mi' } }] },
    ]}
    const m = parsePodMetricsList(raw)
    expect(m.get('default/p1')).toEqual({ cpu: 300, mem: 30 * 1024 * 1024 })
  })
  it('reads node usage keyed by name', () => {
    const raw = { items: [{ metadata: { name: 'n1' }, usage: { cpu: '500m', memory: '1Gi' } }] }
    const m = parseNodeMetricsList(raw)
    expect(m.get('n1')).toEqual({ cpu: 500, mem: 1024 ** 3 })
  })
})
