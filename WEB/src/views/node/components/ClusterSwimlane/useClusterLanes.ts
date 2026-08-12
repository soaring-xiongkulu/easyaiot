import { computed, ref } from 'vue';
import { getClusterLanes, type ClusterLaneVO } from '@/api/device/node';
import {
  LOCAL_LANE_KEY,
  findLaneByKey,
  readActiveLaneKey,
  writeActiveLaneKey,
} from '../../utils/clusterLanes';

const DEFAULT_LANE_PAGE_SIZE = 100;

export function useClusterLanes() {
  const loading = ref(false);
  const lanes = ref<ClusterLaneVO[]>([]);
  const laneTotal = ref(0);
  const page = ref(1);
  const pageSize = ref(DEFAULT_LANE_PAGE_SIZE);
  const activeLaneKey = ref(readActiveLaneKey());

  const activeLane = computed(() => findLaneByKey(lanes.value, activeLaneKey.value));

  async function loadLanes(nextPage = page.value, nextPageSize = pageSize.value) {
    loading.value = true;
    try {
      const res = await getClusterLanes({ pageNo: nextPage, pageSize: nextPageSize });
      lanes.value = res.data.list;
      laneTotal.value = res.data.total;
      page.value = nextPage;
      pageSize.value = nextPageSize;
      if (!lanes.value.some((lane) => lane.laneKey === activeLaneKey.value)) {
        activeLaneKey.value = lanes.value.find((lane) => lane.isLocal)?.laneKey || LOCAL_LANE_KEY;
        writeActiveLaneKey(activeLaneKey.value);
      }
    } finally {
      loading.value = false;
    }
  }

  function setActiveLane(laneKey: string) {
    activeLaneKey.value = laneKey;
    writeActiveLaneKey(laneKey);
  }

  function changePage(nextPage: number, nextPageSize?: number) {
    return loadLanes(nextPage, nextPageSize ?? pageSize.value);
  }

  return {
    loading,
    lanes,
    laneTotal,
    page,
    pageSize,
    activeLaneKey,
    activeLane,
    loadLanes,
    changePage,
    setActiveLane,
  };
}
