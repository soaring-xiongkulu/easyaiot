import { ref } from 'vue'
import { defHttp } from '@/utils/http/axios'
import { CandidateStrategy } from './consts'

/**
 * 候选人选项数据（用户/角色/岗位/部门/用户组），模块级缓存，
 * 设计器与候选人参数控件共用，避免每个弹窗重复拉取。
 */

interface SimpleUser { id: number; nickname: string; avatar?: string; deptId?: number }
interface SimpleRole { id: number; name: string }
interface SimplePost { id: number; name: string }
interface SimpleDept { id: number; name: string; parentId: number }
interface SimpleGroup { id: number; name: string }

const users = ref<SimpleUser[]>([])
const roles = ref<SimpleRole[]>([])
const posts = ref<SimplePost[]>([])
const depts = ref<SimpleDept[]>([])
const userGroups = ref<SimpleGroup[]>([])

let loading: Promise<void> | null = null

function loadUsers() {
  return defHttp.get({ url: '/system/user/list-all-simple' })
}
function loadRoles() {
  return defHttp.get({ url: '/system/role/list-all-simple' })
}
function loadPosts() {
  return defHttp.get({ url: '/system/post/list-all-simple' })
}
function loadDepts() {
  return defHttp.get({ url: '/system/dept/list-all-simple' })
}
function loadUserGroups() {
  return defHttp.get({ url: '/flow/user-group/simple-list' }).catch(() => [])
}

/** 首次调用时并行拉取全部选项，后续调用直接复用 */
export function useCandidateOptions() {
  if (!loading) {
    loading = Promise.all([loadUsers(), loadRoles(), loadPosts(), loadDepts(), loadUserGroups()])
      .then(([u, r, p, d, g]) => {
        users.value = u ?? []
        roles.value = r ?? []
        posts.value = p ?? []
        depts.value = d ?? []
        userGroups.value = g ?? []
      })
      .catch(() => {})
  }
  return { users, roles, posts, depts, userGroups, ready: loading }
}

/** 部门平铺列表 → 树（TreeSelect 用） */
export function buildDeptTree(list: SimpleDept[]): any[] {
  const map = new Map<number, any>()
  list.forEach((item) => {
    map.set(item.id, { id: item.id, title: item.name, value: item.id, key: item.id, parentId: item.parentId, children: [] as any[] })
  })
  const roots: any[] = []
  map.forEach((node) => {
    const parent = node.parentId ? map.get(node.parentId) : null
    if (parent && parent !== node) {
      parent.children.push(node)
    }
    else {
      roots.push(node)
    }
  })
  const prune = (nodes: any[]): any[] => {
    nodes.forEach((node) => {
      if (node.children.length === 0) {
        delete node.children
      }
      else {
        prune(node.children)
      }
    })
    return nodes
  }
  return prune(roots)
}

/** 按 ID 解析名称（展示节点摘要用） */
export function resolveCandidateNames(strategy: CandidateStrategy, ids: string[]): string[] {
  const idNums = ids.map(id => Number(id)).filter(id => !Number.isNaN(id))
  switch (strategy) {
    case CandidateStrategy.USER:
    case CandidateStrategy.START_USER_SELECT:
    case CandidateStrategy.APPROVE_USER_SELECT:
      return idNums.map(id => users.value.find(item => item.id === id)?.nickname ?? `用户${id}`)
    case CandidateStrategy.ROLE:
      return idNums.map(id => roles.value.find(item => item.id === id)?.name ?? `角色${id}`)
    case CandidateStrategy.POST:
      return idNums.map(id => posts.value.find(item => item.id === id)?.name ?? `岗位${id}`)
    case CandidateStrategy.DEPT_MEMBER:
    case CandidateStrategy.DEPT_LEADER:
      return idNums.map(id => depts.value.find(item => item.id === id)?.name ?? `部门${id}`)
    case CandidateStrategy.USER_GROUP:
      return idNums.map(id => userGroups.value.find(item => item.id === id)?.name ?? `用户组${id}`)
    default:
      return []
  }
}
