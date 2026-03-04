# PRD.md — Prescription Data Flow (가칭: 처방추적 프로젝트)

## 0. 문서 정보
- 제품명: Prescription Data Flow (PDF)
- 문서 버전: v1.0 (MVP 기준)
- 작성 목적: 초기 기획안을 기반으로 **바로 빌드 가능한 요구사항/규칙/화면/데이터/검증 기준**을 고정한다.
- 대상 독자: 영업기획(SFE) / 데이터 분석 / 포트폴리오 리뷰어(면접관)

---

## 1. 제품 개요 (Product Overview)
### 1.1 배경/문제
외부 처방데이터(예: 유비스트 등)는 구매 비용이 높다.  
영업 현장에서는 병원 단위 “실처방 금액” 주장(클레임)이 빈번하고, 본부는 이를 정량적으로 검증할 근거가 부족하다.  
특히 **의원 구간은 파편화**되어 전수 트래킹이 어렵다.

### 1.2 제품 정의 (한 문장)
**자사 도매→약국 출고 데이터 + 문전약국 전수조사**로, **담당자 단위 분기 KPI(금액)**를 산출하고 **종병-의원 경계/분쟁을 품목+영업권역 단위 쉐어 정산**으로 해결하며, **도매 미포착 케이스는 도매 확인으로 루트를 복원**하는 운영형 데이터 파이프라인/대시보드.

### 1.3 핵심 가치
- (운영) 외부 처방데이터 없이도 **정산 가능한 KPI 체계**를 만든다.
- (통제) 담당자 “주장 실적”에 대해 **상식적 가능성 검증(Claim Validation)**을 제공한다.
- (확장) 커버리지/루트가 불완전해도 **미포착→역추적→확정**의 폐루프로 데이터 품질이 개선된다.

---

## 2. 목표와 성공 기준
### 2.1 MVP 목표
1) **도매→약국 출고 데이터**(출고일 기준)로 분기 KPI(금액) 산출  
   - 병원/의원 주소는 실제 원천(`1.병원정보서비스(2025.12.).xlsx`) 사용
   - 약국 주소는 실제 원천(`2.약국정보서비스(2025.12.).xlsx`) 사용
   - 도매 마스터는 실제 원천(`전국의약품도매업소표준데이터.csv`) 사용
   - 담당자/품목/출고금액/쉐어룰은 합성 생성
2) 의원 구간은 **담당자 제출 문전약국 리스트** 기반으로 매핑(누락 시 실적 없음 공지)  
3) 종병-인근의원 간 **쉐어 정산** 구현  
   - 단위: **품목(브랜드) + 영업권역(territory)**
   - 방식: 풀(pool) 합산 후 비율 배분
   - 복수 의원 담당자: 의원 몫은 **의원 실적 비례**로 재배분
   - 정산 주기: **분기**
   - 합의 미성립: **전분기 룰 자동 연장**
   - 룰 관리: **본부가 분기마다 조정**
4) **도매 미포착 처리** 구현  
   - 담당자 도매명 확인 → 본부가 도매에 약국 거래 여부 문의 → 매핑 확정(로그 관리)

### 2.2 성공 기준 (MVP)
- synthetic 데이터로 **end-to-end 파이프라인 실행** 시,
  - 분기 KPI가 생성되고
  - 쉐어 룰/전분기 연장이 적용되며
  - 검증 리포트(누락/미매핑/미포착)가 생성되는 상태를 “성공”으로 판정.

---

## 3. 범위 (Scope)
### 3.1 In Scope (MVP)
- 도매→약국 출고 데이터
- 하이브리드 데이터 전략(실주소/실도매 + 합성 속성)
- KPI 기준: 금액(출고가 기준)
- Raw에는 공급가/출고가/수량/브랜드 등 **모든 단위 저장**
- 문전약국 제출/승인(지도 검증은 운영 규칙으로 반영)
- 쉐어 룰(품목+영업권역, 분기정산, 전분기 연장)
- 미포착 루트(도매 확인 기반) 로그

### 3.2 Out of Scope (MVP)
- 경쟁사/시장점유율(외부 데이터 없이는 불가)
- 병원별 “정확 처방금액” 확정(약국/출고 기반은 proxy)
- 환자/처방전 레벨 데이터(개인정보/규제 이슈)
- 도매→도매(전출) 추적(Phase 2)

