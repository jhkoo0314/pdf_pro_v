"""Streamlit orchestration app for MVP Stage 1 (no overlap generation)."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
import re
import sys

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.generate_synth import build_dimensions, save_dimensions
from src.ingest_merge import run_ingest_merge
from src.kpi_publish import run_kpi_publish
from src.mastering import run_mastering
from src.share_engine import run_share_settlement
from src.trace_log import run_trace_log
from src.tracking_validation import run_tracking_validation
from src.validation import run_validation


RAW_DIR = Path("data/raw")
OUT_DIR = Path("data/outputs")


def _canonical_col(col: str) -> str:
    m = re.match(r"^([a-z0-9_]+)\s\(.+\)$", str(col))
    return m.group(1) if m else str(col)


def _to_canonical_headers(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(columns={c: _canonical_col(c) for c in df.columns})


def _read_label_csv(base_name: str, root: Path = OUT_DIR) -> pd.DataFrame:
    path = root / f"{base_name}_label.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, encoding="utf-8-sig")


def _download_xlsx_bytes(df: pd.DataFrame) -> bytes:
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="data")
    return bio.getvalue()


def _render_downloads(df: pd.DataFrame, base_name: str, key: str) -> None:
    if df.empty:
        return
    csv_bytes = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    xlsx_bytes = _download_xlsx_bytes(df)
    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "CSV 다운로드",
            data=csv_bytes,
            file_name=f"{base_name}.csv",
            mime="text/csv",
            key=f"{key}_csv",
        )
    with c2:
        st.download_button(
            "XLSX 다운로드",
            data=xlsx_bytes,
            file_name=f"{base_name}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"{key}_xlsx",
        )


def _apply_filters(
    df: pd.DataFrame,
    period_mode: str,
    period_values: list[str],
    territory_values: list[str],
    brand_values: list[str],
    pharmacy_values: list[str],
    rep_values: list[str],
) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    canon = {_canonical_col(c): c for c in out.columns}

    period_col = {"month": "year_month", "quarter": "year_quarter", "year": "year"}[period_mode]
    if period_values and period_col in canon:
        out = out[out[canon[period_col]].astype(str).isin(period_values)]
    if territory_values and "territory_code" in canon:
        out = out[out[canon["territory_code"]].astype(str).isin(territory_values)]
    if brand_values and "brand" in canon:
        out = out[out[canon["brand"]].astype(str).isin(brand_values)]
    if pharmacy_values and "pharmacy_name" in canon:
        out = out[out[canon["pharmacy_name"]].astype(str).isin(pharmacy_values)]
    if rep_values and "rep_name" in canon:
        out = out[out[canon["rep_name"]].astype(str).isin(rep_values)]
    return out


def _amount_to_thousand(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    # Display-only conversion: keep raw/output files untouched, show money fields in thousand KRW.
    money_cols = {
        "amount_ship",
        "amount_supply",
        "amount_pre_share",
        "amount_post_share",
        "amount_hosp_share",
        "amount_clinic_share",
        "claim_amount",
        "tracked_amount",
        "gap_amount",
        "total_pre_share",
        "total_post_share",
        "list_price_per_pack",
        "net_price_per_pack",
        "price_per_unit",
        "price_per_pack",
    }
    for c in out.columns:
        cc = _canonical_col(c)
        if cc in money_cols:
            vals = pd.to_numeric(out[c], errors="coerce") / 1000.0
            out[c] = vals.round(0).astype("Int64")
    return out


def _run_mvp1_pipeline(seed: int, min_coverage: float) -> None:
    dims = build_dimensions(seed=seed, valid_from="2026-01-01")
    save_dimensions(dims, output_dir=RAW_DIR, fmt="parquet")
    run_ingest_merge(raw_dir=RAW_DIR, output_dir=RAW_DIR, seed=seed)
    run_mastering(raw_dir=RAW_DIR, output_dir=OUT_DIR, seed=seed, territory_missing_threshold=0.05)
    run_tracking_validation(input_dir=OUT_DIR, output_dir=OUT_DIR, min_coverage=min_coverage)
    # MVP stage 1: share overlap generation remains OFF in share_engine default config.
    run_share_settlement(input_dir=OUT_DIR, output_dir=OUT_DIR)
    run_kpi_publish(input_dir=OUT_DIR, output_dir=OUT_DIR)
    run_validation(input_dir=OUT_DIR, output_dir=OUT_DIR)
    run_trace_log(input_dir=OUT_DIR, output_dir=OUT_DIR)


def _meta_caption() -> str:
    rule_df = _read_label_csv("share_rules")
    version_col = next((c for c in rule_df.columns if _canonical_col(c) == "version"), None)
    versions = sorted(rule_df[version_col].dropna().astype(str).unique().tolist()) if version_col else []
    latest = max((p.stat().st_mtime for p in OUT_DIR.glob("*_label.csv")), default=0.0)
    latest_txt = pd.to_datetime(latest, unit="s").strftime("%Y-%m-%d %H:%M:%S") if latest else "N/A"
    return f"기준 파일: data/raw + data/outputs | 룰 버전: {', '.join(versions) if versions else 'N/A'} | 실행시각: {latest_txt}"


def main() -> None:
    st.set_page_config(page_title="Prescription Data Flow MVP1", layout="wide")
    st.title("Prescription Data Flow - MVP 1 오케스트레이션")
    st.caption("MVP 1 정책: overlap 생성 OFF, 병합 해석/추적/정산/KPI 검증 중심")
    st.caption("금액 표기 단위: 천원")
    st.caption(_meta_caption())

    with st.sidebar:
        st.subheader("실행")
        seed = st.number_input("seed", min_value=1, max_value=999999, value=42, step=1)
        min_coverage = st.slider("min_coverage", min_value=0.50, max_value=0.95, value=0.75, step=0.01)
        if st.button("MVP1 전체 파이프라인 실행", use_container_width=True):
            with st.spinner("파이프라인 실행 중..."):
                _run_mvp1_pipeline(seed=int(seed), min_coverage=float(min_coverage))
            st.success("완료: generate/ingest -> mastering -> tracking -> share -> kpi -> validation -> trace")

    tracking_df = _read_label_csv("tracking_report")
    share_df = _read_label_csv("share_settlement")
    master_df = _read_label_csv("fact_ship_pharmacy_mastered")
    rep_kpi_month = _read_label_csv("rep_kpi_month")
    rep_kpi_quarter = _read_label_csv("rep_kpi_quarter")
    rep_kpi_year = _read_label_csv("rep_kpi_year")
    kpi_summary_month = _read_label_csv("kpi_summary_month")
    kpi_summary_quarter = _read_label_csv("kpi_summary_quarter")
    kpi_summary_year = _read_label_csv("kpi_summary_year")
    dim_branch_df = _read_label_csv("dim_branch")
    validation_df = _read_label_csv("validation_report")
    trace_log_df = _read_label_csv("trace_log")
    trace_hist_df = _read_label_csv("trace_history")

    source_for_filters = share_df if not share_df.empty else tracking_df
    canon_cols = {_canonical_col(c): c for c in source_for_filters.columns} if not source_for_filters.empty else {}

    st.sidebar.subheader("전역 필터")
    period_mode = st.sidebar.radio("기간 기준", options=["month", "quarter", "year"], index=1, horizontal=True)
    period_col = {"month": "year_month", "quarter": "year_quarter", "year": "year"}[period_mode]
    period_options = (
        sorted(source_for_filters[canon_cols[period_col]].dropna().astype(str).unique().tolist())
        if period_col in canon_cols
        else []
    )
    period_values = st.sidebar.multiselect("기간", period_options, default=period_options[-1:] if period_options else [])

    # Show branch names in filter UI, but keep internal filtering by territory_code.
    territory_to_branch: dict[str, str] = {}
    if not dim_branch_df.empty:
        bcanon = {_canonical_col(c): c for c in dim_branch_df.columns}
        if "territory_code" in bcanon and "branch_name" in bcanon:
            territory_to_branch = (
                dim_branch_df[[bcanon["territory_code"], bcanon["branch_name"]]]
                .dropna()
                .astype(str)
                .drop_duplicates()
                .set_index(bcanon["territory_code"])[bcanon["branch_name"]]
                .to_dict()
            )

    territory_options = []
    territory_display_to_code: dict[str, str] = {}
    if "territory_code" in canon_cols:
        for code in sorted(source_for_filters[canon_cols["territory_code"]].dropna().astype(str).unique().tolist()):
            branch_name = territory_to_branch.get(code, code)
            territory_options.append(branch_name)
            territory_display_to_code[branch_name] = code

    territory_display_values = st.sidebar.multiselect("권역(지점명)", territory_options, default=[])
    territory_values = [territory_display_to_code[v] for v in territory_display_values if v in territory_display_to_code]

    brand_options = (
        sorted(source_for_filters[canon_cols["brand"]].dropna().astype(str).unique().tolist())
        if "brand" in canon_cols
        else []
    )
    brand_values = st.sidebar.multiselect("브랜드", brand_options, default=[])

    mcanon = {_canonical_col(c): c for c in master_df.columns}
    pharmacy_options = (
        sorted(master_df[mcanon["pharmacy_name"]].dropna().astype(str).unique().tolist())
        if "pharmacy_name" in mcanon
        else []
    )
    pharmacy_values = st.sidebar.multiselect("약국/병원(매핑 기준)", pharmacy_options, default=[])

    rep_source = rep_kpi_quarter if not rep_kpi_quarter.empty else rep_kpi_month
    rcanon = {_canonical_col(c): c for c in rep_source.columns} if not rep_source.empty else {}
    rep_options = (
        sorted(rep_source[rcanon["rep_name"]].dropna().astype(str).unique().tolist())
        if "rep_name" in rcanon
        else []
    )
    rep_values = st.sidebar.multiselect("담당자", rep_options, default=[])

    show_raw_cols = st.sidebar.toggle("원본 컬럼명(영문) 토글", value=False)

    tab1, tab2, tab3, tab4 = st.tabs(
        ["1) 처방추적 검증", "2) 중첩구간 쉐어 정산", "3) 월/분기/연간 KPI 발행", "4) Validation & Trace 운영"]
    )

    with tab1:
        st.subheader("처방추적 검증")
        st.caption("금액 단위: 천원")
        df = _apply_filters(
            tracking_df, period_mode, period_values, territory_values, brand_values, pharmacy_values, rep_values
        )
        if df.empty:
            st.info("표시할 tracking 데이터가 없습니다.")
        else:
            d = _amount_to_thousand(df)
            c = {_canonical_col(col): col for col in d.columns}
            m1, m2, m3 = st.columns(3)
            m1.metric("행 수", f"{len(d):,}")
            m2.metric("평균 coverage_ratio", f"{pd.to_numeric(d[c['coverage_ratio']], errors='coerce').mean():.4f}")
            m3.metric("총 gap_amount (천원)", f"{pd.to_numeric(d[c['gap_amount']], errors='coerce').sum():,.0f}")
            view_df = _to_canonical_headers(d) if show_raw_cols else d
            st.dataframe(view_df, use_container_width=True, height=420)
            _render_downloads(view_df, "tracking_report_view", "trk_view")

    with tab2:
        st.subheader("중첩구간 쉐어 정산")
        st.caption("MVP 1 정책: overlap 생성 OFF 상태의 단순 해석/정산 결과를 확인합니다.")
        st.caption("금액 단위: 천원")
        df = _apply_filters(
            share_df, period_mode, period_values, territory_values, brand_values, pharmacy_values, rep_values
        )
        if df.empty:
            st.info("표시할 share 데이터가 없습니다.")
        else:
            d = _amount_to_thousand(df)
            c = {_canonical_col(col): col for col in d.columns}
            total_pre = pd.to_numeric(d[c["amount_pre_share"]], errors="coerce").sum()
            total_post = pd.to_numeric(d[c["amount_post_share"]], errors="coerce").sum()
            src_counts = d[c["share_rule_source"]].value_counts(dropna=False).to_dict()
            m1, m2, m3 = st.columns(3)
            m1.metric("Pre 합계 (천원)", f"{total_pre:,.0f}")
            m2.metric("Post 합계 (천원)", f"{total_post:,.0f}")
            m3.metric("보전성 차이 (천원)", f"{(total_pre-total_post):,.0f}")
            st.write("룰 소스 분포:", src_counts)
            view_df = _to_canonical_headers(d) if show_raw_cols else d
            st.dataframe(view_df, use_container_width=True, height=420)
            _render_downloads(view_df, "share_settlement_view", "share_view")

    with tab3:
        st.subheader("월/분기/연간 KPI 발행")
        st.caption("금액 단위: 천원")
        period_pick = st.radio("KPI 조회 단위", options=["month", "quarter", "year"], horizontal=True, index=1)
        if st.button("KPI 재발행 실행", use_container_width=True):
            with st.spinner("KPI 발행 중..."):
                run_kpi_publish(input_dir=OUT_DIR, output_dir=OUT_DIR)
            st.success("KPI 재발행 완료")

        rep_map = {"month": rep_kpi_month, "quarter": rep_kpi_quarter, "year": rep_kpi_year}
        sum_map = {"month": kpi_summary_month, "quarter": kpi_summary_quarter, "year": kpi_summary_year}
        rep_df = _apply_filters(
            rep_map[period_pick], period_mode, period_values, territory_values, brand_values, pharmacy_values, rep_values
        )
        sum_df = _apply_filters(
            sum_map[period_pick], period_mode, period_values, territory_values, brand_values, pharmacy_values, rep_values
        )
        if sum_df.empty:
            st.info("표시할 KPI 데이터가 없습니다.")
        else:
            st.markdown("**Summary KPI**")
            sum_view = _to_canonical_headers(_amount_to_thousand(sum_df)) if show_raw_cols else _amount_to_thousand(sum_df)
            st.dataframe(sum_view, use_container_width=True, height=220)
            _render_downloads(sum_view, f"kpi_summary_{period_pick}_view", f"kpi_sum_{period_pick}")
            st.markdown("**Rep KPI**")
            rep_view = _to_canonical_headers(_amount_to_thousand(rep_df)) if show_raw_cols else _amount_to_thousand(rep_df)
            st.dataframe(rep_view, use_container_width=True, height=420)
            _render_downloads(rep_view, f"rep_kpi_{period_pick}_view", f"kpi_rep_{period_pick}")

    with tab4:
        st.subheader("Validation & Trace 운영")
        v = _to_canonical_headers(validation_df) if show_raw_cols else validation_df
        tlog = _to_canonical_headers(trace_log_df) if show_raw_cols else trace_log_df
        thist = _to_canonical_headers(trace_hist_df) if show_raw_cols else trace_hist_df

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Validation Report**")
            st.dataframe(v, use_container_width=True, height=260)
            _render_downloads(v, "validation_report_view", "val_view")
        with c2:
            st.markdown("**Trace History (상태 전이 로그)**")
            st.dataframe(thist, use_container_width=True, height=260)
            _render_downloads(thist, "trace_history_view", "trace_hist_view")

        st.markdown("**Trace Log (현재 상태)**")
        if not tlog.empty:
            tcanon = {_canonical_col(c): c for c in tlog.columns}
            if "trace_status" in tcanon:
                st.write("상태 분포:", tlog[tcanon["trace_status"]].value_counts(dropna=False).to_dict())
        st.dataframe(tlog, use_container_width=True, height=420)
        _render_downloads(tlog, "trace_log_view", "trace_log_view")


if __name__ == "__main__":
    main()
