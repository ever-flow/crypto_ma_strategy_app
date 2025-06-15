#!/bin/bash

# Streamlit 앱을 주기적으로 깨워서 슬립 상태를 방지

# 외부에서 APP_URL 환경 변수를 주지 않으면 종료하지 않고 메시지만 출력
timestamp="$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M:%S')"
if [ -z "$APP_URL" ]; then
    echo "[$timestamp] APP_URL not set, skipping wake up"
    exit 0
fi

# 요청이 실패해도 스크립트 전체가 실패하지 않도록 -f 옵션 사용
curl -fs -o /dev/null "$APP_URL" && echo "[$timestamp] Woke $APP_URL"
