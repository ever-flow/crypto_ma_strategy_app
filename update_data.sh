#!/bin/bash

# 암호화폐 전략 분석 자동 업데이트 스크립트
# 매일 오전 9시에 실행되도록 cron에 등록

cd /home/ubuntu/crypto_strategy_app

# 로그 파일 설정
LOG_FILE="/home/ubuntu/crypto_strategy_app/update.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$DATE] 자동 업데이트 시작" >> $LOG_FILE

# Python 스크립트 실행
python3 data_processor.py >> $LOG_FILE 2>&1

if [ $? -eq 0 ]; then
    echo "[$DATE] 자동 업데이트 성공" >> $LOG_FILE
else
    echo "[$DATE] 자동 업데이트 실패" >> $LOG_FILE
fi

echo "[$DATE] 자동 업데이트 완료" >> $LOG_FILE
echo "" >> $LOG_FILE

