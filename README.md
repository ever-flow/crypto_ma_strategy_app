# Crypto Strategy App

Streamlit 기반 암호화폐 투자 전략 데모입니다. 비트코인(BTC)과 이더리움(ETH)을 대상으로 최적 이동평균 전략을 계산하여 결과를 시각화합니다.
데이터는 매일 오전 9시(KST) 자동 스케줄러를 통해 갱신됩니다. 앱에서는 갱신된 결과 파일만 읽어오므로 기다림 없이 바로 확인할 수 있습니다.
## 폴더 구조

```
app/          Streamlit 애플리케이션
scripts/      자동 업데이트 및 유지 스크립트
utils/        데이터 처리 및 전략 계산 모듈
data/         업데이트된 결과 및 로그 저장 위치
requirements.txt  필요 패키지 목록
```

## 자동 데이터 업데이트

- `scripts/update_data.sh` : 최신 데이터를 내려받고 결과 파일과 로그를 갱신합니다.
- `scripts/keep_awake.sh` : 배포 후 슬립 상태 방지를 위해 주기적으로 웹 앱 URL을 호출합니다.
- `scripts/crontab_entry.txt` : 로컬 서버에서 사용할 경우 참고할 크론탭 예시입니다.
- `.github/workflows/update_data.yml` : GitHub Actions에서 매일 0:00 UTC(한국시간 9시)에 실행되어 데이터를 자동 업데이트합니다.
- `.github/workflows/keep_awake.yml` : 일정 간격으로 앱을 호출해 슬립을 방지합니다. `STREAMLIT_URL` 시크릿에 배포된 앱 주소를 넣어 사용합니다.
- `data/update.log` : 업데이트 과정의 로그가 누적되는 파일로, 앱에서도 최근 기록을 확인할 수 있습니다.
- 앱 상단의 **🔄 데이터 수동 업데이트** 버튼을 눌러 원하는 시점에 최신 데이터를 다시 받을 수 있습니다.

## 주요 전략

- **BTC/ETH 단독 투자**
- **50:50 리밸런싱**: BTC 50%, ETH 50%
- **60:40 리밸런싱**: BTC 60%, ETH 40%

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
일부 네트워크에서는 야후 파이낸스(YFinance) 접속이 제한될 수 있습니다. 이 경우 자동 업데이트가 실패할 수 있으므로 로컬 환경에서 수동 업데이트 버튼을 활용하세요.
