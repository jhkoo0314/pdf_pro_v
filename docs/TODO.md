# TODO.md - Prescription Data Flow 상세 구현계획 (Phase Gate)

기준 문서:
- `AGENTS.md`
- `docs/PRD.md`
- `docs/01_business_rules.md`
- `docs/02_data_dictionary.md`
- `docs/08_rebuild_requirements.md`
- `docs/09_source_column_selection.md`
- `docs/10_rep_branch_generation_plan.md`

작성일: 2026-03-04

## 0. 고정 원칙 (Non-negotiables)
- KPI 금액 기준은 `amount_ship` 고정
- 날짜 기준은 `ship_date` 고정
- 기간 기준은 `year_month`, `year_quarter`, `year` 고정
- 권역 기준은 `territory_code` 고정
- 쉐어 정산 grain은 `year_quarter x territory_code x brand` 고정
- 추적 시작 이전 기간 소급 귀속 금지
- Validation First 순서 고정:
- `generate/ingest -> mastering -> tracking_validation -> share_settlement -> kpi_publish -> validation/trace_log`
- 필수 산출물은 `data/outputs/` 하위로 고정

## 1. Phase 운영 규칙
- 각 Phase는 `구현 -> 테스트 -> 게이트 판정 -> 증적 저장` 순서로 진행
- Phase 종료 시 아래 4개 항목이 모두 충족되어야 다음 Phase 진행
- 필수 테스트 통과율 100%
- 필수 실패 0건
- 필수 산출물 누락 0건
- 문서/코드 용어 불일치 0건

검증 증적 저장 경로:
- `data/outputs/validation_report.*`
- `data/outputs/tracking_report.*`
- `data/outputs/phase_gate_report.md` (신규 권장)

## 1.1 MVP 단계별 적용 정책 (사용자 요청 반영)
핵심 정책:
- [x] 1단계(MVP): 중첩구간 share 케이스를 생성하지 않는다.
- [x] 1단계 목표: 병합파일(`ingest_merge` 결과) 기준으로 해석 가능한 상태를 완성한다.
- [x] 2단계: 중첩구간을 의도적으로 유도하고 share 엔진/정산 검증을 수행한다.
- [ ] 3단계: Streamlit에서 share 값을 직접 조정하고 확정(승인)할 수 있게 한다.

단계별 산출물/기능 기준:
- [x] 1단계: 추적/검증 가능한 병합 해석 리포트 + 기본 KPI
- [x] 2단계: overlap 케이스 포함 `share_rule_source`/재배분 검증
- [ ] 3단계: UI 수동 조정 + 확정 이력(`approved_by`, `approved_at`, `version`) 저장

## 2. Phase 1 - Foundation & Contract
### 2.1 구현 범위
- [x] 디렉토리/모듈 구조 정리 (`src/`, `app/`, `data/`)
- [x] 공통 컬럼/스키마 계약 정의
- [x] `io_utils.py`에 parquet/csv I/O 표준화
- [x] 필수 컬럼 계약 검증기 구현:
- [x] `ship_date`, `year_month`, `year_quarter`, `year`
- [x] `amount_ship`, `amount_supply`, `amount_pre_share`, `amount_post_share`
- [x] `qty`, `brand`, `territory_code`, `pharmacy_uid`
- [x] 감사 컬럼 계약 검증기 구현:
- [x] `share_applied_flag`
- [x] `share_rule_version`
- [x] `share_rule_source`

### 2.2 테스트 항목
- [x] Contract test: 필수 컬럼 존재/타입/nullable
- [x] I/O test: parquet round-trip, csv round-trip
- [x] Naming test: snake_case, canonical column 검사

### 2.3 완료 기준 (Exit Criteria)
- [x] Contract test 100% 통과
- [x] 컬럼 누락 0건
- [x] `U+FFFD` 유입 0건, UTF-8 디코드 실패 0건

## 3. Phase 2 - Ingest & Mastering
### 3.1 구현 범위
- [x] `generate_synth.py` 재현성(seed) 보장
- [x] `ingest_merge.py` 병합 원천 로우 생성
- [x] `mastering.py` 구현:
- [x] 원천 수집 컬럼은 `docs/09_source_column_selection.md` 확정안 준수
- [x] 지점/담당자 생성은 `docs/10_rep_branch_generation_plan.md` 확정안 준수
- [x] 지점 10개, 의원담당자 60명, 종합병원담당자 45명 생성
- [x] `pharmacy_uid` 부여(단일 책임)
- [x] `territory_code` 매핑
- [x] 매핑 품질 플래그 생성

