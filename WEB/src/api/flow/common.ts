import { defHttp } from '@/utils/http/axios'

/** 流程分类 */
export interface FlowCategoryVO {
  id?: string
  name: string
  code: string
  status: number
  sort?: number
  description?: string
}

export function getCategoryPage(params: PageParam & { name?: string; code?: string; status?: number }) {
  return defHttp.get({ url: '/flow/category/page', params })
}

export function getCategorySimpleList() {
  return defHttp.get({ url: '/flow/category/simple-list' })
}

export function getCategory(id: string) {
  return defHttp.get({ url: `/flow/category/get?id=${id}` })
}

export function createCategory(data: FlowCategoryVO) {
  return defHttp.post({ url: '/flow/category/create', data })
}

export function updateCategory(data: FlowCategoryVO) {
  return defHttp.put({ url: '/flow/category/update', data })
}

export function deleteCategory(id: string) {
  return defHttp.delete({ url: `/flow/category/delete?id=${id}` })
}

/** 审批用户组（候选人策略用） */
export interface FlowUserGroupVO {
  id?: number
  name: string
  description?: string
  memberUserIds: number[]
  status?: number
}

export function getUserGroupPage(params: PageParam & { name?: string; status?: number }) {
  return defHttp.get({ url: '/flow/user-group/page', params })
}

export function getUserGroupSimpleList() {
  return defHttp.get({ url: '/flow/user-group/simple-list' })
}

export function getUserGroup(id: number) {
  return defHttp.get({ url: `/flow/user-group/get?id=${id}` })
}

export function createUserGroup(data: FlowUserGroupVO) {
  return defHttp.post({ url: '/flow/user-group/create', data })
}

export function updateUserGroup(data: FlowUserGroupVO) {
  return defHttp.put({ url: '/flow/user-group/update', data })
}

export function deleteUserGroup(id: number) {
  return defHttp.delete({ url: `/flow/user-group/delete?id=${id}` })
}
