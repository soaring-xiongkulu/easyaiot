import { describe, it, expect } from 'vitest'
import { expandedFromCollapsed, collapsedFromExpanded } from './quickCommandStore'

describe('expandedFromCollapsed', () => {
  it('expands all ids by default when nothing is collapsed', () => {
    const result = expandedFromCollapsed(['a', 'b', '__ungrouped__'], [])
    expect(result).toEqual(new Set(['a', 'b', '__ungrouped__']))
  })

  it('keeps collapsed ids closed and others open', () => {
    const result = expandedFromCollapsed(['a', 'b', 'c'], ['b'])
    expect(result).toEqual(new Set(['a', 'c']))
  })

  it('ignores collapsed ids that no longer exist', () => {
    const result = expandedFromCollapsed(['a'], ['a', 'deleted-group'])
    expect(result).toEqual(new Set())
  })
})

describe('collapsedFromExpanded', () => {
  it('lists every known id that is not expanded', () => {
    const result = collapsedFromExpanded(
      ['a', 'b', 'c', '__ungrouped__'],
      new Set(['a', '__ungrouped__'])
    )
    expect(result).toEqual(['b', 'c'])
  })

  it('collapses everything when nothing is expanded', () => {
    expect(collapsedFromExpanded(['a', 'b'], new Set())).toEqual(['a', 'b'])
  })

  it('ignores expanded ids outside the known set', () => {
    expect(collapsedFromExpanded(['a'], new Set(['a', 'ghost']))).toEqual([])
  })
})
