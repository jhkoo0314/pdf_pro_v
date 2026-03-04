# 가칭 처방추적 프로젝트 초기 기획안

**Project Name:** Prescription Data Flow (PDF)
**목적:** 외부 처방데이터(예: 유비스트) 구매 없이, **자사 도매→약국 출고 데이터**와 **문전약국 전수조사**를 결합해 **담당자 단위 처방실적(금액) 트래킹**과 **실적 주장 검증(Claim Validation)**을 구현하는 내부 운영 로직/데이터 파이프라인 구축

---

## 1) 배경과 문제정의

### 1-1. 현재 문제

* 외부 처방데이터는 비용이 높고, 중소/중견 제약사 입장에서는 지속 구매가 부담.
* 영업 현장에서는 병원 단위 “실처방금액” 주장(클레임)이 반복되며, 본부는 이를 **정량적으로 검증**할 근거가 부족함.
* 병원(특히 의원)은 파편화되어 있어 전수 트래킹 난이도가 높음.

### 1-2. 핵심 인사이트(프로젝트 설계의 전제)

* **약국 출고/입고 ≠ 실처방**(100% 매핑 불가)
  그러나 월/분기 추세 및 규모 측면에서 **“주장 실적이 상식적으로 가능한가”**를 판단하는 검증 장치로는 충분히 유효.
* 종합병원은 문전약국 클러스터가 명확하여 트래킹이 상대적으로 용이.
* 의원은 파편화되어 있으므로 “자동 거리”보다 **현장 전수조사(문전약국 리스트 제출)**가 더 현실적.

---

## 2) 목표와 성공 정의

### 2-1. MVP 목표(1차)

1. **도매→약국 출고 데이터 기반**으로 품목(브랜드)별/영업권역별/담당자별 **분기 KPI(금액)** 산출
2. 의원 구간은 **담당자 전수 제출 문전약국 리스트**를 근거로 매핑(누락 시 실적 없음 공지로 제출 강제)
3. 종합병원–인근의원 간 **품목+영업권역(territory) 단위 쉐어(풀 합산 후 배분)**를 분기 단위로 정산
4. 도매 미포착(출고가 안 잡힘) 케이스에 대해 **“도매명 확인 → 해당 도매에 약국 거래 여부 문의 → 매핑 확정”** 운영 루프 구현

### 2-2. 성공 기준

* **MVP 산출물이 분기 KPI 정산까지 end-to-end로 재현**되고, 예외(쉐어 룰 변경/전분기 연장/미포착 도매 확인)가 시스템적으로 처리되는 상태를 “성공”으로 판정.

---

## 3) 범위 정의

### 3-1. 포함(In Scope)

* 도매→약국 출고 데이터(출고일 기준)
* 문전약국 전수조사 기반 병원↔약국 매핑
* KPI 기준 금액: **출고가(1차 MVP)**
* Raw에는 공급가/출고가/수량/브랜드 등 **모든 단위 보관**
* 쉐어: **품목(브랜드)+영업권역** 단위, **분기 정산**
* 합의 미성립 시: **전분기 룰 자동 연장**
* 복수 의원 담당자 존재 가능: 의원 몫은 **의원 실적 비례로 재배분**

### 3-2. 제외(Out of Scope, MVP 기준)

* “진짜 처방(청구) 기반” 시장점유/경쟁사 비교(외부 데이터 없이는 불가)
* 병원별 정확 처방금액 산출(약국/출고 기반은 proxy)
* 환자/처방전 레벨 데이터(개인정보/규제 이슈 포함)

---

## 4) 사용자(Stakeholders)와 사용 시나리오

### 4-1. 이해관계자

* **본부 영업기획(SFE)**: KPI 산출/정산, 쉐어 룰 관리, 데이터 품질 관리
* **지점/팀 리더**: 분기 성과 리뷰, 담당자간 경계 분쟁 조정
* **MR/담당자**: 문전약국 제출, 미포착 도매 역추적, 실적 근거 확보
* **도매 담당(본부/현장)**: 도매 거래 구조 확인, 누락 루트 보완

### 4-2. 핵심 사용 시나리오

