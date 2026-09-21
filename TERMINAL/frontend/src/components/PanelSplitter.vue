<template>
  <div
    class="panel-splitter"
    :class="direction"
    @mousedown="onMouseDown"
  ></div>
</template>

<script setup lang="ts">
const props = defineProps<{
  direction: 'horizontal' | 'vertical'
}>()

const emit = defineEmits<{
  resize: [delta: number]
}>()

function onMouseDown(e: MouseEvent) {
  e.preventDefault()
  window.dispatchEvent(new CustomEvent('split:resize-start'))
  const direction = props.direction
  const splitter = e.currentTarget as HTMLElement
  const grid = splitter.parentElement
  const gridRect = grid?.getBoundingClientRect()
  const gridSize = direction === 'horizontal' ? (gridRect?.width || 400) : (gridRect?.height || 400)
  let lastPos = direction === 'horizontal' ? e.clientX : e.clientY

  function onMove(ev: MouseEvent) {
    ev.preventDefault()
    const currentPos = direction === 'horizontal' ? ev.clientX : ev.clientY
    const delta = currentPos - lastPos
    lastPos = currentPos
    emit('resize', delta / gridSize)
  }

  function onUp() {
    document.removeEventListener('mousemove', onMove)
    document.removeEventListener('mouseup', onUp)
    window.dispatchEvent(new CustomEvent('split:resize-end'))
  }

  document.addEventListener('mousemove', onMove)
  document.addEventListener('mouseup', onUp)
}
</script>

<style scoped>
.panel-splitter {
  flex-shrink: 0;
  background: var(--border-subtle);
  transition: background 0.15s;
}
.panel-splitter:hover {
  background: var(--accent);
}
.panel-splitter.horizontal {
  width: 0.25rem;
  cursor: col-resize;
}
.panel-splitter.vertical {
  height: 0.25rem;
  cursor: row-resize;
}
</style>