---

## 4. 사용자/페르소나 (Personas)
1) 본부 영업기획(SFE)
- KPI 정산, 쉐어 룰 관리, 데이터 품질 관리, 분쟁 조정 근거 제시

2) MR/담당자
- 문전약국 제출, 미포착 도매 역추적, 실적 근거 확보

3) 지점/팀장
- 분기 성과 리뷰, 권역/품목별 실행 우선순위 논의

---

## 5. 핵심 운영 규칙 (Business Rules — 확정)
### 5.1 기간/귀속
- 실적 귀속은 **트래킹 시작 시점부터만 적용**(소급 없음)
- 집계 기준은 **출고일 기준**(월/분기)

### 5.2 KPI 단위
- 최종 KPI는 **금액**
- MVP는 **출고가(amount_ship)** 기준
- Raw에는 **공급가(amount_supply)** 포함(향후 표준화 논의 여지)

### 5.3 문전약국 인정
- 담당자 제출 약국 리스트를 문전으로 인정
- 하드 거리 수치 없음
- 운영 원칙: “취합 단계에서 누락하면 실적 없음”을 공지하여 제출 강제
- 본부는 지도 기반으로 상식적 근접이 아닌 약국은 취합 단계에서 제외

### 5.4 쉐어 정산 (품목+영업권역)
- 단위: `분기 × 영업권역 × 품목(브랜드)`
- 방식: 해당 단위에서 종병+의원 금액을 **합산(pool)** 후 **비율 배분**
- 복수 의원 담당자: 의원 몫은 **의원 실적 비례**로 의원 담당자들에게 배분
- 룰 변경: 분기마다 본부에서 조정 가능
- 합의 미성립: **전분기 룰 자동 연장**
- 지역 정의: “지역”은 행정구역이 아닌 **영업권역(territory_code)**

### 5.5 미포착 도매 처리
- 담당자가 도매명을 확인하면
- 본부가 해당 도매에 **약국 거래 여부** 문의
- 확인 결과를 로그로 남기고 매핑을 확정/보완

---

## 6. 기능 요구사항 (Functional Requirements)

### 6.1 Hybrid Data Generator (포트폴리오용)
**목표:** 실제 주소/실제 도매 원천에 합성 속성을 결합해, 현실적인 난이도(파편화, 룰 변경, 미포착)를 재현한다.

#### FR-01: 엔터티 생성
- 영업권역(territory): 8~15
- 담당자(rep): 30~80
- 도매: 실제 원천 기반(필요 시 5~20 범위 내 합성 보충)
- 품목(브랜드): 10~30
- 종합병원/의원: 실제 원천 주소 기반(`종별코드명`: 의원/병원/종합병원/상급종합병원)
- 약국: 실제 원천 주소 기반(`2.약국정보서비스`)

#### FR-02: 출고 데이터 생성 (도매→약국)
- 단위: `ship_date`, `wholesaler`, `pharmacy`, `brand`, `qty`, `amount_ship`, `amount_supply`
- 특성:
  - 분기별 트렌드/계절성(품목별 성장/하락)
  - 의원 파편화(작은 금액, 분산)
  - 도매는 실제 도매 마스터(`wholesaler_id`)에 연결
  - 미포착 케이스: 일부 약국은 특정 기간 `unknown wholesaler` 또는 출고 누락 상태로 생성

#### FR-03: 쉐어 룰 데이터 생성
- 일부 (분기×권역×품목)에 쉐어 룰 존재
- 일부는 룰 누락 → 전분기 연장 동작 검증
- 복수 의원 담당자 참여 케이스 포함

#### FR-04: 재현성
- 랜덤 시드 고정 옵션 제공
- 동일 시드/파라미터로 동일 결과 생성

---

### 6.2 Data Normalization & Mastering
#### FR-10: 약국 UID 부여
- 입력: 약국명/주소/전화(및 선택적으로 거래처ID)
- 출력: `pharmacy_uid`, `FACT_SHIP_PHARMACY_MASTERED`
- MVP 규칙:
  - 거래처ID가 있으면 우선 매칭(C)
  - 없으면 (약국명+주소+전화) 조합으로 UID 생성(A)
  - 중복 의심은 Validation 리포트로 분리

