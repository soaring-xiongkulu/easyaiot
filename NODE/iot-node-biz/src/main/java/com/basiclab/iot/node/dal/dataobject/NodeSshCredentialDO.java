package com.basiclab.iot.node.dal.dataobject;

import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.basiclab.iot.common.core.dataobject.BaseDO;
import lombok.*;

import java.time.LocalDateTime;

@TableName("node_ssh_credential")
@KeySequence("node_ssh_credential_id_seq")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class NodeSshCredentialDO extends BaseDO {

    @TableId
    private Long id;

    private Long nodeId;

    private String authType;

    private String username;

    private String credentialEnc;

    private String publicKeyFp;

    private LocalDateTime lastTestAt;

    private Boolean lastTestOk;

}
