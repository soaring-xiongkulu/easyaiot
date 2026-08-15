# EasyAIoT IDEA 贡献者工作区（code-server + 六语言开发工具链）
# bash IDEA/install.sh build-workspace
# 对齐：DEVICE 要求 Java 21；WEB 镜像 Node 22；本机参考环境见 docs/dev-languages.md

ARG CODE_SERVER_IMAGE=codercom/code-server:4.96.4

FROM ${CODE_SERVER_IMAGE}

USER root

ENV DEBIAN_FRONTEND=noninteractive \
    IDEA_OPEN_FOLDER=/home/coder/easyaiot \
    JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64 \
    DOTNET_ROOT=/usr/share/dotnet \
    PATH=/usr/lib/jvm/java-21-openjdk-amd64/bin:/usr/share/dotnet:${PATH} \
    EXTENSIONS_GALLERY='{"serviceUrl":"https://marketplace.visualstudio.com/_apis/public/gallery","itemUrl":"https://marketplace.visualstudio.com/items","cacheUrl":"https://vscode.blob.core.windows.net/gallery/index"}'

# 基础工具 + 编译器（JDK 用 Temurin 21，对齐 DEVICE / 本机）
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates curl git wget unzip zip jq \
        build-essential cmake pkg-config clangd \
        python3 python3-pip python3-venv \
        maven \
        golang-go \
        docker.io \
    && rm -rf /var/lib/apt/lists/*

# Temurin JDK 21
RUN mkdir -p /usr/lib/jvm \
    && curl -fsSL "https://api.adoptium.net/v3/binary/latest/21/ga/linux/x64/jdk/hotspot/normal/eclipse?project=jdk" \
        -o /tmp/jdk21.tar.gz \
    && tar -xzf /tmp/jdk21.tar.gz -C /usr/lib/jvm \
    && ln -sfn "$(find /usr/lib/jvm -maxdepth 1 -type d -name 'jdk-21*' | head -1)" /usr/lib/jvm/java-21-openjdk-amd64 \
    && rm -f /tmp/jdk21.tar.gz \
    && ln -sfn /usr/lib/jvm/java-21-openjdk-amd64/bin/java /usr/local/bin/java \
    && java -version

# Node.js 22（对齐 WEB Dockerfile / 本机环境）
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && npm install -g pnpm@9 \
    && rm -rf /var/lib/apt/lists/*

# .NET SDK 8（EDGE C#）
RUN curl -fsSL https://dot.net/v1/dotnet-install.sh -o /tmp/dotnet-install.sh \
    && bash /tmp/dotnet-install.sh --channel 8.0 --install-dir /usr/share/dotnet \
    && ln -sfn /usr/share/dotnet/dotnet /usr/local/bin/dotnet \
    && rm -f /tmp/dotnet-install.sh \
    && dotnet --list-sdks || true

# 预装常用扩展（失败不阻断镜像构建；Copilot 走 VS Marketplace）
COPY image/extensions.txt /tmp/extensions.txt
RUN while IFS= read -r ext || [ -n "$ext" ]; do \
      ext="$(echo "$ext" | sed 's/#.*//;s/[[:space:]]//g')"; \
      [ -z "$ext" ] && continue; \
      code-server --install-extension "$ext" || true; \
    done < /tmp/extensions.txt \
    && rm -f /tmp/extensions.txt

COPY image/code-server/User/settings.json /tmp/idea-settings.json
COPY image/entrypoint.sh /usr/local/bin/idea-entrypoint.sh
COPY image/apply-product.sh /tmp/apply-product.sh
COPY image/login/ /tmp/login-ui/
COPY image/browser/ /tmp/idea-browser/
COPY workspace-template/ /opt/idea/workspace-template/

RUN chmod +x /tmp/apply-product.sh /usr/local/bin/idea-entrypoint.sh \
    && LOGIN_SRC=/tmp/login-ui BRIDGE_SRC=/tmp/idea-browser/easyaiot-ide-bridge.js /tmp/apply-product.sh \
    && rm -f /tmp/apply-product.sh \
    && rm -rf /tmp/login-ui /tmp/idea-browser \
    && mkdir -p /home/coder/easyaiot /home/coder/project-data \
    && mkdir -p /home/coder/.local/share/code-server/User \
    && cp -f /tmp/idea-settings.json /home/coder/.local/share/code-server/User/settings.json \
    && chown -R coder:coder /home/coder /opt/idea \
    && chown coder:coder /usr/lib/code-server/lib/vscode/product.json 2>/dev/null || true \
    && chmod u+rw /usr/lib/code-server/lib/vscode/product.json 2>/dev/null || true

USER coder
WORKDIR /home/coder

EXPOSE 8080

ENTRYPOINT ["/usr/local/bin/idea-entrypoint.sh"]
