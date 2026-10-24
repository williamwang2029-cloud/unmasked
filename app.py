"""Unmasked: Re-identification Risk Meter (Streamlit app).  Run:  streamlit run app.py"""
import json
import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

from reid import attacks, classify, llm, risk
from reid.agent import run_agent
from reid.config import load_config
from reid.release_warnings import release_warnings

load_dotenv()
st.set_page_config(page_title="Unmasked: Re-identification Risk Meter", page_icon="🛡️", layout="wide")
cfg = load_config()
PALETTE = px.colors.qualitative.Safe
RES = Path("results")


def res_csv(name):
    p = RES / name
    return pd.read_csv(p) if p.exists() else None


def res_json(name):
    p = RES / name
    return json.loads(p.read_text()) if p.exists() else None


BU_PARQUET = Path(cfg["data"]["planted_parquet"])
DEMO_CSV = Path("examples/demo_planted.csv")
BU_OPTION = "BU synthetic NSSE (with planted PII)"
DEMO_OPTION = "Demo data (generated, fake)"
UPLOAD_OPTION = "Upload CSV/XLSX"


@st.cache_data(show_spinner="Loading data…")
def load_builtin():
    return pd.read_parquet(BU_PARQUET)


@st.cache_data(show_spinner="Loading demo data…")
def load_demo():
    # logdate parsed as a date; MAJsecond kept as text; empty cells stay missing.
    df = pd.read_csv(DEMO_CSV, dtype={"MAJsecond": "string"}, parse_dates=["logdate"])
    if "row_id" not in df.columns:
        df.insert(0, "row_id", range(len(df)))
    return df


def read_upload(f):
    df = pd.read_csv(f) if f.name.endswith(".csv") else pd.read_excel(f)
    df = df.rename(columns={"First Time First Year": "FTFY"})
    if "row_id" not in df.columns:
        df.insert(0, "row_id", range(len(df)))
    return df


@st.cache_data(ttl=600, show_spinner=False)
def llm_mode():
    """Return (mode, model). One tiny test call; sends no data. Cached ~10 min."""
    model = os.getenv("LLM_MODEL") or ""
    if not llm.llm_enabled():
        return "No LLM: rule-based mode", model
    reply = llm.complete("Reply with OK.", max_tokens=5)
    if reply:
        return "LLM connected", model
    return "LLM configured but not responding: using rule-based mode", model


def using_llm(mode):
    return mode == "LLM connected"


# ---------------- sidebar ----------------
st.sidebar.title("🛡️ Unmasked")
st.sidebar.caption("Synthetic data only. Planted names, emails, IDs, and comments are fake.")

options = []
if BU_PARQUET.exists():
    options.append(BU_OPTION)
options.append(DEMO_OPTION)
options.append(UPLOAD_OPTION)
src = st.sidebar.radio("Data", options)
is_bu = src == BU_OPTION

if src == BU_OPTION:
    df = load_builtin()
elif src == DEMO_OPTION:
    if not DEMO_CSV.exists():
        st.error("Demo data not found. Run: python scripts/make_demo_data.py")
        st.stop()
    df = load_demo()
    st.info("Using generated demo data: fully fake, same columns as the BU survey. The BU dataset isn't "
            "included in this repo. See the README.")
else:
    up = st.sidebar.file_uploader("Upload a file", type=["csv", "xlsx"])
    if up is None:
        st.info("Upload a file, or switch to the demo dataset.")
        st.stop()
    df = read_upload(up)
st.sidebar.write(f"**{len(df):,} rows × {df.shape[1] - 1} columns**")

_mode, _model = llm_mode()
_icon = {"LLM connected": "🟢", "LLM configured but not responding: using rule-based mode": "🟠",
         "No LLM: rule-based mode": "⚪"}[_mode]
_mode_label = _mode + (f" ({_model})" if using_llm(_mode) and _model else "")
st.sidebar.info(f"{_icon} **{_mode_label}**")
if st.sidebar.button("🔄 Recheck LLM connection"):
    llm_mode.clear()
    st.rerun()
st.sidebar.caption("Risk measurement, mitigation, and attacks work the same with or without an LLM. The LLM "
                   "only writes the plan, report wording, and column-role explanations, and it sees only "
                   "column metadata and computed metrics.")

tabs = st.tabs(["1 · Data", "2 · Column roles", "3 · Risk", "4 · Fix it", "5 · Before vs. after", "6 · Report & download"])

