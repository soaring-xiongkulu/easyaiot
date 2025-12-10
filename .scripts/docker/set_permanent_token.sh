#!/bin/bash

REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"
REDIS_PASSWORD="${REDIS_PASSWORD:-basiclab@iot975248395}"
REDIS_KEY_PATTERN="oauth2_access_token:*"
FIXED_TOKEN_KEY="oauth2_access_token:9693e7451efe446785b770afa636319d"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  设置永久Token脚本${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if ! command -v redis-cli &> /dev/null; then
    echo -e "${RED}错误: redis-cli 未安装，请先安装 Redis 客户端${NC}"
    exit 1
fi

echo -e "${YELLOW}正在连接Redis...${NC}"
if ! redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" ping &> /dev/null; then
    echo -e "${RED}错误: 无法连接到Redis服务器 (${REDIS_HOST}:${REDIS_PORT})${NC}"
    echo -e "${YELLOW}提示: 如果Redis在Docker容器中，请确保容器正在运行${NC}"
    exit 1
fi
echo -e "${GREEN}Redis连接成功${NC}"
echo ""

echo -e "${YELLOW}正在查找所有token...${NC}"
TOKEN_KEYS=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" --no-auth-warning KEYS "$REDIS_KEY_PATTERN" 2>/dev/null)

if [ -z "$TOKEN_KEYS" ] || [ "$TOKEN_KEYS" == "(empty list or set)" ]; then
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}  未找到任何token${NC}"
    echo -e "${RED}========================================${NC}"
    echo -e "${YELLOW}提示: 需要用户登录后才可以设置永久token${NC}"
    exit 0
fi

TOKEN_KEYS=$(echo "$TOKEN_KEYS" | grep -v '^$')
IFS=$'\n' read -rd '' -a TOKEN_KEY_ARRAY <<< "$TOKEN_KEYS"

echo -e "${GREEN}找到 ${#TOKEN_KEY_ARRAY[@]} 个token${NC}"
echo ""

PERMANENT_TOKEN_KEY=""
PERMANENT_TOKEN_VALUE=""
FIRST_TOKEN_KEY=""
FIRST_TOKEN_VALUE=""
FIXED_TOKEN_VALUE=""

for token_key in "${TOKEN_KEY_ARRAY[@]}"; do
    token_key=$(echo "$token_key" | xargs)
    
    if [ -z "$token_key" ]; then
        continue
    fi
    
    ttl=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" --no-auth-warning TTL "$token_key" 2>/dev/null)
    token_value=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" --no-auth-warning GET "$token_key" 2>/dev/null)
    
    if [ "$token_key" == "$FIXED_TOKEN_KEY" ] && [ -n "$token_value" ]; then
        FIXED_TOKEN_VALUE="$token_value"
    fi
    
    if [ "$ttl" == "-1" ]; then
        PERMANENT_TOKEN_KEY="$token_key"
        PERMANENT_TOKEN_VALUE="$token_value"
        break
    elif [ -z "$FIRST_TOKEN_KEY" ] && [ -n "$token_value" ]; then
        FIRST_TOKEN_KEY="$token_key"
        FIRST_TOKEN_VALUE="$token_value"
    fi
done

if [ -n "$PERMANENT_TOKEN_KEY" ]; then
    actual_token=$(echo "$PERMANENT_TOKEN_KEY" | sed 's/oauth2_access_token://')
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  已找到永久token${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${BLUE}Token Key:${NC} $PERMANENT_TOKEN_KEY"
    echo -e "${BLUE}Token:${NC} $actual_token"
    echo -e "${BLUE}TTL:${NC} -1 (永久)"
    echo ""
    echo -e "${BLUE}Token Value:${NC}"
    if command -v python3 &> /dev/null; then
        echo "$PERMANENT_TOKEN_VALUE" | python3 -m json.tool 2>/dev/null || echo "$PERMANENT_TOKEN_VALUE"
    elif command -v jq &> /dev/null; then
        echo "$PERMANENT_TOKEN_VALUE" | jq '.' 2>/dev/null || echo "$PERMANENT_TOKEN_VALUE"
    else
        echo "$PERMANENT_TOKEN_VALUE"
    fi
    echo ""
    exit 0
fi

if [ -n "$FIXED_TOKEN_VALUE" ]; then
    echo -e "${YELLOW}未找到永久token，正在将固定token设置为永久...${NC}"
    result=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" --no-auth-warning PERSIST "$FIXED_TOKEN_KEY" 2>/dev/null)
    new_ttl=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" --no-auth-warning TTL "$FIXED_TOKEN_KEY" 2>/dev/null)
    
    if [ "$new_ttl" == "-1" ]; then
        actual_token=$(echo "$FIXED_TOKEN_KEY" | sed 's/oauth2_access_token://')
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}  Token已设置为永久不过期${NC}"
        echo -e "${GREEN}========================================${NC}"
        echo ""
        echo -e "${BLUE}Token Key:${NC} $FIXED_TOKEN_KEY"
        echo -e "${BLUE}Token:${NC} $actual_token"
        echo -e "${BLUE}TTL:${NC} -1 (永久)"
        echo ""
        echo -e "${BLUE}Token Value:${NC}"
        if command -v python3 &> /dev/null; then
            echo "$FIXED_TOKEN_VALUE" | python3 -m json.tool 2>/dev/null || echo "$FIXED_TOKEN_VALUE"
        elif command -v jq &> /dev/null; then
            echo "$FIXED_TOKEN_VALUE" | jq '.' 2>/dev/null || echo "$FIXED_TOKEN_VALUE"
        else
            echo "$FIXED_TOKEN_VALUE"
        fi
        echo ""
        exit 0
    else
        echo -e "${RED}错误: 设置永久token失败${NC}"
        exit 1
    fi
fi

if [ -n "$FIRST_TOKEN_KEY" ]; then
    actual_token=$(echo "$FIRST_TOKEN_KEY" | sed 's/oauth2_access_token://')
    echo -e "${YELLOW}未找到永久token和固定token，正在将第一个token设置为永久...${NC}"
    result=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" --no-auth-warning PERSIST "$FIRST_TOKEN_KEY" 2>/dev/null)
    new_ttl=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" --no-auth-warning TTL "$FIRST_TOKEN_KEY" 2>/dev/null)
    
    if [ "$new_ttl" == "-1" ]; then
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}  Token已设置为永久不过期${NC}"
        echo -e "${GREEN}========================================${NC}"
        echo ""
        echo -e "${BLUE}Token Key:${NC} $FIRST_TOKEN_KEY"
        echo -e "${BLUE}Token:${NC} $actual_token"
        echo -e "${BLUE}TTL:${NC} -1 (永久)"
        echo ""
        echo -e "${BLUE}Token Value:${NC}"
        if command -v python3 &> /dev/null; then
            echo "$FIRST_TOKEN_VALUE" | python3 -m json.tool 2>/dev/null || echo "$FIRST_TOKEN_VALUE"
        elif command -v jq &> /dev/null; then
            echo "$FIRST_TOKEN_VALUE" | jq '.' 2>/dev/null || echo "$FIRST_TOKEN_VALUE"
        else
            echo "$FIRST_TOKEN_VALUE"
        fi
        echo ""
        exit 0
    else
        echo -e "${RED}错误: 设置永久token失败${NC}"
        exit 1
    fi
fi

echo -e "${RED}错误: 未找到任何有效的token${NC}"
exit 1
