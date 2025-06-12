# Crypto Strategy App

Streamlit 기반 암호화폐 투자 전략 데모입니다. 비트코인(BTC)과 이더리움(ETH)을 대상으로 최적 이동평균 전략을 계산하여 결과를 시각화합니다.

 main

## 폴더 구조

```
app/          Streamlit 애플리케이션
scripts/      자동 업데이트 및 유지 스크립트
utils/        데이터 처리 및 전략 계산 모듈
data/         업데이트된 결과 및 로그 저장 위치
requirements.txt  필요 패키지 목록
```

## 자동 데이터 업데이트

- `scripts/update_data.sh` : 매일 한국시간(KST) 오전 9시에 실행되어 최신 데이터를 내려받고 `data/strategy_results.json`을 갱신합니다.
- `scripts/keep_awake.sh` : 배포 후 슬립 상태 방지를 위해 주기적으로 웹 앱 URL을 호출합니다.
- `scripts/crontab_entry.txt` : 예시 크론탭 설정입니다. 실제 경로로 수정하여 사용하세요.

## 사용 방법

1. 의존성 설치
   ```bash
   pip install -r requirements.txt
   ```
2. 데이터 수집 및 최적화 실행
   ```bash
   bash scripts/update_data.sh
   ```
3. Streamlit 앱 실행
   ```bash
   streamlit run app/app.py
   ```

## 주의사항

본 프로젝트는 교육용 예제로, 투자 의사결정에 대한 책임은 사용자에게 있습니다.