### 3.2 테스트 항목
- [x] Unit: UID 생성 규칙, territory 매핑 규칙
- [x] Integration: `generate/ingest -> mastering`
- [x] Regression: 동일 seed 재실행 시 본문 동일성

### 3.3 완료 기준 (Exit Criteria)
- [x] `pharmacy_uid` 누락 0건
- [x] `territory_code` 누락 허용 기준 이하(기준은 validation_report에 명시)
- [x] 동일 seed+동일 파라미터 시 데이터 본문 동일
- [x] 지점/담당자 수량 조건 충족(10/60/45)

## 4. Phase 3 - Tracking Validation (핵심)
###  4.1 구현 범위
- [x] `tracking_validation.py` 구현
- [x] 병원 claim vs 출하 추적량 비교
- [x] 지표 산출:
- [x] `tracked_amount`, `tracked_qty`
- [x] `coverage_ratio`
- [x] `gap_amount`, `gap_ratio`
- [x] `tracking_quality_flag`
- [x] `data/outputs/tracking_report.*` 생성

### 4.2 테스트 항목
- [x] Unit: coverage/gap 계산
- [x] Contract: `tracking_report` 필수 컬럼 검사
- [x] Integration: `mastering -> tracking_validation`
- [x] E2E(부분): 정상추적/저커버리지/미추적 케이스

### 4.3 완료 기준 (Exit Criteria)
- [x] `tracking_report.*` 생성 성공
- [x] coverage/gap 계산 오차 허용 범위 내
- [x] 미포착 케이스가 trace 입력 포맷으로 변환 가능

## 5. Phase 4 - Share Settlement
### 5.1 구현 범위
- [x] `share_engine.py` 순수함수 구현/보강
- [x] 정산 로직:
- [x] pool 합산 후 비율 배분
- [x] 복수 의원 rep 재배분(BaseAmount 비례)
- [x] 룰 누락 시 전분기 연장(`extended`)
- [x] 소스 판정 `direct`/`extended`/`none`
- [x] 감사 컬럼 기록:
- [x] `share_applied_flag`
- [x] `share_rule_version`
- [x] `share_rule_source`
- [x] 단계 적용:
- [x] 1단계에서는 overlap 생성 OFF(정산은 단순 케이스 기준)
- [ ] 2단계에서 overlap 생성 ON(중첩 유도/재배분 검증)

### 5.2 테스트 항목
- [x] Unit: 배분/재배분/룰연장/소스판정
- [x] Regression: 보전성(`sum(amount_pre_share) == sum(amount_post_share)`)
- [x] Edge: 룰 없음, 참여자 불완전, 다중 의원

### 5.3 완료 기준 (Exit Criteria)
- [x] 보전성 위배 0건
- [x] 룰 소스 판정 오분류 0건
- [x] 전분기 연장 로직 케이스 테스트 통과

### 5.4 Phase 2 상세 구현계획 (중첩구간 유도 + Share 고도화)
목표:
- [ ] overlap 케이스를 의도적으로 생성하고, 중첩 정산/재배분/감사 추적을 운영 가능 상태로 만든다.

구현 범위(엔진):
- [ ] `share_engine.py` 2단계 설정 추가:
- [x] `overlap_enabled=True` 시 중첩구간 생성 로직 활성화
- [x] 중첩 참여자 유형(`hosp/clinic/mixed`) 판정 컬럼 추가
- [x] 중첩구간별 `overlap_group_id` 생성
- [x] pool 산출 기준을 `year_quarter x territory_code x brand x overlap_group_id`로 확장
- [x] 복수 의원 재배분 시 라운딩 보정(잔차 보정 1건 귀속) 추가

