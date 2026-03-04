# 08_rebuild_requirements.md

## 0) 문서 목적
- 본 문서는 `Prescription Data Flow`를 **처방추적 시스템** 관점으로 처음부터 다시 빌드한다고 가정할 때,
  필요한 요구사항과 보완사항을 상세 정의한다.
- 기준 배경:
  - 외부 처방데이터 구매 비용 부담
  - 자사 데이터(도매 출하 + 문전약국 등록 + 병원/담당자 운영정보) 기반 추적체계 필요
- 본 문서는 구현 우선순위를 `정산 중심 대시보드`가 아니라 `추적 중심 운영시스템`으로 재정렬한다.

---

## 1) 제품 재정의 (Rebuild Product Definition)

### 1.1 최상위 목적
- 1순위 목적: **처방추적**
- 2순위 목적: **실적 claim 검증**
- 3순위 목적: **월·분기·연간 정산 및 KPI 발행**

### 1.2 문제정의
- 외부 처방데이터 없이도 내부 운영 의사결정이 가능해야 한다.
- 병원/의원 단위 주장의 타당성을 정량적으로 판단할 수 있어야 한다.
- 미포착/누락 케이스를 단발성 예외처리로 끝내지 않고 다음 분기 품질로 환류해야 한다.

### 1.3 핵심 가치
- 비용절감: 외부 데이터 의존도 축소
- 운영정합: 같은 규칙으로 반복 가능한 추적/검증
- 분쟁예방: 룰/버전/근거 로그 기반 정산
- 품질개선: 미포착 -> 확인 -> 매핑개선의 폐루프

---

## 2) 운영 시나리오 (Must-have Flow)

### 2.1 표준 추적 흐름
1. 도매 출하 로우 병합 (`final merged row`)
2. 문전약국 매핑 (병원/담당자 등록 정보 기준)
3. 병원 단위 추적량 산출
4. 병원 claim(또는 내부 처방추정량) 대비 비교 검증
5. 의원/종병 권역 중첩 구간 쉐어 적용
6. 월·분기·연간 KPI/검증 리포트 발행

### 2.2 핵심 해석 질문
- 병원1이 주장한 실적은 출하 데이터로 설명 가능한가?
- 누락/미포착은 어느 구간(도매/약국/매핑)에서 발생했는가?
- 룰 부재 시 전분기 연장이 적절히 적용되었는가?
- 쉐어 적용 후 총량 보전이 유지되는가?

---

## 3) 데이터 요구사항 (Data Requirements)

### 3.1 기준 Fact 고정
- 기준 테이블: 최종 병합 로우 (`merged shipment fact`)
- 최소 포함 컬럼:
  - `ship_date`, `year_month`, `year_quarter`
  - `wholesaler_id`, `wholesaler_name`
  - `pharmacy_uid`(mastered 이후), `pharmacy_name`
  - `brand`, `qty`, `amount_ship`, `amount_supply`
  - `territory_code`
  - `lineage`(source_file/source_sheet/source_row_id)

### 3.2 문전약국 등록 데이터 요구
- 독립 관리 테이블 필요 (`hospital_front_pharmacy_registry`)
- 필수 필드:
  - `hospital_uid`, `hospital_name`
  - `pharmacy_uid`
  - `rep_id`(등록 담당자), `submitted_quarter`
  - `status`(draft/confirmed/rejected)
  - `valid_from`, `valid_to`
  - `version`, `approved_by`, `approved_at`

### 3.3 추적 검증 데이터 요구
- 병원 claim/추정량 입력 테이블 필요 (`hospital_claim_quarter`)
- 필수 필드:
  - `year_quarter`, `hospital_uid`, `brand`
  - `claimed_amount` 또는 `claimed_qty`
  - `submitted_by_rep_id`, `submitted_at`
  - `claim_basis_note`

### 3.5 주기별 집계 산출 요구
- 주기별 집계 테이블을 분리 운영:
  - `rep_kpi_month` (월 정산)
  - `rep_kpi_quarter` (분기 정산)
  - `rep_kpi_year` (연간 정산)
- 요약 테이블도 동일하게 주기 분리:
  - `kpi_summary_month`
  - `kpi_summary_quarter`
  - `kpi_summary_year`

### 3.4 쉐어/정산 데이터 요구
- 룰 테이블: `rule_share_quarterly`, `rule_share_participant`
- 필수 감사 필드:
  - `status`, `version`
  - `share_rule_source`(`direct`/`extended`/`none`)
  - `share_rule_version`

---

## 4) 엔진/파이프라인 보완사항

### 4.1 단계 재구성
- 권장 파이프라인:
1. `generate_or_ingest`
2. `ingest_merge`
3. `mastering`
4. `tracking_validation` (신규 핵심 단계)
5. `share_settlement`
6. `kpi_publish`
7. `validation_report`

### 4.2 `tracking_validation` 신규 정의
- 목적: 정산 전, 추적 품질을 선검증
- 산출:
  - 병원별 `tracked_amount`, `tracked_qty`
  - `coverage_ratio` (tracked vs claim)
  - `gap_amount`, `gap_ratio`
  - `tracking_quality_flag`