* (시나리오 A) 분기 마감 후 “담당자 KPI 산출” 자동 정산
* (시나리오 B) 담당자 실적 주장(예: “A병원 300만원”) 발생 → 문전약국 출고 흐름으로 **상식적 검증**
* (시나리오 C) 도매 미포착 → 담당자 도매명 파악 → 본부 도매 문의로 루트 확정 → 다음 분기부터 커버리지 향상

---

## 5) 운영 규칙(확정된 Business Rules)

### 5-1. 귀속/기간

* 실적 귀속은 **트래킹 개시 시점부터 적용**, 소급 없음(분쟁 최소화)

### 5-2. KPI 단위

* 최종 KPI는 **금액**
* MVP는 **출고가 기준**
* Raw에는 공급가/출고가 모두 보관(향후 표준화/환산 논의 가능)

### 5-3. 문전약국 인정

* 담당자 제출 리스트는 문전으로 인정(미제출/누락 시 실적 없음 공지)
* 하드 거리 수치 없음
  단, 취합 단계에서 “상식적으로 납득 가능한 근접”만 포함하도록 본부 지도 검증

### 5-4. 쉐어(풀 합산 후 배분)

* 단위: **품목(브랜드) + 영업권역(territory)**
* 정산: **분기**
* 방식:

  * `Pool = (종합병원 담당자 해당 품목 금액 + 인근 의원 담당자들 해당 품목 금액)`
  * `Pool을 본부가 정한 비율로 배분`
* 복수 의원 담당자 시: 의원 몫은 **의원 실적 비례**로 재배분
* 룰은 본부가 매 분기 관리/조정
* 합의 미성립 시: **전분기 룰 자동 연장**

### 5-5. 도매 미포착 처리

* 담당자가 “도매명” 확인 → 본부가 해당 도매에 **약국 거래 여부 문의** → 매핑 확정
  (즉, “말로 인정”이 아니라 “도매 확인”으로 닫음)

---

## 6) 데이터 모델 설계(포트폴리오용 핵심)

아래는 MVP가 돌아가기 위한 최소 테이블(엑셀/DB 공통 구조)이다.

### 6-1. 테이블 목록과 그레인(Grain)

#### (1) `FACT_SHIP_PHARMACY`

* **그레인:** `출고일 × 도매 × 약국 × 품목(브랜드) × 규격(옵션)`
* **주요 컬럼**

  * `ship_date`(출고일), `year_month`, `year_quarter`
  * `wholesaler_id`, `wholesaler_name`
  * `pharmacy_name`, `pharmacy_addr`, `pharmacy_tel`
  * `product_brand`, `sku`(옵션)
  * `qty`, `amount_ship`(출고가), `amount_supply`(공급가)

#### (2) `DIM_PHARMACY_MASTER`

* **그레인:** 약국 1행
* **주요 컬럼**

  * `pharmacy_uid`(내부키), `pharmacy_name`, `addr`, `tel`
  * `account_id`(있으면), `territory_code`(영업권역)
  * `territory_source`(A=수작업, C=마스터)
  * `active_flag`

#### (3) `DIM_HOSPITAL_MASTER`

* **그레인:** 병원 1행
* **주요 컬럼**

  * `hospital_uid`, `hospital_name`, `addr`, `hospital_type`
  * `territory_code`

#### (4) `MAP_FRONT_PHARMACY` (문전약국 매핑)

* **그레인:** `병원×약국` 관계 1행
* **주요 컬럼**

  * `hospital_uid`, `pharmacy_uid`
  * `submitted_by_rep`, `submitted_quarter`
  * `status`(approved/rejected), `hq_map_check_note`

#### (5) `DIM_REP_ASSIGN` (담당자-권역/기간)

* **그레인:** `담당자×권역×기간`
* **주요 컬럼**

  * `rep_id`, `rep_name`, `territory_code`
  * `valid_from`(트래킹 시작점 반영)

#### (6) `RULE_SHARE_QUARTERLY`

* **그레인:** `분기×영업권역×품목`
* **주요 컬럼**

  * `year_quarter`, `territory_code`, `product_brand`
  * 참여자: `rep_ids`(종병 1 + 의원 n)
  * 배분: `ratio_hosp`, `ratio_clinic` 또는 rep별 직접 비율
  * `status`(confirmed/draft), `version`
  * `extend_prev_quarter_flag`

