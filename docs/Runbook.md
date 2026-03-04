# Runbook — Prescription Data Flow (MVP)

## 0) 실행 환경 고정(Conda)
1. `conda activate pdf-pro`
2. 인터프리터 확인:
   - `python -V`
   - `where python`
   - `python -m pip -V`
3. `conda` 명령이 잡히지 않으면:
   - `C:\ProgramData\Anaconda3\Scripts\conda.exe run -n base python -V`
4. 패키지 설치/업데이트는 항상 `python -m pip ...` 형태 사용

## 1) 분기 운영 절차(본부)
1. 출고 raw 적재(출고일 기준)
2. 마스터링:
   - pharmacy_uid 부여
   - territory_code 부여(거래처ID 우선, 없으면 수작업)
3. 룰 관리:
   - RULE_SHARE_QUARTERLY 확정(version, status=confirmed)
   - 룰 누락 구간은 전분기 연장 디폴트 적용
4. 정산 실행:
   - Pre-share 산출 → 쉐어 적용(Post-share) → rep_kpi_quarter 생성
5. 검증/리포트:
   - validation_report 생성
   - 전분기 연장 적용 목록 및 룰 버전 확인
6. 배포:
   - Streamlit 갱신 또는 outputs 파일 배포(포트폴리오에서는 outputs 저장)

## 2) 문전약국 취합 절차
1. 담당자 제출(병원별 문전약국: 이름/주소/전화)
2. 본부 취합 및 지도 검증(상식적 근접 여부)
3. 승인 매핑을 MAP_FRONT_PHARMACY 반영
4. 공지: 취합 누락 약국은 실적 산정 제외

## 3) 미포착 케이스 처리
1. Validation에서 UNKNOWN_WHOLESALER 또는 출고 미포착 감지
2. 담당자 도매명 확인(약국 확인)
3. 본부가 도매에 약국 거래 여부 문의
4. LOG 상태 업데이트(Confirmed/Rejected)
5. 다음 분기부터 매핑/커버리지 개선(포트폴리오에서는 시뮬레이션)

## 4) 변경 관리
- 룰은 분기 단위로 변경 가능하나, 반드시 version 증가 및 적용 결과에 버전 기록
- territory 매핑 변경 시 영향 범위를 Validation에 표시(이상치 원인 추적용)

## 5) 월 운영정책 (신규)
### 5.1 운영 원칙
1. 월 운영의 1순위 목적은 처방추적 품질 확보이다.
2. 월 운영은 분기/연간 정산의 선행 품질 게이트로 사용한다.
3. 월 마감 전 미포착 케이스를 최대한 해소하고, 분기 이월 사유를 명시한다.

### 5.2 월간 표준 일정
1. `M+1 ~ M+3 영업일`: 도매 출하 로우 수집/병합, 원천 누락 점검
2. `M+4 ~ M+5 영업일`: mastering(약국 UID/권역) 및 문전약국 등록 변경 반영
3. `M+6 ~ M+7 영업일`: 병원 claim 대비 추적 검증(coverage/gap) 수행
4. `M+8 영업일`: 권역 중첩 구간 사전 쉐어 시뮬레이션 및 draft 룰 점검
5. `M+9 영업일`: 월 KPI 발행 및 validation/trace 보고서 확정

### 5.3 월간 필수 점검 항목
1. 병합 로우 기준 데이터 완전성:
   - 중복 로우/누락 로우/필수 컬럼 누락 여부
2. 추적 품질:
   - 병원별 `coverage_ratio`, `gap_amount`, `gap_ratio`
   - 급증/급감 이상치 목록
3. 룰 품질:
   - `direct/extended/none` 비율
   - `draft` 잔량 및 확정 필요 건수
4. 미포착 운영:
   - `Unverified -> Inquired -> Confirmed/Rejected` 상태 전이 정상 여부
   - 미해결 SLA 경과일 상위 케이스

### 5.4 월간 필수 산출물
1. `data/outputs/rep_kpi_month.*`
2. `data/outputs/kpi_summary_month.*`
3. `data/outputs/validation_report.*`
4. `data/outputs/tracking_report.*`
5. `data/log/log_wholesaler_trace.*` (월 업데이트 반영)

### 5.5 월 -> 분기/연간 연결 규칙
1. 분기 KPI는 월 KPI 누적 기준으로 산출한다.
2. 연간 KPI는 분기 확정분 누적 기준으로 산출한다.
3. 월 미해결 케이스는 분기 마감 시 `이월/종결` 상태를 반드시 표기한다.
4. 전분기 연장 룰 적용 건은 월 리포트부터 사전 경고로 노출한다.

### 5.6 책임자/승인
1. 데이터 운영 담당:
   - 병합/마스터링/검증 실행 및 증적 저장
2. 본부 운영 담당:
   - 룰 확정, 미포착 케이스 승인, 이월 사유 승인
3. 지점/담당자:
   - 문전약국 등록 변경 제출, claim 근거 제출, 미포착 확인 응답
