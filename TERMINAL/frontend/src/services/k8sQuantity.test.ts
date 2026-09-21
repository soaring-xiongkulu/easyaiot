import { describe, it, expect } from 'vitest'
import { parseCpu, parseMemory, formatCpu, formatMemory, percent } from './k8sQuantity'

describe('k8sQuantity', () => {
  it('parseCpu handles cores, milli, nano', () => {
    expect(parseCpu('1')).toBe(1000)
    expect(parseCpu('500m')).toBe(500)
    expect(parseCpu('1500000000n')).toBe(1500)
    expect(parseCpu('')).toBe(0)
  })
  it('parseMemory handles Ki/Mi/Gi and plain bytes', () => {
    expect(parseMemory('1Ki')).toBe(1024)
    expect(parseMemory('1Mi')).toBe(1024 * 1024)
    expect(parseMemory('2Gi')).toBe(2 * 1024 * 1024 * 1024)
    expect(parseMemory('1000')).toBe(1000)
    expect(parseMemory('')).toBe(0)
  })
  it('formatCpu shows m under a core, cores above', () => {
    expect(formatCpu(12)).toBe('12m')
    expect(formatCpu(1500)).toBe('1.5')
  })
  it('formatMemory picks the largest sensible unit', () => {
    expect(formatMemory(45 * 1024 * 1024)).toBe('45Mi')
    expect(formatMemory(2 * 1024 * 1024 * 1024)).toBe('2Gi')
  })
  it('percent guards divide-by-zero', () => {
    expect(percent(37, 100)).toBe('37%')
    expect(percent(5, 0)).toBe('—')
  })
})