#### (7) `LOG_WHOLESALER_TRACE` (미포착 루트 추적 로그)

* **그레인:** 케이스 1행
* **주요 컬럼**

  * `case_id`, `pharmacy_uid`, `rep_id`, `product_brand`, `claim_amount`
  * `suspected_wholesaler_name`
  * `hq_inquiry_result`(거래 확인 여부), `resolved_flag`, `resolved_date`

---

## 7) 파이프라인(ETL) 흐름

### 7-1. 처리 단계

1. **Raw 생성/수집(가상데이터)**

   * FACT 출고 데이터 생성
   * 병원/약국/담당자/영업권역 마스터 생성
2. **정규화**

   * 약국명/주소/전화 기반으로 `pharmacy_uid` 부여
   * 거래처 ID가 있으면 마스터 우선(C), 없으면 수작업(A)
3. **권역 매핑**

   * `pharmacy_uid → territory_code` 매핑(수작업+마스터 혼합)
4. **집계**

   * 출고일 기준 월/분기 집계
   * 기준: `분기 × 영업권역 × 품목 × rep`
5. **쉐어 룰 적용(분기)**

   * `RULE_SHARE_QUARTERLY` 기준으로 Pool 생성 → 배분
   * 의원 몫은 의원 실적 비례로 재배분
6. **결과 산출**

   * `rep_kpi_quarter`(담당자 분기 KPI)
   * `validation_report`(미매핑/미포착/룰 버전/전분기 연장 적용 리스트)

---

## 8) 분기 KPI 산출 로직(정확히 고정)

### 8-1. 기본 실적(Pre-Share)

* `BaseAmount(rep, quarter, territory, brand) = Σ amount_ship`

  * 출고일이 해당 분기에 속하는 출고를 합산
  * rep 귀속은 `DIM_REP_ASSIGN`의 territory 기준(트래킹 시작 이후만)

### 8-2. 쉐어 룰 적용(Post-Share)

해당 분기/권역/품목에 룰이 있으면:

1. 참여자 집합: `R = {rep_hosp} ∪ {rep_clinic_1..n}`
2. 풀: `Pool = Σ BaseAmount(r in R)`
3. 배분

   * 종병 몫: `Pool * ratio_hosp`
   * 의원 총몫: `Pool * ratio_clinic`
4. 의원 재배분(의원 실적 비례)

   * 의원 i의 가중치: `w_i = BaseAmount(rep_clinic_i) / Σ BaseAmount(rep_clinic_k)`
   * 의원 i 배정: `ClinicShare_i = (Pool * ratio_clinic) * w_i`

### 8-3. 룰 미존재/합의 미성립

* 해당 분기 룰이 없으면:

  * **전분기 룰 자동 연장 플래그**가 활성화되어 있으면 연장 적용
  * 그렇지 않으면 쉐어 없이 Base 유지

---

## 9) 검증/품질관리(Validation) 설계

MVP에서 “정확도”보다 중요한 건 **재현성, 정산 가능성, 분쟁 방지**다.

### 9-1. 필수 검증 리포트 항목

* 미매핑 약국(UID 미부여/territory 미부여)
* 약국 중복 의심(동일 tel + 유사 주소/명칭)
* 쉐어 룰 누락(전분기 연장 적용 여부 포함)
* 룰 version / 변경 이력
* 분기 경계 이상치(출고가 0인데 갑자기 Pool 급증 등)

### 9-2. Claim Validation(주장 검증) — 포트폴리오 가치가 큰 기능

* 담당자 주장 “300만원” 발생 시:

  * 해당 병원 문전약국 클러스터(제출 기반)의 분기 출고가 합과 비교
  * 결과를 PASS/SUSPECT로 분류(FAIL은 MVP에서는 보수적으로 운영)
* 미포착이면 `LOG_WHOLESALER_TRACE` 케이스 생성 → 도매 문의로 확정

---

## 10) 가상 데이터 생성 설계(Python 기반)

**목표:** “현실적인 난이도(파편화/룰 변경/미포착/도매 루트 차이)”가 포함된 synthetic dataset을 만들어, 로직이 실무처럼 동작함을 증명.

