"""Unmasked: Re-identification Risk Meter (Streamlit app).  Run:  streamlit run app.py"""
import json
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


@st.cache_data(show_spinner="Loading data…")
def load_builtin():
    return pd.read_parquet(cfg["data"]["planted_parquet"])


def read_upload(f):
    df = pd.read_csv(f) if f.name.endswith(".csv") else pd.read_excel(f)
    df = df.rename(columns={"First Time First Year": "FTFY"})
    if "row_id" not in df.columns:
        df.insert(0, "row_id", range(len(df)))
    return df


# ---------------- sidebar ----------------
st.sidebar.title("🛡️ Unmasked")
st.sidebar.caption("Synthetic data only. Planted names, emails, IDs, and comments are fake.")
src = st.sidebar.radio("Data", ["BU synthetic NSSE (with planted PII)", "Upload CSV/XLSX"])
if src.startswith("BU"):
    df = load_builtin()
else:
    up = st.sidebar.file_uploader("Upload a file", type=["csv", "xlsx"])
    if up is None:
        st.info("Upload a file or switch to the built-in dataset.")
        st.stop()
    df = read_upload(up)
st.sidebar.write(f"**{len(df):,} rows × {df.shape[1] - 1} columns**")
st.sidebar.write("AI agent: " + ("🟢 LLM connected" if llm.llm_enabled() else "⚪ rule-based fallback (no LLM key)"))
st.sidebar.caption("The AI only ever sees column names, counts, and computed metrics, never student rows.")

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
        known = classify.roles_from_config(cfg) if src.startswith("BU") else None
        st.session_state.profile = classify.profile_columns(df)
        st.session_state.roles = classify.classify_columns(st.session_state.profile, known)
    roles = st.session_state.roles
    table = pd.DataFrame([{"column": c, "role": v["role"], "reason": v["reason"], "source": v["source"]}
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
        if stairs is not None:
            stairs["label"] = stairs["n_fields"].astype(str) + " fields"
            fig = px.bar(stairs, x="label", y="pct_unique", text_auto=".0%", hover_data=["fields"],
                         title="Each ordinary field you add makes more students unique",
                         color_discrete_sequence=PALETTE)
            fig.update_layout(yaxis_tickformat=".0%", xaxis_title="", yaxis_title="% uniquely identifiable")
            st.plotly_chart(fig, use_container_width=True)

        if len(quasi) >= 2:
            combos = risk.riskiest_combos(df, quasi, max_size=2, k=k)
            pairs = combos[combos["size"] == 2].copy()
            pairs[["a", "b"]] = pairs["combo"].str.split(" + ", regex=False, expand=True)
            heat = pairs.pivot(index="a", columns="b", values="pct_unique")
            fig = px.imshow(heat, text_auto=".0%", color_continuous_scale="Blues",
                            title="Riskiest pairs of fields (% unique)")
            st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            personas = {p: [c for c in cols if c in df.columns] for p, cols in cfg["personas"].items()}
            pr = attacks.persona_risk(df, {p: c for p, c in personas.items() if c}, k)
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
    if st.button("🤖 Run privacy agent", type="primary"):
        with st.status("Agent working…", expanded=True) as status:
            result = run_agent(df, roles, target_k=target_k, max_suppression=max_sup, protect_small_groups=protect,
                               group_col=cfg["roles"]["group_col"],
                               max_group_suppression=cfg["targets"]["max_group_suppression"],
                               personas={p: c for p, c in cfg["personas"].items() if all(x in df.columns for x in c)},
                               scales=cfg["utility_analyses"]["scales"], by_list=cfg["utility_analyses"]["by"],
                               scrub_comments=scrub, log=st.write)
            status.update(label="Done", state="complete")
        st.session_state.result = result
        st.session_state.max_removed = max_sup
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
            st.subheader("🏷️ Privacy nutrition label")
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
            if fair is not None:
                fig = px.bar(fair, x="group", y="pct_suppressed", color="setting", barmode="group", text_auto=".1%",
                             title="Who pays for privacy? Records removed by group", color_discrete_sequence=PALETTE)
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
            if ms and mode in ms:
                ml = ms[mode]["ml"]
                st.write(f"**ML utility test:** predicting engagement score SE, R² {ml['r2_original']:.2f} on original data "
                         f"vs {ml['r2_release']:.2f} on the protected release.")
        curve = res_csv("curve.csv")
        if curve is not None:
            fig = px.line(curve, x="k", y=["pct_suppressed", "mean_abs_shift"], markers=True,
                          title="Privacy vs. usefulness as k increases", color_discrete_sequence=PALETTE)
            st.plotly_chart(fig, use_container_width=True)
        det = res_csv("detection.csv")
        if det is not None:
            st.subheader("PII detection on planted ground truth")
            st.dataframe(det, hide_index=True)
        with st.expander("Agent log"):
            st.write("\n".join(f"- {s}" for s in r["steps"]))

# ---------------- 6. report ----------------
with tabs[5]:
    st.header("Report & download")
    r = st.session_state.get("result")
    if r is None:
        st.info("Run the agent in tab 4.")
    else:
        st.markdown(r["report_md"])
        release = r["mitigation"]["release_df"].drop(columns=["row_id"], errors="ignore")
        st.download_button("⬇️ Download safe release (CSV)", release.to_csv(index=False), "release.csv", "text/csv")
        st.download_button("⬇️ Download report (Markdown)", r["report_md"], "privacy_report.md", "text/markdown")
        st.caption("Token vaults stay in keys/ and are never bundled with the release. Tokenized data is pseudonymous, "
                   "not anonymous: whoever holds the vault key can re-link it.")
