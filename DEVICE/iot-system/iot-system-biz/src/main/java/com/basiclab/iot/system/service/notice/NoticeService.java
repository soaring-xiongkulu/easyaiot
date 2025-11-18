package com.basiclab.iot.system.service.notice;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.system.controller.admin.notice.vo.NoticePageReqVO;
import com.basiclab.iot.system.controller.admin.notice.vo.NoticeSaveReqVO;
import com.basiclab.iot.system.dal.dataobject.notice.NoticeDO;

/**
 * NoticeService
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public interface NoticeService {

    /**
     * 创建通知公告
     *
     * @param createReqVO 通知公告
     * @return 编号
     */
    Long createNotice(NoticeSaveReqVO createReqVO);

    /**
     * 更新通知公告
     *
     * @param reqVO 通知公告
     */
    void updateNotice(NoticeSaveReqVO reqVO);

    /**
     * 删除通知公告
     *
     * @param id 编号
     */
    void deleteNotice(Long id);

    /**
     * 获得通知公告分页列表
     *
     * @param reqVO 分页条件
     * @return 部门分页列表
     */
    PageResult<NoticeDO> getNoticePage(NoticePageReqVO reqVO);

    /**
     * 获得通知公告
     *
     * @param id 编号
     * @return 通知公告
     */
    NoticeDO getNotice(Long id);

}