구현 범위(룰/이력):
- [ ] `share_rules`에 2단계 필드 확장:
- [x] `overlap_mode` (`none/partial/full`)
- [x] `participant_scope` (`hosp_only/clinic_only/mixed`)
- [x] `priority` (중첩 우선순위)
- [ ] 룰 적용 이력 컬럼 추가:
- [x] `rule_match_key`
- [x] `rule_resolution_path` (`direct/extended/overlap_resolved/none`)
- [x] `allocation_rounding_delta`

구현 범위(산출물):
- [x] `share_settlement.*`에 2단계 컬럼 반영
- [x] `share_overlap_audit.*` 신규 생성:
- [x] 중첩구간별 pool, 참여자, 배분전/후, 잔차 보정 내역 기록

테스트 계획(Unit):
- [x] overlap_group_id 생성 규칙(동일 입력 시 동일 결과)
- [x] mixed 참여자 비율 배분 규칙
- [x] 라운딩 보정 후 보전성 유지
- [x] priority 기반 룰 선택 결정성

테스트 계획(Integration):
- [x] `tracking_validation -> share_settlement(phase2)` 파이프라인 검증
- [x] overlap ON/OFF 결과 차이 검증(ON에서만 중첩 컬럼 populated)
- [x] `share_overlap_audit`와 `share_settlement` 키 정합성 검증

테스트 계획(Regression/E2E):
- [x] 동일 seed 재실행 시 overlap 그룹/배분 결과 동일
- [x] 전분기 연장 + 중첩 동시 발생 시 소스판정 일관성 유지
- [x] 분기 경계(예: Q1->Q2)에서 룰 상속/중첩 해소 시나리오 검증

완료 기준(Exit Criteria):
- [x] overlap ON 데이터셋에서 `overlap_group_id` 누락 0건
- [x] `sum(amount_pre_share) == sum(amount_post_share)` 보전성 위배 0건
- [x] `rule_resolution_path` 허용값 외 발생 0건
- [x] `share_overlap_audit.*` 생성 성공 + 키 정합성 오류 0건
- [x] Phase2 marker(`integration/regression/e2e`) 100% 통과

## 6. Phase 5 - KPI Publish
### 6.1 구현 범위
- [x] `kpi_publish.py` 구현/완성
- [x] 월/분기/연 KPI 생성:
- [x] `rep_kpi_month.*`, `rep_kpi_quarter.*`, `rep_kpi_year.*`
- [x] `kpi_summary_month.*`, `kpi_summary_quarter.*`, `kpi_summary_year.*`
- [x] pre/post KPI와 share 필드 연결
- [x] validation 결과와 `data_quality_flag` 연결

### 6.2 테스트 항목
- [x] Contract: 6개 KPI 출력 스키마 검사
- [x] Integration: `share_settlement -> kpi_publish`
- [x] E2E(부분): 기간 필터(month/quarter/year) 합계 일관성

### 6.3 완료 기준 (Exit Criteria)
- [x] KPI 출력 6종 누락 0건
- [x] 기간별 집계 일관성 위배 0건
- [x] `data_quality_flag` 정상 반영

## 7. Phase 6 - Validation & Trace Operation
### 7.1 구현 범위
- [x] `validation.py` 구현/보강
- [x] `trace_log.py` 상태 전이 구현
- [x] 상태 전이: `Unverified -> Inquired -> Confirmed/Rejected`
- [x] validation 실패 사유 구조화 기록
- [x] KPI 발행 가능 + 경고 플래그 정책 구현

### 7.2 테스트 항목
- [x] Unit: 이슈 분류, 상태 전이
- [x] Contract: `validation_report` 필수 컬럼
- [x] Integration: `tracking_validation -> validation -> trace_log`
- [x] Regression: 미포착 복원 루프

### 7.3 완료 기준 (Exit Criteria)
- [x] `validation_report.*` 생성 성공
- [x] trace 상태 전이 로그 생성 성공
- [x] 실패 사유 누락 0건

