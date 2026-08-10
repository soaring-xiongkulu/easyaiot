package com.basiclab.iot.video.domain.vo;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.util.List;
import java.util.Map;

/** List envelope for snap/record space APIs (includes nullable scope like Python oracle). */
@Data
public class SpaceListApiResponse<T> {

    private int code;
    private String msg;
    private String message;
    private T data;
    private Integer total;
    @JsonProperty("parent_key")
    private String parentKey;
    private List<Map<String, Object>> breadcrumbs;
    @JsonProperty("is_search")
    private Boolean isSearch;
    private String scope;

    public static <T> SpaceListApiResponse<T> success(T data, int total, String parentKey,
            List<Map<String, Object>> breadcrumbs, boolean isSearch, String scope) {
        SpaceListApiResponse<T> response = new SpaceListApiResponse<>();
        response.setCode(0);
        response.setMsg("success");
        response.setMessage("success");
        response.setData(data);
        response.setTotal(total);
        response.setParentKey(parentKey);
        response.setBreadcrumbs(breadcrumbs);
        response.setIsSearch(isSearch);
        response.setScope(scope);
        return response;
    }
}