#### FR-11: 영업권역(territory_code) 매핑
- 우선순위:
  1) 거래처ID 기반 마스터가 있으면 해당 territory_code 사용 (C)
  2) 없으면 제출 주소 기반 수작업 mapping table 사용 (A)

---

### 6.3 KPI Engine (분기 정산)
#### FR-20: Base KPI 산출 (Pre-share)
- `BaseAmount = Σ amount_ship` (출고일이 해당 분기에 속하는 출고 합)
- 입력 Fact는 `FACT_SHIP_PHARMACY_MASTERED` 고정
- 집계 단위: `분기 × territory_code × brand × rep`

#### FR-21: 쉐어 룰 적용 (Post-share)
- 해당 `분기×territory×brand`에 룰이 존재하면:
  - Pool = 참여 rep들의 BaseAmount 합
  - Pool을 비율로 종병 몫/의원 몫 배분
  - 의원 몫은 의원 rep들의 BaseAmount 비례로 재배분

#### FR-22: 룰 누락 처리 (전분기 연장)
- 룰이 없으면:
  - 전분기 룰 존재 시 자동 연장 적용
  - 전분기도 없으면 쉐어 미적용(Base 그대로)

#### FR-23: 룰 버전/이력
- 룰 테이블은 최소한 `quarter`, `version`, `status`, `extend_prev_quarter_flag`를 포함
- 정산 결과에는 “어떤 룰 버전이 적용되었는지” 기록

---

### 6.4 Validation & Monitoring
#### FR-30: Validation Report 생성
필수 항목:
- 미매핑 약국(UID 없음)
- territory 미부여 약국
- 중복 의심 약국(전화 동일 + 주소 유사 등)
- 룰 누락/전분기 연장 적용 목록
- 미포착/unknown wholesaler 케이스 목록
- 이상치: 특정 분기 급증/급감(Top 변화 리스트)

---

### 6.5 Wholesaler Trace Log (미포착 루프)
#### FR-40: 미포착 케이스 생성
- 조건 예: 특정 약국/품목/권역에서 출고가 0 또는 unknown 도매
- 생성: `case_id`, `pharmacy`, `brand`, `rep`, `quarter`, `status(Unverified)`

#### FR-41: 케이스 처리 상태 업데이트
- `Unverified → Inquired → Confirmed/Rejected`
- Confirmed 시: 다음 분기부터 정상 도매로 매핑되도록 데이터/룰 보정(포트폴리오에서는 시뮬레이션)

---

## 7. UI/UX 요구사항 (Streamlit 기준, 무료 배포 고려)
> 목표: “정산 로직이 실제로 돈다”를 보여주는 얇은 UI

### 7.1 페이지 구조
#### UI-01: Executive Summary
- 필터: 분기 선택
- 카드:
  - 총 출고금액(Pre-share)
  - 총 정산금액(Post-share)
  - 쉐어 룰 적용 건수 / 전분기 연장 건수
  - 미포착 케이스(오픈/해결)
- 테이블:
  - Top reps (Post-share)
  - Top territory×brand 변화

#### UI-02: KPI Explorer
- 필터: 분기 / territory / brand / rep
- 출력:
  - Pre vs Post 비교 테이블
  - 참여 룰(적용된 룰 버전, 비율, 참여자)
  - 의원 재배분 상세(복수 의원 rep일 경우)

#### UI-03: Share Rule Manager (MVP는 read-only 가능)
- 분기 선택 → 룰 목록 조회
- 룰 누락 시 “전분기 연장 적용됨” 표시
- (선택) 룰 CSV 업로드/다운로드 (본부 운영 시뮬레이션)

#### UI-04: Validation & Trace
- Validation 리포트 테이블(필터/정렬)
- 미포착 케이스 목록 + 상태(Confirmed/Rejected)
- (선택) 케이스 상태 변경 UI(포트폴리오 데모)

---

## 8. 데이터 모델 (MVP 스키마)
> 저장 포맷: CSV 또는 Parquet 권장

