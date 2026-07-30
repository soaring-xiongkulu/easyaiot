import { defHttp } from '@/utils/http/axios'

enum Api {
  Overview = '/transform/overview',
  Cluster = '/transform/cluster/workers',
  Instances = '/transform/cluster/instances',
  Command = '/transform/cluster/command',
  Party = '/transform/party',
  Contract = '/transform/contract',
  Mapping = '/transform/mapping',
  Pipeline = '/transform/pipeline',
  Outbox = '/transform/outbox',
  Dlq = '/transform/dlq',
  Backup = '/transform/backup',
}

/** 统一把后端 R.data / 数组 / 空列表解成数组，避免表格拿到异常结构 */
function asList(res: any): Recordable[] {
  if (!res) return []
  if (Array.isArray(res)) return res
  if (Array.isArray(res.data)) return res.data
  if (Array.isArray(res.list)) return res.list
  return []
}

function asObject(res: any): Recordable {
  if (!res) return {}
  if (Array.isArray(res)) return {}
  if (res.data && typeof res.data === 'object' && !Array.isArray(res.data)) return res.data
  return res
}

export const getTransformOverview = async () => asObject(await defHttp.get({ url: Api.Overview }))
export const getTransformCluster = async () => asObject(await defHttp.get({ url: Api.Cluster }))
export const getTransformInstances = async () => asList(await defHttp.get({ url: Api.Instances }))
export const issueTransformCommand = (data: Recordable) => defHttp.post({ url: Api.Command, data })
export const getTransformCommandAcks = async (commandId: string) =>
  asList(await defHttp.get({ url: `${Api.Command}/${commandId}/acks` }))
export const purgeTransformInstances = async (offlineOnly = true) =>
  asObject(
    await defHttp.post({
      url: `${Api.Instances}/purge`,
      params: { offlineOnly },
    }),
  )
export const removeTransformInstance = (instanceId: string) =>
  defHttp.delete({ url: `${Api.Instances}/${encodeURIComponent(instanceId)}` })

export const getTransformPartyList = async () => asList(await defHttp.get({ url: Api.Party }))
export const createTransformParty = (data: Recordable) => defHttp.post({ url: Api.Party, data })
export const updateTransformParty = (id: string, data: Recordable) =>
  defHttp.put({ url: `${Api.Party}/${id}`, data })
export const deleteTransformParty = (id: string) => defHttp.delete({ url: `${Api.Party}/${id}` })

export const getTransformContractList = async () => asList(await defHttp.get({ url: Api.Contract }))
export const createTransformContract = (data: Recordable) => defHttp.post({ url: Api.Contract, data })
export const updateTransformContract = (id: string, data: Recordable) =>
  defHttp.put({ url: `${Api.Contract}/${id}`, data })
export const deleteTransformContract = (id: string) =>
  defHttp.delete({ url: `${Api.Contract}/${id}` })

export const getTransformMappingList = async () => asList(await defHttp.get({ url: Api.Mapping }))
export const createTransformMapping = (data: Recordable) => defHttp.post({ url: Api.Mapping, data })
export const updateTransformMapping = (id: string, data: Recordable) =>
  defHttp.put({ url: `${Api.Mapping}/${id}`, data })
export const deleteTransformMapping = (id: string) =>
  defHttp.delete({ url: `${Api.Mapping}/${id}` })

export const getTransformPipelineList = async () => asList(await defHttp.get({ url: Api.Pipeline }))
export const createTransformPipeline = (data: Recordable) => defHttp.post({ url: Api.Pipeline, data })
export const updateTransformPipeline = (id: string, data: Recordable) =>
  defHttp.put({ url: `${Api.Pipeline}/${id}`, data })
export const enableTransformPipeline = (id: string, enabled: boolean) =>
  defHttp.post({ url: `${Api.Pipeline}/${id}/enable`, params: { enabled } })
export const deleteTransformPipeline = (id: string) =>
  defHttp.delete({ url: `${Api.Pipeline}/${id}` })

export const getTransformOutboxList = async () => asList(await defHttp.get({ url: Api.Outbox }))
export const replayTransformOutbox = (id: string) =>
  defHttp.post({ url: `${Api.Outbox}/${id}/replay` })

export const getTransformDlqList = async () => asList(await defHttp.get({ url: Api.Dlq }))
export const replayTransformDlq = (id: string) => defHttp.post({ url: `${Api.Dlq}/${id}/replay` })

export const getTransformBackupInfo = async () => asObject(await defHttp.get({ url: Api.Backup }))