## 8. Phase 7 - Streamlit Orchestration & Smoke
### 8.1 구현 범위
- [x] `app/streamlit_app.py`는 오케스트레이션만 담당
- [x] 화면 우선순위 구현
- [x] 처방추적 검증
- [x] 중첩구간 쉐어 정산
- [x] 월/분기/연간 KPI 발행
- [x] Validation & Trace 운영
- [ ] 필수 필터 구현:
- [x] `year_month/year_quarter/year`
- [x] `territory_code`, `brand`
- [x] 병원/담당자 추가 필터
- [x] CSV/XLSX 다운로드
- [ ] Share 수동조정/확정 기능(3단계):
- [ ] `ratio_hosp`, `ratio_clinic` 또는 참여자별 비율 편집
- [ ] 확정 시 `version`, `status`, `approved_by`, `approved_at` 저장
- [ ] 확정 전/후 시뮬레이션 비교(preview vs confirmed)

### 8.2 테스트 항목
- [x] Smoke: 주요 페이지 로딩/필터 적용
- [x] Integration: 추적 -> 쉐어 -> KPI 흐름 연결
- [x] UX check: 기준 파일/룰버전/실행시각 표시

### 8.3 완료 기준 (Exit Criteria)
- [x] 주요 경로 smoke 100% 통과
- [x] 추적 -> 쉐어 -> KPI 흐름 UI 검증 성공
- [x] 필수 다운로드 동작 성공
- [ ] 수동 조정 -> 확정 -> KPI 재반영 E2E 검증 성공

## 9. 공통 테스트 전략 (자동화 권장)
권장 marker:
- [ ] `unit`
- [ ] `contract`
- [ ] `integration`
- [ ] `regression`
- [ ] `e2e`
- [ ] `smoke`

권장 실행 순서:
1. [ ] `unit`
2. [ ] `contract`
3. [ ] `integration`
4. [ ] `regression`
5. [ ] `e2e`
6. [ ] `smoke`

권장 게이트 명령 예시:
- [ ] `pytest -m unit`
- [ ] `pytest -m contract`
- [ ] `pytest -m integration`
- [ ] `pytest -m regression`
- [ ] `pytest -m e2e`
- [ ] `pytest -m smoke`

## 10. Phase 게이트 판정표
판정 기준:
- `PASS`: 필수 테스트 100%, 필수 실패 0, 필수 산출물 누락 0
- `CONDITIONAL_PASS`: 비필수 경미 이슈만 존재, 차기 Phase 진입 허용
- `FAIL`: 필수 테스트 실패 또는 필수 산출물 누락

Phase별 판정 체크:
- [ ] Phase 1 Gate
- [ ] Phase 2 Gate
- [ ] Phase 3 Gate
- [ ] Phase 4 Gate
- [ ] Phase 5 Gate
- [ ] Phase 6 Gate
- [ ] Phase 7 Gate

## 11. 최종 완료 기준 (DoD)
- [ ] 한 명령으로 핵심 파이프라인 실행 가능
- [ ] 월/분기/연 KPI + validation + tracking 산출물 생성
- [ ] 쉐어 적용/전분기 연장/복수 의원 재배분 테스트 통과
- [ ] Streamlit에서 추적 -> 쉐어 -> KPI 발행 흐름 검증 가능
- [ ] 문서/코드/화면 용어 완전 일치

## 12. 컬럼 표기 정책 업데이트 (영문+한글 병행)
목표:
- 컬럼이 영어만 존재해도 사용자 화면/문서에서는 항상 영어+한글을 함께 표기한다.

정책:
- [x] Canonical 컬럼명은 영문(snake_case) 유지
- [x] 문서/리포트/UI 라벨은 `영문 컬럼명 (한글명)` 형식으로 표기
- [ ] 데이터 사전에 `column_name_en`, `column_name_ko`, `definition_ko`를 명시
- [x] Streamlit 표/차트는 기본 한글 라벨, 원본 영문 컬럼 토글 제공
- [ ] CSV/XLSX 다운로드는 아래 2종 제공
- [ ] `*_raw` : 영문 원본 컬럼
- [x] `*_label` : 영문+한글 병행 컬럼 헤더

예시 표기:
- [x] `ship_date (출고일)`
- [x] `amount_ship (출고금액)`
- [x] `territory_code (영업권역코드)`
- [x] `coverage_ratio (추적커버리지비율)`

검증 테스트 추가:
- [x] Contract: 라벨 매핑 테이블의 영문/한글 1:1 매핑 검증
- [x] Integration: 출력 리포트에 병행 표기 컬럼 헤더 포함 검증
- [x] Smoke: Streamlit 원본 컬럼 토글 동작 검증








