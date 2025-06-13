#!/bin/bash

# 암호화폐 전략 분석 자동 업데이트 스크립트
# 매일 한국시간 오전 9시에 실행되도록 cron에 등록

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$REPO_ROOT"

LOG_DIR="$REPO_ROOT/data"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/update.log"
echo "[$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M:%S')] 자동 업데이트 시작" >> "$LOG_FILE"

PYTHON_CMD="${PYTHON:-$(command -v python3)}"
# 필요한 패키지가 없으면 자동으로 설치
"$PYTHON_CMD" -m pip install -r requirements.txt >> "$LOG_FILE" 2>&1
"$PYTHON_CMD" utils/data_processor.py >> "$LOG_FILE" 2>&1

if [ $? -eq 0 ]; then
    echo "[$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M:%S')] 자동 업데이트 성공" >> "$LOG_FILE"
else
    echo "[$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M:%S')] 자동 업데이트 실패" >> "$LOG_FILE"
fi
echo "[$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M:%S')] 자동 업데이트 완료" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