# ---------------- 1. data ----------------
with tabs[0]:
    st.header("Is this dataset really anonymous?")
    st.write("This file has no names attached to survey answers. Let’s check whether students can still be singled out.")
    st.dataframe(df.drop(columns=["row_id"]).head(20), use_container_width=True)

# ---------------- 2. roles ----------------
with tabs[1]:
    st.header("What is each column?")
    st.write("The agent labels every column from metadata only. Review and override before measuring risk.")
    if st.button("🤖 Classify columns") or "roles" not in st.session_state:
        # BU and demo share the BU survey's columns, so use the known schema for both.
        known = classify.roles_from_config(cfg) if src in (BU_OPTION, DEMO_OPTION) else None
        st.session_state.profile = classify.profile_columns(df)
        st.session_state.roles = classify.classify_columns(st.session_state.profile, known)
    roles = st.session_state.roles
    SOURCE_LABELS = {"schema": "Known schema", "heuristic": "Rule-based", "llm": "LLM"}
    table = pd.DataFrame([{"column": c, "role": v["role"], "reason": v["reason"],
                           "source": SOURCE_LABELS.get(v["source"], v["source"])}
                          for c, v in roles.items()])
    edited = st.data_editor(table, hide_index=True, use_container_width=True, disabled=["column", "reason", "source"],
                            column_config={"role": st.column_config.SelectboxColumn("role", options=classify.ROLES, required=True)})
    if st.button("✅ Confirm roles"):
        st.session_state.roles = {r.column: {**roles[r.column], "role": r.role} for r in edited.itertuples()}
        st.success("Roles confirmed.")

roles = st.session_state.get("roles", {})
quasi = [c for c, v in roles.items() if v["role"] == "quasi_id" and c in df.columns]
meta = [c for c, v in roles.items() if v["role"] == "metadata" and c in df.columns]
k = cfg["targets"]["k"]

# ---------------- 3. risk ----------------
with tabs[2]:
    st.header("How identifiable are students?")
    if not quasi:
        st.warning("No quasi-identifiers selected yet (tab 2).")
    else:
        base = risk.risk_summary(df, quasi, k)
        withm = risk.risk_summary(df, quasi + meta, k)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Uniquely identifiable", f"{base['pct_unique']:.1%}")
        c2.metric(f"In a group smaller than {k}", f"{base['pct_below_k']:.1%}")
        c3.metric("Including survey timing", f"{withm['pct_unique']:.1%}")
        c4.metric("Average re-identification risk", f"{base['avg_risk']:.2f}")

        stairs = res_csv("staircase.csv")
        if is_bu and stairs is not None:
            stairs["label"] = stairs["n_fields"].astype(str) + " fields"
            fig = px.bar(stairs, x="label", y="pct_unique", text_auto=".0%", hover_data=["fields"],
                         title="Each ordinary field you add makes more students unique",
                         color_discrete_sequence=PALETTE)
            fig.update_layout(yaxis_tickformat=".0%", xaxis_title="", yaxis_title="% uniquely identifiable")
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Precomputed on BU's synthetic NSSE data.")

        LABELS = {"Year": "Year", "Class": "Class", "program": "Program", "FTFY": "First-time first-year",
                  "affiliation": "Affiliation", "MAJfirstcode": "First major", "MAJsecondcode": "Second major",
                  "begincol": "Began at college", "edaspire": "Education goal",
                  "attend_voc": "Attended vocational", "attend_com": "Attended community college",
                  "attend_col": "Attended other college", "attend_none": "No prior attendance",
                  "attend_other": "Other prior attendance", "logdate": "Survey date", "duration": "Survey duration"}

        if len(quasi) >= 2:
            # attendance flags are all ~0%; leave them out to keep the grid readable
            heat_qis = [q for q in quasi if not q.startswith("attend_")]
            if len(heat_qis) < 2:
                heat_qis = quasi
            combos = risk.riskiest_combos(df, heat_qis, max_size=2, k=k)
            pairs = combos[combos["size"] == 2].copy()
            if len(pairs):
                pairs[["a", "b"]] = pairs["combo"].str.split(" + ", regex=False, expand=True)
                both = pd.concat([pairs, pairs.rename(columns={"a": "b", "b": "a"})])   # make it symmetric
                heat = (both.pivot(index="a", columns="b", values="pct_below_k")
                            .reindex(index=heat_qis, columns=heat_qis))
                heat = heat.rename(index=lambda c: LABELS.get(c, c), columns=lambda c: LABELS.get(c, c))
                top = pairs.sort_values("pct_below_k", ascending=False).iloc[0]
                fig = px.imshow(heat, text_auto=".0%", color_continuous_scale="Cividis", aspect="auto",
                                labels=dict(x="", y="", color=f"% in groups < {k}"),
                                title=f"Riskiest pair: {LABELS.get(top['a'], top['a'])} + "
                                      f"{LABELS.get(top['b'], top['b'])}<br>puts {top['pct_below_k']:.0%} "
                                      f"of students in groups smaller than {k}")
                fig.update_layout(height=550, coloraxis_colorbar_tickformat=".0%")
                st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            personas = attacks.personas_for(df, cfg["personas"], quasi)
            if not personas:
                st.info("No quasi-identifiers to simulate an attacker with.")
            else:
                pr = attacks.persona_risk(df, personas, k)
                if len(pr):
                    fig = px.bar(pr, x="persona", y="pct_unique", text_auto=".0%", hover_data=["fields"],
                                 title="What different attackers could do", color_discrete_sequence=PALETTE)
                    fig.update_layout(yaxis_tickformat=".0%")
                    st.plotly_chart(fig, use_container_width=True)
        with col2:
            g = cfg["roles"]["group_col"]
            if g in df.columns:
                rbg = risk.risk_by_group(df, quasi, g, k)
                fig = px.bar(rbg, x="group", y="pct_below_k", text_auto=".0%",
                             title=f"Share at risk (group < {k}) by {g}", color_discrete_sequence=PALETTE)
                fig.update_layout(yaxis_tickformat=".0%")
                st.plotly_chart(fig, use_container_width=True)
        if meta:
            st.subheader("Hidden leak: survey metadata")
            st.dataframe(risk.metadata_leaks(df, cols=meta, combos=()), hide_index=True)

