"""Rebuild the report asset pack from frozen, read-only evidence.

Run from any directory: python docs/final_report_assets/provenance/generate_assets.py
The script writes only inside docs/final_report_assets. It never exports raw study rows.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import shutil
import zipfile
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import pandas as pd

HERE = Path(__file__).resolve().parent
PACK = HERE.parent
ROOT = PACK.parent.parent
PARENT = ROOT.parent
DOWNLOADS = Path(r"C:\Users\Abdelazim\Downloads")
V89 = DOWNLOADS / "CM3070_CANONICAL_FINAL_REPORT_EVIDENCE_LOG_v89.md"
STUDY_ZIP = DOWNLOADS / "AI-Driven Football Tactical Analysis and Training Evaluation System — Prototype Evaluation.csv.zip"
E2E = ROOT / "IMPLEMENTATION_PHASE6_FINAL_E2E_RESULT.json"
TIMINGS = ROOT / "IMPLEMENTATION_PHASE6_STAGE_TIMINGS.json"
TRANSPORT = ROOT / "IMPLEMENTATION_PHASE6_TRANSPORT_COPY_MANIFEST.json"
CAL_GATE = ROOT / "IMPLEMENTATION_PHASE6_CALIBRATION_GATE.json"
P0 = ROOT / "P0_ARCHITECTURE_CONTRACT_FREEZE_REV2A.json"
PROTOCOL = PARENT / "final_vision_evaluation" / "FORMAL_EXECUTION_PROTOCOL.json"
CAL_POINTS = PARENT / "physical_metric_upgrade" / "experiments" / "homography_validation_physical_corrected" / "03_validation" / "corrected_independent_point_validation.csv"
CAL_SUMMARY = PARENT / "physical_metric_upgrade" / "experiments" / "homography_validation_physical_corrected" / "04_results" / "corrected_homography_validation_summary.json"
RESEARCH = Path(r"G:\My Drive\Football_Training_Assistant_MVP")
VISION_AGG = RESEARCH / "methodology_comparison/final_evaluation/whole_system_challenge_evaluation/FINAL_WHOLE_SYSTEM_AGGREGATE_METRICS.csv"
VISION_CLIP = RESEARCH / "methodology_comparison/final_evaluation/whole_system_challenge_evaluation/FINAL_WHOLE_SYSTEM_PER_CLIP_METRICS.csv"
VISION_SAFETY = RESEARCH / "methodology_comparison/final_evaluation/whole_system_challenge_evaluation/FINAL_WHOLE_SYSTEM_IDENTITY_SAFETY.json"
ASR_COMPARE = RESEARCH / "methodology_comparison/asr/model_selection/ASR_CANDIDATE_A_VS_B_FINAL_COMPARISON.csv"
LLM_DECISION = RESEARCH / "methodology_comparison/llm/LLM_SELECTION_DECISION.json"
LLM_FREEZE = RESEARCH / "methodology_comparison/llm/LLM_FINAL_INTEGRATION_FREEZE.json"
VISION_MANIFEST = RESEARCH / "methodology_comparison/final_evaluation/whole_system_challenge_evaluation/FINAL_WHOLE_SYSTEM_EVALUATION_MANIFEST.json"
G_PROTOCOL = RESEARCH / "methodology_comparison/final_vision_evaluation/formal_fresh_state_per_clip/FORMAL_EXECUTION_PROTOCOL.json"
SHOWCASE = ROOT / "golden/fixtures/showcase_frontend_payload.json"

NAVY = "#17324d"
BLUE = "#2875a8"
TEAL = "#16817a"
ORANGE = "#d48325"
RED = "#b94d4d"
GRAY = "#607080"
LIGHT = "#eef4f7"
PALETTE = [BLUE, TEAL, ORANGE]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.titlesize": 14,
                     "axes.labelsize": 10, "svg.fonttype": "none", "figure.facecolor": "white",
                     "axes.spines.top": False, "axes.spines.right": False})

for part in ["00_catalog", "01_introduction", "02_design_architecture", "03_methodology/vision",
             "03_methodology/asr", "03_methodology/fusion", "03_methodology/llm",
             "03_methodology/calibration", "04_implementation", "05_evaluation/vision",
             "05_evaluation/asr", "05_evaluation/llm", "05_evaluation/calibration",
             "05_evaluation/end_to_end", "05_evaluation/user_study", "06_iterative_design",
             "07_limitations_future_work", "tables", "source_data", "screenshots", "provenance"]:
    (PACK / part).mkdir(parents=True, exist_ok=True)

def load_json(p):
    return json.loads(p.read_text(encoding="utf-8"))

e2e = load_json(E2E)
timings = load_json(TIMINGS)
transport = load_json(TRANSPORT)
cal_summary = load_json(CAL_SUMMARY)
cal_points = pd.read_csv(CAL_POINTS)
v89_text = V89.read_text(encoding="utf-8")
with zipfile.ZipFile(STUDY_ZIP) as z:
    study_bytes = z.read(next(n for n in z.namelist() if n.lower().endswith(".csv")))
assert hashlib.sha256(study_bytes).hexdigest() == "b61c5ec89c0a3b96905af9e4e3ac928e4777e232d78d08706f9fa8d96232dbb5"
study = pd.read_csv(io.BytesIO(study_bytes))
assert len(study) == 6

REG = []
def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()

def register(paths, title, kind, sources, fields, derivation, caption, caveat, priority, placement, data=None):
    if isinstance(paths, (str, Path)): paths = [paths]
    paths = [Path(p) for p in paths]
    REG.append(dict(id=paths[0].stem, title=title, kind=kind,
                    paths=[p.relative_to(PACK).as_posix() for p in paths],
                    source_paths=[str(Path(s)) for s in sources],
                    source_fields=fields, derived_calculation=derivation,
                    caption=caption, guardrail=caveat, priority={"high":"A","medium":"B","low":"C"}.get(priority,priority),
                    placement=placement,
                    source_data=data.relative_to(PACK).as_posix() if data else None))

def save_fig(fig, rel, **meta):
    stem = PACK / rel
    fig.savefig(stem.with_suffix(".svg"), bbox_inches="tight", facecolor="white")
    fig.savefig(stem.with_suffix(".png"), dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    register([stem.with_suffix(".svg"), stem.with_suffix(".png")], kind="figure", **meta)

def save_data(name, df):
    p = PACK / "source_data" / (name + ".csv")
    df.to_csv(p, index=False, encoding="utf-8")
    return p

def box(ax, x, y, w, h, title, detail="", color=BLUE, fc=LIGHT):
    rect = FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.012,rounding_size=0.016",
                          linewidth=1.4, edgecolor=color, facecolor=fc)
    ax.add_patch(rect)
    ax.text(x+w/2,y+h*.67,title,ha="center",va="center",fontweight="bold",color=NAVY,fontsize=10)
    if detail: ax.text(x+w/2,y+h*.31,detail,ha="center",va="center",color=GRAY,fontsize=8.3,linespacing=1.3)

def arrow(ax, x1,y1,x2,y2, color=GRAY):
    ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle="-|>",mutation_scale=13,
                                 linewidth=1.35,color=color))

def diagram(rel, heading, draw, **meta):
    fig,ax=plt.subplots(figsize=(12,5.3))
    ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis("off")
    ax.text(.02,.97,heading,ha="left",va="top",fontsize=17,fontweight="bold",color=NAVY)
    draw(ax)
    save_fig(fig,rel,**meta)

def table(name, title, df, sources, fields, caption, caveat, placement, priority="high", derivation="None"):
    csvp=PACK/"tables"/(name+".csv")
    mdp=PACK/"tables"/(name+".md")
    df.to_csv(csvp,index=False,encoding="utf-8")
    vals=[[str(v) for v in row] for row in df.itertuples(index=False,name=None)]
    heads=[str(x) for x in df.columns]
    esc=lambda s:s.replace("|","\\|").replace("\n"," ")
    lines=["# "+title,"",caption,"","| "+" | ".join(map(esc,heads))+" |",
           "| "+" | ".join(["---"]*len(heads))+" |"]
    lines += ["| "+" | ".join(map(esc,row))+" |" for row in vals]
    lines += ["","**Guardrail:** "+caveat,"","**Sources:** "+"; ".join(str(s) for s in sources),""]
    mdp.write_text("\n".join(lines),encoding="utf-8")
    register([mdp,csvp],title,"table",sources,fields,derivation,caption,caveat,priority,placement)

# 1. Architecture, methodology, safety, and provenance diagrams.
def draw_overview(ax):
    xs=[.02,.22,.42,.62,.82]
    items=[("Private input","video + coaching audio"),("Vision","M2 selected; tracks"),
           ("ASR + fusion","events + response windows"),("Safety + report","identity / metric gates"),
           ("Coach UI","scoped evidence + caveats")]
    for i,(t,d) in enumerate(items):
        box(ax,xs[i],.42,.16,.28,t,d,color=PALETTE[i%3]);
        if i<4: arrow(ax,xs[i]+.16,.56,xs[i+1]-.01,.56)
    ax.text(.5,.19,"Real full-session run: completed with limitations; player attribution withheld",ha="center",color=RED,fontweight="bold")
diagram("01_introduction/system_overview", "From training media to evidence-scoped coaching output",draw_overview,
        title="System overview",sources=[P0,E2E,V89],fields="P0 contracts; E2E analysis status",
        derivation="Schematic only",caption="The integrated product processes private media through Vision, ASR, fusion, safety gates and reporting. The completed full-session run withheld player-level conclusions.",
        caveat="Schematic; no claim that automated persistent identity passed.",priority="high",placement="Introduction / system overview")

def draw_safety(ax):
    box(ax,.05,.57,.23,.23,"Vision observation","track evidence",BLUE)
    box(ax,.38,.57,.23,.23,"Formal identity gate","FAIL_UNSAFE_MERGE",RED,"#fff1f1")
    box(ax,.71,.57,.23,.23,"Player-level output","WITHHELD",RED,"#fff1f1")
    arrow(ax,.28,.685,.38,.685);arrow(ax,.61,.685,.71,.685,RED)
    box(ax,.38,.18,.23,.23,"Scoped evidence","anonymous / team / event",TEAL)
    arrow(ax,.495,.57,.495,.41,TEAL)
    ax.text(.5,.06,"Runtime heuristic diagnostics cannot override the formal gate",ha="center",color=RED,fontweight="bold")
diagram("02_design_architecture/fail_closed_identity_gate","Identity safety controls the report scope",draw_safety,
        title="Fail-closed identity gate",sources=[E2E,V89],fields="analysis.identity; v89 §138.4",
        derivation="Schematic only",caption="All three formal methods failed the identity-safety gate. The Phase 6 run returned scoped non-player evidence while withholding player-level analytics.",
        caveat="TrackEval IDSW and separate unsafe-merge audit are distinct diagnostics.",priority="high",placement="Design / safety architecture")

method_rows=[("M1","YOLO11m adapted","BoT-SORT + ReID","Original hybrid"),
             ("M2","RF-DETR-L","Deep-EIoU + GTA + ReID","Selected product run"),
             ("M3-v1","YOLO26m","SRITrack-v1","Re-entry focused")]
def draw_methods(ax):
    for i,(m,det,tr,role) in enumerate(method_rows):
        y=.69-i*.25
        box(ax,.04,y,.14,.16,m,role,PALETTE[i])
        box(ax,.28,y,.25,.16,det,"detector",PALETTE[i])
        box(ax,.63,y,.32,.16,tr,"association / tracking",PALETTE[i])
        arrow(ax,.18,y+.08,.28,y+.08);arrow(ax,.53,y+.08,.63,y+.08)
diagram("03_methodology/vision/methodology_stacks","Frozen complete Vision methodologies",draw_methods,
        title="Vision method stacks",sources=[P0,V89],fields="P0 method contracts; v89 §138",
        derivation="Schematic only",caption="The formal comparison evaluates complete detector-and-tracker methodologies. M2 is selected for the product, subject to a failed identity-safety gate.",
        caveat="Do not attribute DetA differences solely to detectors; no method enables player-level accumulated analytics.",priority="high",placement="Methodology / Vision")

def draw_fusion(ax):
    box(ax,.04,.44,.22,.27,"ASR tactical event","instruction end = t",BLUE)
    box(ax,.39,.44,.22,.27,"Response window","t + 2 s to t + 6 s",TEAL)
    box(ax,.74,.44,.22,.27,"Fused evidence","observed / missing / withheld",ORANGE)
    arrow(ax,.26,.575,.39,.575);arrow(ax,.61,.575,.74,.575)
    ax.text(.5,.19,"No target, track, or measurement is invented when evidence is missing",ha="center",color=RED,fontweight="bold")
diagram("03_methodology/fusion/response_window_contract","Instruction-to-response temporal contract",draw_fusion,
        title="Fusion response window",sources=[P0,E2E,V89],fields="P0 fusion window; analysis.response_windows_without_tracking",
        derivation="Schematic only",caption="Fusion inspects visual evidence from two to six seconds after an instruction ends and explicitly records unavailable responses.",
        caveat="Window is a contract, not a guarantee of observed player behaviour.",priority="high",placement="Methodology / Fusion")

def draw_calpolicy(ax):
    box(ax,.03,.48,.25,.27,"Research camera","fixed homography only",BLUE)
    box(ax,.38,.48,.25,.27,"Transport copy","different checksum",ORANGE)
    box(ax,.73,.48,.24,.27,"Product result","NO_METRIC_CALIBRATION",RED,"#fff1f1")
    arrow(ax,.28,.615,.38,.615);arrow(ax,.63,.615,.73,.615,RED)
    ax.text(.5,.2,"No metres, km/h, metric distance, or pitch-plane claim on this run",ha="center",color=RED,fontweight="bold")
diagram("03_methodology/calibration/calibration_permission_boundary","Camera-specific calibration did not transfer",draw_calpolicy,
        title="Calibration permission boundary",sources=[CAL_GATE,TRANSPORT,E2E],fields="calibration gate; source/transport SHA; analysis.calibration",
        derivation="Schematic only",caption="The research homography was denied for the derived transport input; the full-session product result used no metric calibration.",
        caveat="Research-camera RMSE does not validate arbitrary uploads or the Phase 6 transport copy.",priority="high",placement="Methodology / Calibration")

def draw_llm(ax):
    box(ax,.03,.44,.22,.27,"Structured evidence","provenance + nulls",BLUE)
    box(ax,.28,.44,.22,.27,"Llama 3.1 8B","bounded report attempt",TEAL)
    box(ax,.53,.44,.22,.27,"Patch-001","8 grounding gates",ORANGE)
    box(ax,.78,.44,.19,.27,"Output","validated / fallback",RED)
    for a,b in [(.25,.28),(.50,.53),(.75,.78)]:arrow(ax,a,.575,b,.575)
    ax.text(.5,.19,"Full-session Phase 6 report status: DETERMINISTIC_FALLBACK",ha="center",color=RED,fontweight="bold")
diagram("03_methodology/llm/grounded_reporting_flow","Grounded reporting and deterministic fallback",draw_llm,
        title="Report grounding flow",sources=[P0,E2E,V89],fields="P0 validator contract; analysis.report_status; v89 §143–144",
        derivation="Schematic only",caption="Structured evidence passes through the frozen Llama 3.1/Patch-001 reporting path; the full-session result used deterministic fallback.",
        caveat="A bounded C04 8/8 gate pass does not imply the full-session report was LLM-validated.",priority="high",placement="Methodology / Reporting")

# 2. Frozen Vision evaluation. Values transcribed from the canonical v89 §138.2 table.
vision = pd.read_csv(VISION_AGG)
assert list(vision["method"]) == ["method_1","method_2","method_3"]
vision["method"]=["M1","M2","M3-v1"]
v_safety=load_json(VISION_SAFETY)
vision["unsafe_shared_track_ids"]=[sum(v_safety[f"method_{i}"][clip]["unsafe_shared_track_count"] for clip in v_safety[f"method_{i}"]) for i in (1,2,3)]
assert list(vision["unsafe_shared_track_ids"]) == [21,9,9]
assert "| M2 · Global Association | 0.6710 | 0.6567" in v89_text
vision_data=save_data("vision_formal_aggregate",vision)
table("vision_formal_aggregate","Official four-clip complete-system Vision evaluation",vision,[VISION_AGG,VISION_SAFETY,V89,PROTOCOL],
      "v89 §138.2 and §138.4; protocol four clips", "Official TrackEval aggregate over four independent frozen challenge clips; unsafe shared-track IDs are a separate descriptive audit.",
      "All methods fail identity safety. M3's five IDSW must be read beside its 0.3273 recall and 14,180 FN.","Evaluation / Vision",derivation="Direct transcription; no recomputation")
fig,ax=plt.subplots(figsize=(9,5))
x=range(3); w=.24
for j,col in enumerate(["HOTA","DetA","AssA"]):
    ax.bar([v+(j-1)*w for v in x],vision[col],w,label=col,color=PALETTE[j])
ax.set_xticks(list(x),vision.method);ax.set_ylim(0,1);ax.set_ylabel("Official TrackEval score (0–1)")
ax.set_title("Four-clip complete-system Vision quality");ax.legend(ncol=3,loc="upper right")
ax.grid(axis="y",alpha=.18);ax.set_axisbelow(True)
save_fig(fig,"05_evaluation/vision/hota_deta_assa",title="Official HOTA, DetA and AssA",sources=[VISION_AGG,V89,PROTOCOL],
         fields="v89 §138.2 HOTA/DetA/AssA",derivation="Direct plotting of frozen aggregate values",
         caption="M2 achieved the highest aggregate HOTA, DetA and AssA across the frozen four-clip complete-system evaluation.",
         caveat="Whole-system metrics; all methods still fail the identity-safety gate.",priority="high",placement="Evaluation / Vision",data=vision_data)
fig,ax=plt.subplots(figsize=(9,5))
for j,col in enumerate(["precision","recall"]):
    ax.bar([v+(j-.5)*.3 for v in x],vision[col],.3,label=col,color=[BLUE,ORANGE][j])
ax.set_xticks(list(x),vision.method);ax.set_ylim(0,1.07);ax.set_ylabel("Proportion")
ax.set_title("Detection coverage prevents misleading IDSW interpretation");ax.legend();ax.grid(axis="y",alpha=.18);ax.set_axisbelow(True)
save_fig(fig,"05_evaluation/vision/precision_recall",title="Precision and recall by complete Vision method",sources=[VISION_AGG,V89,PROTOCOL],
         fields="v89 §138.2 precision/recall",derivation="Direct plotting",
         caption="M3-v1's low IDSW count accompanies very low recall (0.3273); coverage must be considered when interpreting identity diagnostics.",
         caveat="Precision/recall are whole-method evaluation values, not a standalone detector test.",priority="high",placement="Evaluation / Vision",data=vision_data)
fig,axs=plt.subplots(1,2,figsize=(10,4.5))
axs[0].bar(vision.method,vision.IDSW,color=PALETTE);axs[0].set_title("Official TrackEval IDSW");axs[0].set_ylabel("Count")
axs[1].bar(vision.method,vision.unsafe_shared_track_ids,color=PALETTE);axs[1].set_title("Separate unsafe shared-track audit")
for a in axs:a.grid(axis="y",alpha=.18);a.set_axisbelow(True)
save_fig(fig,"05_evaluation/vision/identity_diagnostics",title="Distinct identity diagnostics",sources=[VISION_AGG,VISION_SAFETY,V89],
         fields="v89 §138.2 IDSW and §138.4 one-to-one IoU audit",derivation="Direct plotting",
         caption="TrackEval ID switches and the separate one-to-one IoU shared-track audit are different measures; every method retained a failed identity gate.",
         caveat="Do not add the two count types or treat low IDSW as proof of safe persistent identity.",priority="high",placement="Evaluation / Vision",data=vision_data)

per_clip=pd.read_csv(VISION_CLIP)
per_clip["method"]=per_clip.method.replace({"method_1":"M1","method_2":"M2","method_3":"M3-v1"})
clip_data=save_data("vision_formal_per_clip",per_clip)
table("vision_formal_per_clip","Official Vision metrics by frozen challenge clip",per_clip,[VISION_CLIP,V89],
      "per-clip HOTA, DetA, AssA, MOTA, IDF1, IDSW, FP, FN, precision, recall",
      "M2 achieved the highest HOTA and IDF1 in each of the four independent challenge clips.",
      "The clips were fresh-state independent runs; per-clip scores do not prove full-session persistent identity.",
      "Evaluation / Vision",derivation="Direct CSV transcription")
fig,ax=plt.subplots(figsize=(10,5))
for j,m in enumerate(["M1","M2","M3-v1"]):
    vals=per_clip[per_clip.method==m].IDF1.values
    ax.bar([i+(j-1)*.25 for i in range(4)],vals,.25,label=m,color=PALETTE[j])
ax.set_xticks(range(4),["Re-entry","Occlusion","Same-team","Long gap"])
ax.set_ylim(0,1.05);ax.set_ylabel("Official IDF1 (0–1)")
ax.set_title("Identity score by independent challenge clip");ax.legend(ncol=3);ax.grid(axis="y",alpha=.18);ax.set_axisbelow(True)
save_fig(fig,"05_evaluation/vision/per_clip_idf1",title="Per-clip Vision IDF1",sources=[VISION_CLIP,V89],
         fields="IDF1 by method and clip",derivation="Direct plotting of per-clip CSV",
         caption="M2 had the highest IDF1 in all four frozen challenge clips, but failed the separate identity-safety gate.",
         caveat="IDF1 is not trajectory survival or permission for player-specific analytics.",priority="high",placement="Evaluation / Vision",data=clip_data)

# 3. ASR benchmark from canonical frozen §125–126; G direct benchmark pending mount.
asr=pd.DataFrame([["A: faster-whisper base.en",18.4,11.8571,92.8571,76.4706,83.8710,14,13,1,4],
                  ["B: Parakeet TDT 0.6B v2",36.8,23.2857,90.0,52.9412,66.6667,10,9,1,8]],
                 columns=["candidate","WER_pct","CER_pct","event_precision_pct","event_recall_pct","event_F1_pct","predictions","TP","FP","FN"])
assert "F1: 83.8710%" in v89_text
asr_source=pd.read_csv(ASR_COMPARE).set_index("Metric Dimension")
for metric,a,b in [("Word Error Rate (WER)",18.4,36.8),("Tactical F1 Score",83.8710,66.6667)]:
    assert float(asr_source.loc[metric].iloc[0].strip("%"))==a
    assert float(asr_source.loc[metric].iloc[1].strip("%"))==b
asr_data=save_data("asr_frozen_benchmark",asr)
table("asr_frozen_benchmark","Frozen ASR lexical and tactical-event comparison",asr,[ASR_COMPARE,V89],
      "v89 §125–126", "Candidate A was selected on the project's coaching audio under the corrected frozen tactical-event protocol.",
      "Project-specific benchmark; candidate runtimes used different hardware. No universal ASR ranking.","Evaluation / ASR",derivation="Direct transcription")
fig,axs=plt.subplots(1,2,figsize=(10,4.7))
axs[0].bar(["A","B"],asr.WER_pct,color=[TEAL,ORANGE]);axs[0].set_title("Word error rate ↓");axs[0].set_ylabel("%")
axs[1].bar(["A","B"],asr.event_F1_pct,color=[TEAL,ORANGE]);axs[1].set_title("Tactical-event F1 ↑");axs[1].set_ylabel("%")
for a in axs:a.grid(axis="y",alpha=.18);a.set_axisbelow(True)
save_fig(fig,"05_evaluation/asr/asr_comparison",title="Frozen ASR candidate comparison",sources=[ASR_COMPARE,V89],
         fields="v89 §125–126 WER and REV3 tactical F1",derivation="Direct plotting",
         caption="Selected Candidate A had 18.4% WER and 83.871% tactical-event F1, versus Candidate B's 36.8% and 66.667% on this project audio.",
         caveat="Candidate A's initial temporal-boundary circularity was corrected in the frozen REV3 protocol; hardware differs for runtime.",priority="high",placement="Evaluation / ASR",data=asr_data)

# LLM selection uses a lexicographic safety-first decision, not a composite score.
llm_decision=load_json(LLM_DECISION)
llm_freeze=load_json(LLM_FREEZE)
assert llm_decision["formal_decision_verdict"]=="CANDIDATE_B_SELECTED_FOR_FINAL_SYSTEM_INTEGRATION"
assert len(llm_freeze["validator_contract"]["deterministic_gates"])==8
llm=pd.DataFrame([["Qwen3 8B",5,11,5,2],["Llama 3.1 8B",15,1,15,0]],
                 columns=["candidate","completed_of_16","timeout_of_16","schema_valid_of_16","raw_pre_patch_gate_pass_of_16"])
llm_data=save_data("llm_formal_selection",llm)
table("llm_formal_selection","LLM frozen formal selection evidence",llm,[LLM_DECISION,LLM_FREEZE],
      "selection ranks 1–6; frozen Patch-001 contract",
      "Both candidates avoided unsupported player identity and unavailable-evidence misuse. Llama 3.1 was selected after 15/16 schema-valid runs versus Qwen3's 5/16.",
      "Raw pre-patch gate flags misclassified authorized numbers from string observations; do not interpret 0/16 as 16 hallucinations. Post-patch full benchmark was not rerun.",
      "Evaluation / LLM",derivation="Counts parsed from frozen selection decision; no new evaluation")
fig,ax=plt.subplots(figsize=(8.5,4.6))
for j,col in enumerate(["completed_of_16","schema_valid_of_16"]):
    ax.bar([i+(j-.5)*.32 for i in range(2)],llm[col],.32,label=col.replace("_of_16",""),color=[BLUE,TEAL][j])
ax.set_xticks(range(2),llm.candidate);ax.set_ylim(0,17);ax.set_ylabel("Cases of 16")
ax.set_title("Formal local LLM delivery and schema validity");ax.legend();ax.grid(axis="y",alpha=.18);ax.set_axisbelow(True)
save_fig(fig,"05_evaluation/llm/llm_schema_delivery",title="LLM formal schema delivery",sources=[LLM_DECISION,LLM_FREEZE],
         fields="selection ranks 4 and 9",derivation="Direct case counts from selection record",
         caption="The selected Llama 3.1 candidate completed and schema-validated 15/16 frozen cases, while Qwen3 did so for 5/16.",
         caveat="Pre-patch grounding numeric flags were false positives on authorized observations; safety was maintained through deterministic fallback. Full-session Phase 6 used fallback.",
         priority="high",placement="Evaluation / LLM",data=llm_data)
gates=pd.DataFrame([[i+1,g.split(": ",1)[1]] for i,g in enumerate(llm_freeze["validator_contract"]["deterministic_gates"])],
                   columns=["gate","frozen_check"])
table("grounding_gates","Eight deterministic report-grounding gates",gates,[LLM_FREEZE],
      "validator_contract.deterministic_gates", "Patch-001 preserves eight checks for identity, privacy, missing data and unsupported claims.",
      "The gate list specifies intended validation scope; it is not an empirical pass-rate result.","Methodology / Reporting",derivation="Direct list extraction")

# 4. Calibration validation from direct corrected independent point records.
cal_data=save_data("corrected_calibration_points",cal_points[["name","visibility","expected_x_m","expected_y_m","projected_x_m","projected_y_m","euclidean_error_m"]])
fig,ax=plt.subplots(figsize=(9,4.8))
labels=["Far sideline","Near sideline","Goal far post","Goal near post"]
ax.barh(labels,cal_points.euclidean_error_m,color=[BLUE,TEAL,BLUE,ORANGE]);ax.invert_yaxis()
ax.axvline(float(cal_summary["corrected_validation"]["rmse_m"]),color=RED,linestyle="--",label="RMSE 0.651 m")
ax.set_xlim(0,1.05);ax.set_xlabel("Independent landmark error (m)");ax.set_title("Corrected research-camera homography: four holdout landmarks")
ax.legend();ax.grid(axis="x",alpha=.18);ax.set_axisbelow(True)
save_fig(fig,"05_evaluation/calibration/corrected_landmark_errors",title="Independent calibration residuals",sources=[CAL_POINTS,CAL_SUMMARY],
         fields="euclidean_error_m; corrected RMSE",derivation="Direct point plot; RMSE line from summary (rounded to 3 decimals)",
         caption="Four independent landmarks support a corrected research-camera RMSE of approximately 0.651 m, with maximum error 0.841 m.",
         caveat="Moderate-confidence camera-specific estimate; not valid for arbitrary uploads or Phase 6 transport.",priority="high",placement="Evaluation / Calibration",data=cal_data)

# 5. Phase 6 transport and measured run.
src=transport["authoritative_research_source"]; dst=transport["derived_transport_copy"]
orig_video=next(s for s in src["probe"]["streams"] if s.get("codec_type")=="video")
dst_video=next(s for s in dst["probe"]["streams"] if s.get("codec_type")=="video")
provenance=pd.DataFrame([
    ["Original research source",src["size_bytes"],orig_video["width"],orig_video["height"],int(orig_video["nb_frames"]),src["sha256_previously_verified"]],
    ["Derived transport copy",dst["size_bytes"],dst_video["width"],dst_video["height"],int(dst_video["nb_frames"]),dst["sha256"]]],
    columns=["role","bytes","width_px","height_px","frames","sha256"])
prov_data=save_data("phase6_media_provenance",provenance)
table("phase6_media_provenance","Phase 6 source and transport provenance",provenance,[TRANSPORT,E2E],
      "source/derived probe, SHA, size, frames", "The accepted product input was a downscaled, nontrimmed derived copy with 20,391 frames; it is distinct from the research source.",
      "No formal research benchmark or research-camera metric calibration is transferred to the derived copy.","Implementation / Phase 6",derivation="Direct fields")
def draw_transport(ax):
    box(ax,.03,.43,.25,.32,"Research source",f"3840×2160 · 2.390 GB\n20,391 frames",BLUE)
    box(ax,.38,.43,.25,.32,"Transport copy",f"1920×1080 · 44.0 MB\n20,391 frames",TEAL)
    box(ax,.73,.43,.24,.32,"Product E2E","M2 · 340 s\ncompleted with limitations",ORANGE)
    arrow(ax,.28,.59,.38,.59);arrow(ax,.63,.59,.73,.59)
    ax.text(.5,.18,"Different SHA-256 → explicit derived-input provenance; research calibration denied",ha="center",color=RED,fontweight="bold")
diagram("04_implementation/phase6_transport_provenance","Source to transport to full-session run",draw_transport,
        title="Phase 6 transport provenance",sources=[TRANSPORT,E2E,CAL_GATE],fields="source/transport probe; analysis.calibration",
        derivation="GB/MB display rounded decimal from byte counts; full bytes in table",
        caption="The 2.390 GB original could not be uploaded; the 44.0 MB nontrimmed downscaled copy was accepted and used for the 340-second M2 E2E run.",
        caveat="Original upload and 64 MiB probe returned 413; exact provider limit is unknown. The copy is not a research benchmark input.",priority="high",placement="Implementation / Phase 6",data=prov_data)

tm=timings["modal_worker_measured_component_seconds"]
time_df=pd.DataFrame([["Media acquisition",tm["media_acquisition"]],["Model verification",tm["model_verification"]],
                      ["Pipeline total",tm["pipeline_total"]],["Persistence",tm["persistence"]],
                      ["Worker total",tm["worker_total"]]],columns=["measured_component","seconds"])
time_data=save_data("phase6_measured_timings",time_df)
table("phase6_measured_timings","Measured Phase 6 worker timings",time_df,[TIMINGS,E2E],
      "modal_worker_measured_component_seconds", "The worker total was 2,032.682 s (33 min 52.682 s); the pipeline aggregate dominated.",
      "Vision, ASR, fusion and report were not separately instrumented. Do not mistake API polling for exact stage runtime.","Evaluation / E2E",derivation="Seconds to minutes: seconds/60")
fig,ax=plt.subplots(figsize=(9,4.6))
comp=time_df.iloc[:4]
ax.barh(comp.measured_component,comp.seconds/60,color=[TEAL,BLUE,ORANGE,TEAL]);ax.invert_yaxis()
ax.set_xlabel("Measured minutes");ax.set_title("Phase 6 worker components (total 33.88 min)")
ax.grid(axis="x",alpha=.18);ax.set_axisbelow(True)
save_fig(fig,"05_evaluation/end_to_end/worker_timing",title="Measured Phase 6 worker components",sources=[TIMINGS],
         fields="modal_worker_measured_component_seconds",derivation="seconds/60; total is separately measured, not sum of bars",
         caption="The measured pipeline aggregate was 2,012.314 s of a 2,032.682 s worker run. Individual Vision/ASR/fusion/report durations are unavailable.",
         caveat="Bars omit uninstrumented overhead; component sums must not replace independently measured worker total.",priority="high",placement="Evaluation / E2E",data=time_data)

events=pd.DataFrame(e2e["analysis"]["instruction_events"])
events["group"]=events.category.replace({"Positioning / Hold Ground":"Positioning"})
events_data=save_data("phase6_event_summary",events.groupby("group").size().rename("count").reset_index())
fig,ax=plt.subplots(figsize=(8.5,4.3))
counts=events.groupby("group").size().reindex(["Pressing","Positioning","Defensive"])
ax.bar(counts.index,counts.values,color=[BLUE,TEAL,ORANGE]);ax.set_ylim(0,7);ax.set_ylabel("Instruction events")
ax.set_title("Phase 6 tactical events (n=13)");ax.grid(axis="y",alpha=.18);ax.set_axisbelow(True)
save_fig(fig,"05_evaluation/end_to_end/event_categories",title="Phase 6 tactical event categories",sources=[E2E],
         fields="analysis.instruction_events[].category",derivation="Count persisted event categories; Positioning / Hold Ground shortened for label",
         caption="The full-session run yielded 13 tactical events: six pressing, four positioning and three defensive.",
         caveat="These are ASR-derived events, not verified individual player responses or tactical compliance.",priority="high",placement="Evaluation / E2E",data=events_data)
windows=pd.DataFrame(e2e["analysis"]["response_windows_without_tracking"])
window_data=save_data("phase6_missing_response_windows",windows[["event_id","window_start_s","window_end_s"]])
fig,ax=plt.subplots(figsize=(10,4.5))
for i,row in windows.iterrows():
    ax.plot([row.window_start_s,row.window_end_s],[i,i],linewidth=7,color=RED,solid_capstyle="round")
ax.axvline(340,color=NAVY,linestyle="--",label="Media end: 340 s")
ax.set_yticks(range(len(windows)),windows.event_id);ax.set_xlim(165,348);ax.invert_yaxis()
ax.set_xlabel("Session time (s)");ax.set_title("Response windows with missing visual tracking")
ax.legend(loc="upper left");ax.grid(axis="x",alpha=.18);ax.set_axisbelow(True)
save_fig(fig,"05_evaluation/end_to_end/missing_response_windows",title="Phase 6 unavailable response windows",sources=[E2E],
         fields="analysis.response_windows_without_tracking",derivation="Direct window segments; media boundary from duration_s",
         caption="Six response windows lacked tracking or visual observations; some extend beyond the 340-second media boundary.",
         caveat="Unavailable tracking is not zero movement. Overlapping event windows remain separate records.",priority="high",placement="Evaluation / E2E",data=window_data)

e2e_summary=pd.DataFrame([
    ["Input role","DERIVED_TRANSPORT_COPY"],["Method","M2 RF-DETR/Deep-EIoU/GTA"],
    ["Media duration","340 s"],["Frames processed","20,391"],["Tactical events","13"],
    ["Structured evidence items","28"],["Unresolved instruction targets","13"],
    ["Missing response windows","6"],["Formal identity","FAIL_UNSAFE_MERGE"],
    ["Player-level analysis","Withheld"],["Calibration","NO_METRIC_CALIBRATION"],
    ["Metric values in evidence","0 (unavailable; not an observed zero)"],
    ["Report","DETERMINISTIC_FALLBACK"],["Job","COMPLETED_WITH_LIMITATIONS"]],columns=["field","observed_result"])
table("phase6_e2e_summary","Phase 6 full-session result",e2e_summary,[E2E],
      "product; analysis", "The accepted derived transport copy completed the full product path with explicit identity, calibration and report limitations.",
      "Metric value count is an absence of reported metric evidence, not a zero distance or speed.","Evaluation / E2E",derivation="Direct fields and explicit wording")

# 6. Study: six hash-matched raw rows are read in memory; only aggregate outputs leave this script.
names=["Purpose clear","Post-training useful","Pressing example","Marking example","Hold-position example",
       "Audio + movement","Numeric evidence clear","Report useful","Limitations clear","Trust via uncertainty",
       "Review with players","Real-training potential"]
likert=[]
for idx,label in enumerate(names,start=6):
    vals=study.iloc[:,idx].astype(str).str.extract(r"^([1-5])")[0].astype(int)
    likert.append([label,len(vals),round(float(vals.mean()),4),*[(vals==k).sum() for k in range(1,6)]])
for idx,label in [(20,"Overall usefulness"),(21,"Ease of understanding"),(22,"Spoken-to-visual link"),(27,"Withholding explanation")]:
    vals=study.iloc[:,idx].astype(str).str.extract(r"^([1-5])")[0].astype(int)
    likert.append([label,len(vals),round(float(vals.mean()),4),*[(vals==k).sum() for k in range(1,6)]])
lk=pd.DataFrame(likert,columns=["item","n","mean_1_to_5","rating_1","rating_2","rating_3","rating_4","rating_5"])
assert round(float(lk.loc[lk.item=="Withholding explanation","mean_1_to_5"].iloc[0]),2)==3.83
lk_data=save_data("coach_study_likert_aggregates",lk)
table("coach_study_likert","Coach-study descriptive Likert summary (n=6)",lk,[STUDY_ZIP,V89],
      "CSV columns 6–17,20–22,27; v89 §148.2", "Six respondents rated 16 prototype statements/items on a 1–5 scale; all means and response counts derive from the hash-matched CSV.",
      "Small purposive stakeholder sample; descriptive only, no inferential or population claim. Raw comments and timestamps excluded.","Evaluation / user study",derivation="Mean=sum of six integer ratings/6; rating counts per 1–5 category")
fig,ax=plt.subplots(figsize=(10,7))
subset=lk.sort_values("mean_1_to_5")
colors=[RED if x<4.1 else TEAL for x in subset.mean_1_to_5]
ax.barh(subset.item,subset.mean_1_to_5,color=colors);ax.set_xlim(0,5.2)
ax.set_xlabel("Mean rating (1–5)");ax.set_title("Coach-study descriptive ratings (n=6)")
ax.grid(axis="x",alpha=.18);ax.set_axisbelow(True)
save_fig(fig,"05_evaluation/user_study/study_item_means",title="Coach-study item means",sources=[STUDY_ZIP,V89],
         fields="CSV columns 6–17,20–22,27",derivation="Mean of six integer responses per item",
         caption="Withholding explanation was the lowest-rated item (3.83/5), informing the subsequent coach-facing design iterations.",
         caveat="Descriptive six-person study; ordinal item means are presentation summaries, not population estimates.",priority="high",placement="Evaluation / user study",data=lk_data)

features=Counter()
for val in study.iloc[:,18].fillna(""):
    features.update(s.strip() for s in str(val).split(";") if s.strip())
feature_df=pd.DataFrame(sorted(features.items(),key=lambda x:(-x[1],x[0])),columns=["future_capability","respondents_selecting"])
feature_data=save_data("coach_study_future_preferences",feature_df)
table("coach_study_future_preferences","Future-capability selections (n=6)",feature_df,[STUDY_ZIP,V89],
      "CSV column 18", "Four of six respondents selected comparison between players as a desired capability for a reliable future version.",
      "Multiple selections per respondent; counts do not sum to six. Preferences are not current system capabilities.","Evaluation / user study",derivation="Split semicolon-delimited choices; count respondents selecting each")
fig,ax=plt.subplots(figsize=(10,6))
ax.barh(feature_df.future_capability,feature_df.respondents_selecting,color=TEAL);ax.invert_yaxis()
ax.set_xlim(0,6);ax.set_xlabel("Respondents selecting (of 6)");ax.set_title("Requested future capabilities")
ax.grid(axis="x",alpha=.18);ax.set_axisbelow(True)
save_fig(fig,"05_evaluation/user_study/future_capabilities",title="Coach-study future-capability preferences",sources=[STUDY_ZIP,V89],
         fields="CSV column 18",derivation="Count multi-select choices across six responses",
         caption="Player comparison was the most selected future capability (4/6), but requires safe persistent identity before implementation.",
         caveat="Multiple-choice preferences, not validated product features or a representative population survey.",priority="high",placement="Evaluation / user study",data=feature_data)

profile=pd.DataFrame([(field,str(v),int(c)) for field,col in [("Role",3),("Experience",4),("Football level",5)]
                      for v,c in study.iloc[:,col].value_counts().items()],columns=["dimension","category","respondents"])
table("coach_study_profile","Coach-study participant profile",profile,[STUDY_ZIP,V89],
      "CSV columns 3–5", "The six participants included head coaches, assistant coaches, an analyst and a former player.",
      "Small stakeholder sample; no identifying response-level records included.","Evaluation / user study",derivation="Category counts")

# 7. Iterative design and scope/limitations assets.
shots=[
    ("before_report",ROOT/"docs/evaluation/coach_study_iteration/before_report.png","Pass 01 before: report"),
    ("after_report",ROOT/"docs/evaluation/coach_study_iteration/after_report.png","Pass 01 after: coach report"),
    ("before_showcase_plain_report",ROOT/"docs/evaluation/coach_study_iteration_pass02/before_showcase_plain_report.png","Pass 02 before: plain showcase report"),
    ("after_full_session_summary_rich_report",ROOT/"docs/evaluation/coach_study_iteration_pass02/after_full_session_summary_rich_report.png","Pass 02 after: full-session rich report"),
    ("after_c04_summary_rich_report",ROOT/"docs/evaluation/coach_study_iteration_pass02/after_c04_summary_rich_report.png","Pass 02 after: C04 rich report"),
    ("after_coach_overview",ROOT/"docs/evaluation/coach_study_iteration/after_coach_overview.png","Pass 01 after: coach overview")]
for name,source,title in shots:
    dest=PACK/"screenshots"/(name+".png")
    shutil.copyfile(source,dest)
    register(dest,title,"screenshot",[source],"Screenshot pixels; original file SHA in catalog","Unmodified copy",
             title+" from the recorded iterative-design evidence.",
             "UI evidence only; screenshot does not validate scientific accuracy.","medium","Iterative design")

def draw_iterations(ax):
    box(ax,.03,.43,.27,.32,"Study finding","withholding rationale 3.83/5\nreport clarity themes",BLUE)
    box(ax,.365,.43,.27,.32,"Pass 01","coach-first overview\nvideo event links",TEAL)
    box(ax,.70,.43,.27,.32,"Pass 02","rich report summary\nscoped technical detail",ORANGE)
    arrow(ax,.30,.59,.365,.59);arrow(ax,.635,.59,.70,.59)
    ax.text(.5,.17,"Recorded UI iterations respond to small-sample feedback; no new science claim",ha="center",color=GRAY,fontweight="bold")
diagram("06_iterative_design/feedback_to_ui_iterations","Coach feedback to UI revisions",draw_iterations,
        title="Iterative design rationale",sources=[STUDY_ZIP,V89,ROOT/"docs/evaluation/coach_study_iteration_pass02/after_full_session_summary_rich_report.png"],
        fields="study column 27 and qualitative themes; v89 §§148–150",derivation="Schematic only; 3.83 is mean from CSV",
        caption="The lowest-rated explanation item and qualitative readability feedback informed coach-first summaries and richer report presentation across two recorded passes.",
        caveat="No post-iteration repeat user study was recorded; do not claim measured usability improvement.",priority="high",placement="Iterative design")

limits=pd.DataFrame([
    ["Identity","Formal unsafe-merge gate fails for all methods","Player-level accumulated analytics withheld"],
    ["Calibration","Research homography is camera-specific","Phase 6 transport reports no metric measures"],
    ["Vision coverage","M3-v1 recall 0.3273","Low IDSW cannot imply safe tracking"],
    ["Full-session evidence","Six response windows lack tracking/visual observations","No player response invented"],
    ["Report generation","Phase 6 deterministic fallback","No claim of LLM report success on full run"],
    ["Presentation","No full-session overlay artifact","Use event navigation and scoped evidence"],
    ["Study","Six stakeholder responses","Descriptive findings only"]],columns=["boundary","observed_basis","reporting_consequence"])
table("limitations_matrix","Evidence and reporting limitations",limits,[E2E,V89,STUDY_ZIP],
      "v89 §138, §148, Phase 6 analysis", "The result is useful when evidence scope, missing data and failed safety gates remain visible.",
      "No row is an estimated metric or a claim that future work is currently implemented.","Limitations / future work",derivation="Qualitative synthesis of frozen status fields")

clip_protocol=load_json(G_PROTOCOL)
clip_table=pd.DataFrame([[c["id"],c["source_start"],c["source_end_inclusive"],c["frames"]] for c in clip_protocol["clips"]],
                        columns=["challenge_clip","source_start_frame","source_end_frame_inclusive","scored_frames_per_method"])
table("formal_clip_protocol","Frozen independent Vision challenge protocol",clip_table,[G_PROTOCOL,VISION_MANIFEST],
      "clips; state_contract; total_frames_per_method",
      "Each method ran on four independent fresh-state clips, totaling 3,780 scored frames per method.",
      "The full 20,391-frame session and M3 R2 are excluded from this formal comparison.",
      "Methodology / Vision",derivation="Direct protocol extraction")

model_manifest=load_json(VISION_MANIFEST)["external_authoritative_artifacts"]
models=pd.DataFrame([[key,model_manifest[key]["sha256"],model_manifest[key]["bytes"]]
                     for key in ["M1_detector","M1_ReID","M2_detector","M2_ReID","M3_detector","M3_ReID"]],
                    columns=["frozen_role","sha256","artifact_bytes"])
table("vision_checkpoint_provenance","Frozen Vision checkpoint provenance",models,[VISION_MANIFEST],
      "external_authoritative_artifacts SHA and bytes",
      "The formal comparison used specific frozen model artifacts; these hashes identify their checkpoint provenance.",
      "Manifest metadata is not a fresh hash verification of large checkpoint binaries in this report run.",
      "Methodology / Vision",priority="medium",derivation="Direct manifest fields; appendix candidate")

show=load_json(SHOWCASE)
show_df=pd.DataFrame([[c["id"],c["title"],show["showcase_mode"],"manually verified"] for c in show["cards"]],
                     columns=["case","coaching_scenario","evidence_mode","identity_and_target_scope"])
table("oracle_showcase_scope","Three frozen oracle-assisted showcase cases",show_df,[SHOWCASE,V89],
      "showcase_mode; cards; manual_verification",
      "C06 pressing, C04 defensive marking and C03 hold position demonstrate manually verified capabilities.",
      "Showcase evidence must never be presented as automated persistent-identity success or mixed with Phase 6 product evidence.",
      "Evaluation / showcase",derivation="Direct case labels and mode")

# Catalog, captions, placement map, source hashes, and machine-readable manifest.
main_report_titles={
    "System overview","Fail-closed identity gate","Vision method stacks","Fusion response window",
    "Calibration permission boundary","Official four-clip complete-system Vision evaluation",
    "Official HOTA, DetA and AssA","Distinct identity diagnostics","Frozen ASR candidate comparison",
    "LLM frozen formal selection evidence","Independent calibration residuals",
    "Phase 6 transport provenance","Measured Phase 6 worker components","Phase 6 full-session result",
    "Coach-study item means","Iterative design rationale","Evidence and reporting limitations",
    "Three frozen oracle-assisted showcase cases"}
appendix_titles={"Official Vision metrics by frozen challenge clip","Frozen Vision checkpoint provenance",
                 "Coach-study descriptive Likert summary (n=6)","Measured Phase 6 worker timings"}
for item in REG:
    item["priority"]="A" if item["title"] in main_report_titles else "C" if item["title"] in appendix_titles else "B"
    item["source_sha256"]={p:(sha(p) if Path(p).is_file() else None) for p in item["source_paths"]}
    item["asset_sha256"]={p:sha(PACK/p) for p in item["paths"]}
    if item["source_data"]: item["source_data_sha256"]=sha(PACK/item["source_data"])

catalog_csv=PACK/"00_catalog"/"REPORT_ASSET_CATALOG.csv"
cols=["id","title","kind","paths","source_paths","source_sha256","source_fields","source_data",
      "derived_calculation","caption","guardrail","priority","placement","asset_sha256"]
with catalog_csv.open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
    for item in REG:
        w.writerow({k:json.dumps(item[k],ensure_ascii=False) if isinstance(item.get(k),(dict,list)) else item.get(k,"") for k in cols})
cat=["# Report asset catalog","","Every path is relative to `docs/final_report_assets/`; source paths are absolute and read-only. Source SHA-256 hashes are recorded in the CSV/manifest. Numeric source-data extracts contain aggregates only.",""]
for item in REG:
    cat += [f"## {item['title']}","",f"- Files: {', '.join(item['paths'])}",
            f"- Source: {', '.join(item['source_paths'])}",f"- Fields: {item['source_fields']}",
            f"- Source SHA-256: {json.dumps(item['source_sha256'],ensure_ascii=False)}",
            f"- Calculation: {item['derived_calculation']}",f"- Data: {item['source_data'] or 'none (schematic/screenshot/table)'}",
            f"- Caption: {item['caption']}",f"- Guardrail: {item['guardrail']}",
            f"- Priority / placement: {item['priority']} / {item['placement']}",""]
(PACK/"00_catalog"/"REPORT_ASSET_CATALOG.md").write_text("\n".join(cat),encoding="utf-8")
captions=["# Suggested figure/table captions","","Captions are editable report snippets; preserve their guardrails.",""]
captions += [f"- **Priority {i['priority']} · {i['title']}** — {i['caption']} **Evidence:** {', '.join(Path(p).name for p in i['source_paths'])}. **Guardrail:** {i['guardrail']}" for i in REG]
(PACK/"00_catalog"/"REPORT_ASSET_CAPTIONS.md").write_text("\n".join(captions)+"\n",encoding="utf-8")
placements=["# Placement map","","Use high-priority assets first; avoid repeating adjacent views of the same data.",""]
for placement in dict.fromkeys(i["placement"] for i in REG):
    placements += ["## "+placement,""]
    placements += [f"- `{i['paths'][0]}` — {i['title']} (Priority {i['priority']}; {'essential' if i['priority']=='A' else 'optional/appendix'}). Supports: {i['caption']}" for i in REG if i["placement"]==placement]
    placements += [""]
(PACK/"00_catalog"/"REPORT_ASSET_PLACEMENT_MAP.md").write_text("\n".join(placements),encoding="utf-8")
manifest={"project":"AI-Driven Football Tactical Analysis and Training Evaluation System",
          "source_map":str(V89),"source_map_sha256":sha(V89),"study_csv_uncompressed_sha256":hashlib.sha256(study_bytes).hexdigest(),
          "asset_count":len(REG),"assets":REG,
          "research_drive_access_at_initial_generation":"Mounted after discovery; final Vision, ASR and LLM records reconciled directly on G drive",
          "research_safety":"Read-only inputs; no inference, retraining or research reruns."}
manifest_text=json.dumps(manifest,indent=2,ensure_ascii=False)+"\n"
(PACK/"provenance"/"REPORT_ASSET_MANIFEST.json").write_text(manifest_text,encoding="utf-8")
(PACK/"FINAL_REPORT_ASSET_PACK_MANIFEST.json").write_text(manifest_text,encoding="utf-8")
print(f"Generated {len(REG)} catalog entries, {sum(i['kind']=='figure' for i in REG)} vector+PNG figures, {sum(i['kind']=='table' for i in REG)} tables, {sum(i['kind']=='screenshot' for i in REG)} screenshots.")