### 10-1. 사용 라이브러리(권장)

* `pandas`, `numpy`: 데이터 생성/집계/정산
* `faker`(ko_KR): 약국/병원 이름, 주소, 전화 생성
* `datetime`, `random`
* (선택) `pyarrow`/`parquet`: 저장 포맷
* (선택) `networkx`: 병원-약국 네트워크(문전 클러스터) 구조 생성 시 유용

### 10-2. 생성할 엔터티 규모 예시(포트폴리오 기준 현실감)

* 영업권역(territory): 8~15개
* 담당자(rep): 30~80명
* 종합병원: 20~50개 (문전약국 5~15개 클러스터)
* 의원: 300~1500개 (문전약국 1~3개 중심)
* 약국: 800~4000개
* 도매: 5~20개
* 품목(브랜드): 10~30개

### 10-3. 현실감을 주는 시뮬레이션 요소(중요)

* **계절성/트렌드:** 특정 품목은 분기별 성장/하락 패턴 반영
* **파편화:** 의원은 작은 금액/약국 분산이 많도록 생성
* **미포착 케이스:** 일부 약국은 도매 데이터가 누락되거나 “unknown wholesaler”로 시작 → 로그 통해 다음 분기에 해결되는 시나리오 생성
* **쉐어 룰 변경:** 분기마다 `RULE_SHARE_QUARTERLY` 일부 변경 + 일부는 전분기 연장
* **복수 의원 담당자:** 동일 (품목+권역)에서 의원 reps가 2~5명 참여하는 케이스 생성

### 10-4. synthetic 데이터 산출물(파일)

* `/data/raw/fact_ship_pharmacy.parquet`
* `/data/dim/dim_pharmacy_master.parquet`
* `/data/dim/dim_hospital_master.parquet`
* `/data/map/map_front_pharmacy.parquet`
* `/data/rules/rule_share_quarterly.parquet`
* `/data/log/log_wholesaler_trace.parquet`

---

## 11) 포트폴리오 제출물(가시성 극대화)

### 11-1. GitHub/포트폴리오 구성(권장)

* `README.md`

  * 문제정의 → 목표 → 운영 규칙 → 데이터 모델 → KPI 산출 로직 → 한계/확장
* `docs/`

  * `data_dictionary.md` (컬럼 정의/그레인/키)
  * `business_rules.md` (쉐어 룰/전분기 연장/미포착 SOP)
  * `architecture.md` (ETL 흐름도)
* `notebooks/`

  * `01_generate_synthetic_data.ipynb`
  * `02_build_masters_and_mapping.ipynb`
  * `03_quarter_kpi_with_share.ipynb`
  * `04_validation_and_claim_check.ipynb`
* `src/`

  * `generate_synth.py`, `ingest_merge.py`, `kpi_publish.py`, `validation.py`
* `outputs/`

  * 분기 KPI 결과 CSV/엑셀
  * validation 리포트
  * (선택) 간단 대시보드(표/차트) 이미지

### 11-2. 면접에서 먹히는 “한 문장 가치”

* “외부 처방데이터 없이도, 자사 유통 전수와 문전약국 전수조사로 **분기 정산 가능한 담당자 KPI**를 만들고, 종병-의원 경계 분쟁을 **품목+권역 단위 풀 정산 로직**으로 해결했습니다.”

---

## 12) 리스크와 대응(현실적)

* **주소/약국 식별 불안정:** 내부 UID 부여 + 전화 포함(가능한 최소 식별자)
* **도매 미포착 지속:** 로그 기반 케이스 관리 + 도매 문의 프로세스
* **분기별 룰 변경으로 혼선:** 룰 versioning + 전분기 연장 디폴트 + 변경 이력 리포트
* **출고가 기준의 한계:** MVP는 출고가로 고정하되, Raw에 공급가/출고가 보관해 향후 표준화 논의 가능하게 설계

---

## 13) MVP 이후 확장 로드맵(선택)

* 도매→도매(전출)까지 추적해 커버리지 확대
* 출고가→표준 약가/정책가 환산 모델 도입
* 권역 매핑 자동화(거래처 ID/마스터 우선) 강화
* Claim Validation을 “케이스 관리(티켓)”로 시스템화

---


