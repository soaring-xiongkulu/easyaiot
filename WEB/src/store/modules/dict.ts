import { defineStore } from 'pinia'
import type { DictState } from '@/types/store'

import { store } from '@/store'

import { DICT_KEY } from '@/enums/cacheEnum'
import { createLocalStorage } from '@/utils/cache'
import { listSimpleDictData } from '@/api/system/dict/data'
import type { DictDataVO } from '@/api/system/dict/types'

const ls = createLocalStorage()

/** edge/nginx 桩或分页包装后的 simple-list 响应统一转为数组 */
function normalizeSimpleListResponse(res: unknown): DictDataVO[] {
  if (Array.isArray(res))
    return res as DictDataVO[]
  if (!res || typeof res !== 'object')
    return []
  const obj = res as Recordable
  if (Array.isArray(obj.list))
    return obj.list as DictDataVO[]
  if (Array.isArray(obj.data))
    return obj.data as DictDataVO[]
  if (obj.data && typeof obj.data === 'object' && Array.isArray(obj.data.list))
    return obj.data.list as DictDataVO[]
  return []
}

export const useDictStore = defineStore({
  id: 'app-dict',
  state: (): DictState => ({
    dictMap: new Map<string, any>(),
    isSetDict: false,
  }),
  getters: {
    getDictMap(state): Recordable {
      const dictMap = ls.get(DICT_KEY)
      if (dictMap)
        state.dictMap = dictMap

      return state.dictMap
    },
    getIsSetDict(state): boolean {
      return state.isSetDict
    },
  },
  actions: {
    async setDictMap() {
      const dictMap = ls.get(DICT_KEY)
      if (dictMap) {
        this.dictMap = dictMap
        this.isSetDict = true
      }
      else {
        const res = await listSimpleDictData()
        const dictList = normalizeSimpleListResponse(res)
        // 设置数据
        const dictDataMap = new Map<string, any>()
        dictList.forEach((dictData: DictDataVO) => {
          // 获得 dictType 层级
          const enumValueObj = dictDataMap[dictData.dictType]
          if (!enumValueObj)
            dictDataMap[dictData.dictType] = []

          // 处理 dictValue 层级
          dictDataMap[dictData.dictType].push({
            value: dictData.value,
            label: dictData.label,
            colorType: dictData.colorType,
            cssClass: dictData.cssClass,
          })
        })
        this.dictMap = dictDataMap
        this.isSetDict = true
        ls.set(DICT_KEY, dictDataMap, 60) // 60 秒 过期
      }
    },
  },
})

// Need to be used outside the setup
export function useDictStoreWithOut() {
  return useDictStore(store)
}