### 8.0 원천 정제 스냅샷
- `REF_PROVIDER_ADDRESS`
  - source_file, source_sheet, source_row_id
  - provider_id, provider_name, provider_type_code, provider_type_name
  - provider_addr, provider_tel, coord_x, coord_y, opened_date
  - addr_norm, tel_norm
- `REF_PHARMACY_ADDRESS`
  - source_file, source_sheet, source_row_id
  - pharmacy_provider_id, pharmacy_name, pharmacy_type_code, pharmacy_type_name
  - pharmacy_addr, pharmacy_tel, pharmacy_coord_x, pharmacy_coord_y, pharmacy_opened_date
  - addr_norm, tel_norm
- `DIM_WHOLESALER_MASTER`
  - wholesaler_id, wholesaler_name, biz_type (`일반종합도매` 필터)
  - wholesaler_addr_road, wholesaler_addr_jibun, wholesaler_tel
  - lat, lon, business_status, active_flag, is_valid_wholesaler
  - as_of_date, provider_org_code, provider_org_name
  - source_file, source_row_id

### 8.1 FACT_SHIP_PHARMACY_RAW
- ship_date (date)
- year_month (YYYY-MM)
- year_quarter (YYYY-Q)
- wholesaler_id, wholesaler_name
- wholesaler_raw_name (nullable)
- pharmacy_name, pharmacy_addr, pharmacy_tel
- pharmacy_account_id (nullable)
- brand (품목/브랜드)
- qty
- amount_ship (출고가, KPI 기준)
- amount_supply (공급가, 옵션)
- data_source (예: hybrid_simulated)
- is_unknown_wholesaler_case (bool, nullable)

### 8.2 FACT_SHIP_PHARMACY_MASTERED
- ship_date (date)
- year_month (YYYY-MM)
- year_quarter (YYYY-Q)
- wholesaler_id, wholesaler_name
- pharmacy_uid (not null; mastering에서 생성)
- pharmacy_name, pharmacy_addr, pharmacy_tel
- pharmacy_account_id (nullable)
- territory_code, territory_source (nullable)
- brand, qty, amount_ship, amount_supply
- mapping_quality_flag (`C`/`A`/`UNMAPPED`)
- mastering_run_id (nullable)

### 8.3 DIM_PHARMACY_MASTER
- pharmacy_uid (PK)
- pharmacy_name, pharmacy_addr, pharmacy_tel
- pharmacy_account_id (nullable)
- territory_code
- territory_source ('A' manual / 'C' master)
- active_flag
- source_file, source_row_id (nullable)
- addr_norm, tel_norm (optional)

### 8.4 DIM_HOSPITAL_MASTER
- hospital_uid (PK)
- provider_id (nullable)
- hospital_name, hospital_addr, hospital_tel
- hospital_type
- territory_code
- active_flag
- coord_x, coord_y (nullable)
- opened_date (nullable)
- source_file, source_sheet, source_row_id (nullable)

### 8.5 DIM_REP_ASSIGN
- rep_id, rep_name
- territory_code
- valid_from (트래킹 시작)

### 8.6 RULE_SHARE_QUARTERLY
- year_quarter
- territory_code
- brand
- rep_hosp_id
- rep_clinic_ids (list or separate table normalize)
- ratio_hosp (0~1)
- ratio_clinic (1-ratio_hosp)
- version
- status (draft/confirmed)
- extend_prev_quarter_flag (bool)

> 권장: rep_clinic_ids는 별도 테이블로 정규화  
- RULE_SHARE_PARTICIPANT(year_quarter, territory_code, brand, rep_id, role[hosp/clinic])

### 8.7 LOG_WHOLESALER_TRACE
- case_id
- created_quarter
- pharmacy_uid
- rep_id
- brand
- suspected_wholesaler_name
- status (Unverified/Inquired/Confirmed/Rejected)
- note
- resolved_date (nullable)

---

## 9. 비기능 요구사항 (Non-Functional)
- NFR-01: 재현성(동일 시드로 동일 결과)
- NFR-02: 실행 시간(로컬 기준) — synthetic 데이터 10만~50만 row도 수초~수십초 내 처리 목표
- NFR-03: 코드 구조화(모듈 분리), 테스트 가능(핵심 함수 단위)
- NFR-04: 개인정보/환자정보 미사용(공개 기관주소 + 합성 속성만 사용)