# ---------------- 4. fix ----------------
with tabs[3]:
    st.header("Fix it")
    c1, c2, c3 = st.columns(3)
    target_k = c1.slider("Every group must have at least k students", 2, 10, k)
    max_sup = c2.slider("Max share of records removed", 0.0, 0.10, cfg["targets"]["max_suppression"], 0.01)
    protect = c3.toggle("Protect small demographic groups", value=True,
                        help="Never merge or drop the demographic group column, so equity analyses stay possible.")
    scrub = st.radio("Free-text comments", ["drop", "presidio"], horizontal=True,
                     help="Presidio scrubbing on all rows can take a few minutes.")
    _run_mode, _run_model = llm_mode()
    if using_llm(_run_mode):
        st.caption(f"The agent will run with an LLM ({_run_model}) writing the plan and report." if _run_model
                   else "The agent will run with an LLM writing the plan and report.")
    else:
        st.caption("The agent will run in rule-based mode (no LLM).")
    if st.button("🤖 Run privacy agent", type="primary"):
        with st.status("Agent working…", expanded=True) as status:
            result = run_agent(df, roles, target_k=target_k, max_suppression=max_sup, protect_small_groups=protect,
                               group_col=cfg["roles"]["group_col"],
                               max_group_suppression=cfg["targets"]["max_group_suppression"],
                               personas=attacks.personas_for(df, cfg["personas"], quasi),
                               scales=cfg["utility_analyses"]["scales"], by_list=cfg["utility_analyses"]["by"],
                               scrub_comments=scrub, log=st.write)
            status.update(label="Done", state="complete")
        st.session_state.result = result
        st.session_state.max_removed = max_sup
        st.session_state.run_llm_mode = _run_mode
        st.session_state.run_llm_model = _run_model
        rw = release_warnings(
            considered_qis=list(result["mitigation"]["levels"].keys()),
            active_qis=result["mitigation"]["active_qis"],
            analysis_status=result["utility"]["analysis_status"],
            pct_removed=float(result["mitigation"]["suppressed_mask"].mean()),
            max_removed=max_sup,
        )
        for w in rw["warnings"]:
            st.warning(w)
        for e in rw["errors"]:
            st.error(e)