### 4.3 쉐어 발동 조건 명확화
- 쉐어는 모든 케이스가 아니라 아래에서만 발동:
  - 동일 `year_quarter x territory_code x brand`에서
  - 의원/종병 또는 다중 참여자 중첩이 확인된 경우
- 쉐어 미발동 케이스는 사유를 명시:
  - `none_no_overlap`, `none_no_rule`, `none_invalid_participant`

### 4.4 발행 단계 분리
- `kpi_publish`는 마지막 단계로 분리
- 발행 시점 필수 출력:
  - `rep_kpi_month.*`
  - `rep_kpi_quarter.*`
  - `rep_kpi_year.*`
  - `kpi_summary_month.*`
  - `kpi_summary_quarter.*`
  - `kpi_summary_year.*`
  - `validation_report.*`
  - `tracking_report.*` (신규 권장)

---

## 5) KPI/검증 지표 재정의

### 5.1 처방추적 1차 지표 (핵심)
- `tracked_amount` (병원-문전약국 연결로 추적된 출하금액)
- `claim_amount` (병원 claim 금액)
- `coverage_ratio = tracked_amount / claim_amount`
- `gap_amount = claim_amount - tracked_amount`
- `gap_ratio = gap_amount / claim_amount`

### 5.2 정산 2차 지표
- `year_month`, `year_quarter`, `year`
- `amount_pre_share`, `amount_post_share`
- `share_applied_flag`
- `share_rule_source`
- `conservation_gap`

### 5.3 운영 품질 지표
- 미포착 건수/비율
- 미해결 SLA 경과일
- 전분기 연장 적용 비율
- draft 룰 잔량

---

## 6) Streamlit 재설계 요구사항

### 6.1 IA(정보구조) 재배치
1. `처방추적 검증` (메인)
2. `중첩구간 쉐어정산`
3. `최종 KPI 발행`
4. `검증/트레이스 운영`

### 6.2 화면별 필수 기능
- 공통:
  - 전역 필터 (`year_quarter`, `territory_code`, `brand`)
  - 병원/담당자 추가 필터
  - 기준 파일 및 룰 버전 명시
  - CSV/XLSX 다운로드
- 추적검증 화면:
  - 도매 -> 문전약국 -> 병원/담당자 드릴다운
  - 병원별 coverage/gap 랭킹
  - 이상치(급증/급감) 경고
- 쉐어정산 화면:
  - 중첩 구간 목록
  - 적용 룰(버전/출처)과 배분 결과
  - none/direct/extended 사유 표시
- KPI 발행 화면:
  - 발행 전 체크리스트
  - 월/분기/연간 발행 결과 요약
  - 리포트 다운로드

### 6.3 UX 표준
- 금액 단위 통일(천원)
- 한글 라벨 기본, 원본 컬럼 토글 제공
- 의사결정 문구(“무엇을 봐야 하는지”) 카드 상단 고정

---

## 7) 테스트/품질 게이트 보완

### 7.1 우선 테스트
- 단위:
  - 쉐어 배분/재배분
  - 전분기 연장 판정
  - 추적 coverage/gap 계산
- 통합:
  - 병합 -> mastering -> tracking_validation
  - tracking_validation -> share_settlement
- E2E:
  - 정상추적
  - 중첩쉐어
  - 미포착복원

### 7.2 Phase 게이트 재정의
- “화면이 보인다”가 아니라 “운영 판단 가능” 기준으로 통과
- Phase 7 통과 조건 예시:
  - 병원 단위 추적 커버리지 확인 가능
  - 중첩 쉐어 적용 근거 확인 가능
  - 최종 KPI 발행까지 한 흐름으로 점검 가능

---

## 8) 문서/거버넌스 보완

### 8.1 문서 동기화
- `README.md`: 추적 목적/운영 흐름을 맨 앞에 고정
- `PRD.md`: 기능 우선순위를 추적 -> 정산 순서로 고정
- `02_data_dictionary.md`: 추적/claim/registry 테이블 확장 반영
- `Runbook.md`: 월/분기 운영 절차 + 책임주체 + 승인 절차 명시

### 8.2 운영 승인 체계
- 문전약국 등록 승인 플로우 명문화
- 쉐어 룰 변경 승인 플로우(초안/확정/적용일)
- 감사로그(누가/언제/무엇을 변경) 의무화

---

## 9) 재빌드 착수 우선순위 (실행 순서)
1. 제품정의/운영질문 고정 (문서)
2. 데이터모델 확장 (registry/claim/tracking_report)
3. `tracking_validation` 엔진 구현
4. 쉐어 발동 조건/사유 체계화
5. KPI 발행 단계 분리
6. Streamlit IA 재배치 (추적 중심)
7. E2E 회귀셋 고정
8. Phase 게이트 재판정

---

## 10) Definition of Done (Rebuild)
- 처방추적 메인 흐름에서 병원 단위 해석이 가능해야 한다.
- 쉐어는 중첩 구간에서만 발동하고 근거/버전이 노출되어야 한다.
- 월·분기·연간 KPI 발행이 추적검증 결과와 일관돼야 한다.
- 미포착 케이스가 다음 분기 개선 루프로 연결되어야 한다.
- 문서/코드/화면 용어가 동일해야 한다.