---

## 10. 디렉터리/모듈 구조 (권장)

project/
README.md
requirements.txt
docs/
PRD.md
Runbook.md
01_business_rules.md
02_data_dictionary.md
03_data_model_erd.md
04_validation_qa_plan.md
05_synthetic_data_spec.md
06_kpi_output_spec.md
data/
raw/
dim/
rules/
log/
outputs/
src/
config.py
generate_synth.py
mastering.py
kpi_publish.py
share_engine.py
validation.py
trace_log.py
io_utils.py
app/
streamlit_app.py
pages/
01_summary.py
02_kpi_explorer.py
03_share_rules.py
04_validation_trace.py
notebooks/
01_generate.ipynb
02_kpi.ipynb


---

## 11. 수용 기준 (Acceptance Criteria)
### AC-01 End-to-End 실행
- `generate_synth.py` 실행 → raw/staging/rules 생성
- `mastering.py` 실행 → mastered fact + dim_pharmacy 생성
- `kpi_publish.py` 실행 → outputs에 Pre/Post KPI 생성
- `validation.py` 실행 → validation 리포트 생성
- Streamlit에서 분기 선택 시 KPI/룰/검증이 일관되게 표시

### AC-02 쉐어 룰 동작
- 룰이 있는 (quarter×territory×brand)에서:
  - Pool 합산
  - 비율 배분
  - 복수 의원 rep 재배분(의원 실적 비례)
  - 적용 룰 버전 표시

### AC-03 전분기 연장 동작
- 현 분기 룰 누락 시 전분기 룰이 자동 적용되고, UI/리포트에 표시

### AC-04 미포착 로그
- unknown wholesaler 또는 출고 누락이 있는 약국이 Validation에 잡히고
- LOG 케이스가 생성되며
- 케이스 상태 변경(Confirmed) 시 다음 분기 매핑이 개선되는 시뮬레이션이 가능

---

## 12. 리스크 및 대응
- R1: 약국 식별자 부재(명칭/주소 흔들림)
  - 대응: UID 생성 규칙 고정 + 중복 의심 리포트 + (가능하면) 거래처ID 우선 사용
- R2: 룰 분기별 변경으로 혼선
  - 대응: 룰 versioning + 전분기 연장 디폴트 + 룰 적용 리포트
- R3: 출고가 기준 KPI의 해석 한계
  - 대응: MVP는 출고가로 고정하되 raw에 공급가 병행 저장 → Phase 2에서 환산 논의

---

## 13. 로드맵
### Phase 1 (MVP)
- 도매→약국 출고 기반 KPI
- 품목+territory 분기 쉐어 정산
- 전분기 연장
- 미포착 로그/검증 리포트
- Streamlit 데모

### Phase 2 (고도화)
- 도매→도매(전출) 추적 확장
- 금액 표준화(정책가/표준 약가 환산 등) 논의
- 매핑 자동화 강화(거래처ID 커버 확대)

---

## 14. 오픈 이슈 (MVP 이후 논의)
- 출고가 → 표준화 금액(약가/정책가)로 전환 기준
- 지도 검증 프로세스의 문서화(승인/반려 기준)
- 쉐어 룰 변경 이력/승인 워크플로우(권한/감사)

---

## ?? ??? ???? (2026-03-04)
? ????? ?? 4??? ????.

Phase 1 (MVP): ?? ?? ??
- overlap ???(0%)
- `ingest_merge -> mastering -> tracking_validation` ?? ??
- ?? ?? ?? ?? ???? ?? KPI ?? ??

Phase 2: ???? ??/?? ??
- overlap ??(20~30%)
- share ???, ??? ??, ??? ?? ??

Phase 3: Streamlit ?? ??
- share ?? UI?? ?? ?? ? ??
- ?? ??(`approved_by`, `approved_at`, `version`, `status`) ??
- ?? ? KPI ??? ??

Phase 4 (?? ??): ????? ??? ???
- ???? ?? ?? ???? ??
- ??? ???? ???? ?? ??/???/??/??/KPI/validation ??
- ?? ???(`rep_kpi_*`, `kpi_summary_*`, `tracking_report`, `validation_report`) ?? ??
- ?? ??? validation ???? ??? ??