# ---------------- 5. before / after ----------------
with tabs[4]:
    st.header("Before vs. after")
    r = st.session_state.get("result")
    if r is None:
        st.info("Run the agent in tab 4.")
    else:
        rw = release_warnings(
            considered_qis=list(r["mitigation"]["levels"].keys()),
            active_qis=r["mitigation"]["active_qis"],
            analysis_status=r["utility"]["analysis_status"],
            pct_removed=float(r["mitigation"]["suppressed_mask"].mean()),
            max_removed=st.session_state.get("max_removed", cfg["targets"]["max_suppression"]),
        )
        for w in rw["warnings"]:
            st.warning(w)
        for e in rw["errors"]:
            st.error(e)
        lab = r["label"]
        with st.container(border=True):
            st.subheader("📋 Release Privacy Summary")
            a, b, c, d = st.columns(4)
            a.metric("Unique before → after", f"{lab['pct_unique_before']:.1%} → {lab['pct_unique_after']:.1%}")
            b.metric("Smallest group (k)", lab["k_after"])
            c.metric("Records removed", f"{lab['pct_suppressed']:.1%}")
            d.metric("Attack success", f"{lab['attack_before_pct']:.0%} → {lab['attack_after_pct']:.0%}")
            if lab["most_affected_group"]:
                st.write(f"**Most affected group:** {lab['most_affected_group']} ({lab['most_affected_pct']:.1%} removed)")
            st.write(f"**Largest shift in a group average:** {lab['max_mean_shift']:.2f} points (0–60 scale)")
            for x in lab["remaining_risks"]:
                st.write("⚠️ " + x)

        atk = pd.DataFrame([{"persona": p, "when": w, "re-identified": v[w]["correct_rate"]}
                            for p, v in r["attacks"].items() for w in ("before", "after")])
        fig = px.bar(atk, x="persona", y="re-identified", color="when", barmode="group", text_auto=".0%",
                     title="Simulated linkage attacks (200 targets each)", color_discrete_sequence=PALETTE)
        fig.update_layout(yaxis_tickformat=".0%")
        st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            fair = res_csv("fairness.csv")
            if is_bu and fair is not None:
                fig = px.bar(fair, x="group", y="pct_suppressed", color="setting", barmode="group", text_auto=".1%",
                             title="Who pays for privacy? Records removed by group", color_discrete_sequence=PALETTE)
                fig.update_layout(yaxis_tickformat=".0%")
                st.plotly_chart(fig, use_container_width=True)
                st.caption("Precomputed on BU's synthetic NSSE data.")
            else:
                fig = px.bar(r["fairness"], x="group", y="pct_suppressed", text_auto=".1%",
                             title="Records removed by group", color_discrete_sequence=PALETTE)
                fig.update_layout(yaxis_tickformat=".0%")
                st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.subheader("Which analyses still work?")
            st.dataframe(pd.DataFrame([{"analysis by": k2, "status": v} for k2, v in r["utility"]["analysis_status"].items()]),
                         hide_index=True)
            st.caption(f"Fields kept in the release: {rw['fields_kept']}")
            ms = res_json("mitigation_summary.json")
            mode = "protect_on" if r["protect_small_groups"] else "protect_off"
            if is_bu and ms and mode in ms:
                ml = ms[mode]["ml"]
                st.write(f"**ML utility test:** predicting engagement score SE, R² {ml['r2_original']:.2f} on original data "
                         f"vs {ml['r2_release']:.2f} on the protected release.")
                st.caption("Precomputed on BU's synthetic NSSE data.")
        curve = res_csv("curve.csv")
        if is_bu and curve is not None:
            fig = px.line(curve, x="k", y=["pct_suppressed", "mean_abs_shift"], markers=True,
                          title="Privacy vs. usefulness as k increases", color_discrete_sequence=PALETTE)
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Precomputed on BU's synthetic NSSE data.")
        det = res_csv("detection.csv")
        if is_bu and det is not None:
            st.subheader("PII detection on planted ground truth")
            st.dataframe(det, hide_index=True)
            st.caption("Precomputed on BU's synthetic NSSE data.")
        with st.expander("Agent log"):
            st.write("\n".join(f"- {s}" for s in r["steps"]))

# ---------------- 6. report ----------------
with tabs[5]:
    st.header("Report & download")
    r = st.session_state.get("result")
    if r is None:
        st.info("Run the agent in tab 4.")
    else:
        run_mode = st.session_state.get("run_llm_mode", "No LLM: rule-based mode")
        run_model = st.session_state.get("run_llm_model", "")
        if using_llm(run_mode):
            st.caption(f"Written by: LLM ({run_model})" if run_model else "Written by: LLM")
        else:
            st.caption("Written by: rule-based template")
        st.markdown(r["report_md"])
        release = r["mitigation"]["release_df"].drop(columns=["row_id"], errors="ignore")
        st.download_button("⬇️ Download safe release (CSV)", release.to_csv(index=False), "release.csv", "text/csv")
        st.download_button("⬇️ Download report (Markdown)", r["report_md"], "privacy_report.md", "text/markdown")
        st.caption("Token vaults stay in keys/ and are never bundled with the release. Tokenized data is pseudonymous, "
                   "not anonymous: whoever holds the vault key can re-link it.")
