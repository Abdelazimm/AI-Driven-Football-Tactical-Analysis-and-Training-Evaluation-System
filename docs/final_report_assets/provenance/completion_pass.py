"""Add only completion-pass assets to the validated report pack.

Never invokes generate_assets.py or rewrites existing figure/table/screenshot files.
The original 41 asset hashes are checked before and after this one-time append.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle
import pandas as pd
from PIL import Image

PACK=Path(__file__).resolve().parent.parent
ROOT=PACK.parent.parent
RESEARCH=Path(r"G:\My Drive\Football_Training_Assistant_MVP")
MANIFEST=PACK/"FINAL_REPORT_ASSET_PACK_MANIFEST.json"
PREVIOUS=json.loads(MANIFEST.read_text(encoding="utf-8"))
if any(a.get("completion_pass") for a in PREVIOUS["assets"]):
    raise SystemExit("Completion pass already registered; existing files were not regenerated.")
assert PREVIOUS["asset_count"]==41

def digest(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):
            h.update(block)
    return h.hexdigest()

for asset in PREVIOUS["assets"]:
    for rel,expected in asset["asset_sha256"].items():
        assert digest(PACK/rel)==expected,rel

NAVY="#17324d"; BLUE="#2875a8"; TEAL="#16817a"; ORANGE="#d48325"; RED="#b94d4d"
GRAY="#607080"; LIGHT="#eef4f7"; PALE="#fafcff"
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"svg.fonttype":"none",
                     "figure.facecolor":"white","axes.spines.top":False,"axes.spines.right":False})
NEW=[]
def add(paths,title,kind,sources,fields,calculation,caption,guardrail,priority,placement,source_data=None,extra=None):
    paths=[Path(p) for p in paths]
    record={"id":paths[0].stem,"title":title,"kind":kind,
            "paths":[p.relative_to(PACK).as_posix() for p in paths],
            "source_paths":[str(Path(s)) for s in sources],"source_fields":fields,
            "derived_calculation":calculation,"caption":caption,"guardrail":guardrail,
            "priority":priority,"placement":placement,
            "source_data":source_data.relative_to(PACK).as_posix() if source_data else None,
            "completion_pass":True}
    record["source_sha256"]={str(Path(s)):digest(s) for s in sources}
    record["asset_sha256"]={p.relative_to(PACK).as_posix():digest(p) for p in paths}
    if source_data:record["source_data_sha256"]=digest(source_data)
    if extra:record.update(extra)
    NEW.append(record)

def save_fig(fig,rel,**metadata):
    stem=PACK/rel
    stem.parent.mkdir(parents=True,exist_ok=True)
    svg=stem.with_suffix(".svg");png=stem.with_suffix(".png")
    assert not svg.exists() and not png.exists(),f"Existing asset: {stem}"
    fig.savefig(svg,bbox_inches="tight",facecolor="white")
    fig.savefig(png,dpi=300,bbox_inches="tight",facecolor="white")
    plt.close(fig)
    add([svg,png],kind="figure",**metadata)

def node(ax,x,y,w,h,title,detail="",color=BLUE,fill=LIGHT,title_size=10):
    patch=FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.008,rounding_size=0.014",
                         linewidth=1.3,edgecolor=color,facecolor=fill)
    ax.add_patch(patch)
    ax.text(x+w/2,y+h*.63,title,ha="center",va="center",fontweight="bold",fontsize=title_size,color=NAVY)
    if detail:ax.text(x+w/2,y+h*.25,detail,ha="center",va="center",fontsize=8.3,color=GRAY,linespacing=1.2)

def arrow(ax,a,b,c,d,color=GRAY):
    ax.add_patch(FancyArrowPatch((a,b),(c,d),arrowstyle="-|>",mutation_scale=12,linewidth=1.25,color=color))

def canvas(title,width=13,height=6):
    fig,ax=plt.subplots(figsize=(width,height));ax.set_xlim(0,1);ax.set_ylim(0,1);ax.axis("off")
    ax.text(.025,.975,title,ha="left",va="top",fontsize=16,fontweight="bold",color=NAVY)
    return fig,ax

P0=ROOT/"docs/reproducibility/P0_ARCHITECTURE_CONTRACT_FREEZE_REV2A.json"
PKG=ROOT/"frontend/tactical-ai-insights-main/package.json"
API=ROOT/"backend/app/api/jobs.py"
MAIN=ROOT/"backend/app/main.py"
DISPATCH=ROOT/"backend/app/services/dispatch_service.py"
WORKER=ROOT/"modal_app/worker.py"
CALLBACK=ROOT/"backend/app/api/internal.py"
README=ROOT/"README.md"
ASR=ROOT/"backend/app/services/asr_service.py"
KIN=ROOT/"backend/app/services/kinematics_service.py"
CAL=ROOT/"backend/app/services/calibration_service.py"
ADAPTER=ROOT/"backend/app/adapters/common_adapter.py"
VISION=RESEARCH/"methodology_comparison/final_evaluation/whole_system_challenge_evaluation/FINAL_WHOLE_SYSTEM_AGGREGATE_METRICS.csv"
PROTOCOL=RESEARCH/"methodology_comparison/final_vision_evaluation/formal_fresh_state_per_clip/FORMAL_EXECUTION_PROTOCOL.json"
TRANSPORT=ROOT/"docs/phase6/IMPLEMENTATION_PHASE6_TRANSPORT_COPY_MANIFEST.json"

# Detailed product architecture: current application code, not stale planning documents.
fig,ax=canvas("Final product architecture: control, private storage, and compute",15,7.4)
for y,h,label,fc in [(.75,.18,"PRESENTATION", "#f2f8fc"),(.51,.20,"CONTROL PLANE","#f4f8f7"),
                     (.30,.17,"PRIVATE DATA", "#f9f7f1"),(.06,.20,"COMPUTE PLANE","#f8f4f4")]:
    ax.add_patch(Rectangle((.02,y),.96,h,facecolor=fc,edgecolor="none"))
    ax.text(.035,y+h-.026,label,color=GRAY,fontsize=9,fontweight="bold",va="top")
node(ax,.07,.785,.22,.105,"React + TanStack","upload / status / review",BLUE)
node(ax,.70,.785,.23,.105,"Results UI","scoped evidence + limitations",BLUE)
node(ax,.20,.55,.23,.115,"FastAPI control plane","validation / jobs / results",TEAL)
node(ax,.58,.55,.23,.115,"Job + dispatch","idempotent worker submission",TEAL)
node(ax,.07,.335,.31,.105,"Supabase database","sessions, jobs, dispatch, results",ORANGE)
node(ax,.62,.335,.31,.105,"Private storage","input media + output artifacts",ORANGE)
node(ax,.05,.095,.13,.105,"Modal worker","real full-session run",RED)
stages=[("Vision",.22,.12),("ASR",.365,.10),("Fusion",.49,.11),("Report + validator",.625,.17),("Persist",.83,.12)]
for label,x,w in stages:node(ax,x,.095,w,.105,label,"",RED,title_size=9)
for a,b,c,d in [(.29,.84,.30,.665),(.43,.61,.58,.61),(.20,.55,.20,.44),(.78,.55,.78,.44),
                (.70,.55,.14,.205),(.18,.147,.22,.147),(.34,.147,.365,.147),(.465,.147,.49,.147),
                (.60,.147,.625,.147),(.795,.147,.83,.147),(.89,.20,.78,.335),(.22,.335,.79,.785)]:
    arrow(ax,a,b,c,d)
ax.text(.5,.025,"Callbacks update job progress; completed results are served from persisted records",ha="center",fontsize=9,color=GRAY)
save_fig(fig,"02_design_architecture/detailed_product_architecture",
         title="Detailed final product architecture",sources=[PKG,MAIN,API,DISPATCH,CALLBACK,WORKER],
         fields="frontend dependencies; API job endpoints; dispatch; authenticated callback; worker flow",
         calculation="Schematic from implemented interfaces",caption="The final React/TanStack frontend uses a FastAPI control plane, private Supabase persistence and a Modal compute worker; results return through durable job state and scoped evidence.",
         guardrail="Diagram describes implemented product flow; the Phase 6 report still completed with identity/calibration limitations.",
         priority="A",placement="Requirements and Design / detailed architecture")

# Workspace/research responsibility boundary.
fig,ax=canvas("Product integration and frozen research have different authorities",13.2,5.9)
ax.add_patch(Rectangle((.03,.18),.39,.69,facecolor="#eef6fb",edgecolor=BLUE,linewidth=1.5))
ax.add_patch(Rectangle((.58,.18),.39,.69,facecolor="#f5f8f4",edgecolor=TEAL,linewidth=1.5))
ax.text(.225,.81,"D:  PRIMARY PRODUCT WORKSPACE",ha="center",fontweight="bold",color=BLUE)
ax.text(.775,.81,"G:  FROZEN RESEARCH · READ ONLY",ha="center",fontweight="bold",color=TEAL)
ax.text(.225,.65,"Frontend / FastAPI / Modal",ha="center",fontsize=12,color=NAVY)
ax.text(.225,.52,"Product schemas, contracts, tests",ha="center",fontsize=11,color=NAVY)
ax.text(.225,.39,"UI and persisted job results",ha="center",fontsize=11,color=NAVY)
ax.text(.775,.67,"Vision methods + formal evaluation",ha="center",fontsize=11,color=NAVY)
ax.text(.775,.54,"ASR and LLM model selection",ha="center",fontsize=11,color=NAVY)
ax.text(.775,.41,"Homography validation + frozen GT",ha="center",fontsize=11,color=NAVY)
arrow(ax,.57,.31,.43,.31,ORANGE)
ax.text(.5,.34,"controlled adaptation",ha="center",fontsize=9,color=ORANGE,fontweight="bold")
ax.text(.5,.10,"Research evidence is cited or adapted into product packages; source artifacts are never rerun or overwritten",ha="center",fontsize=9,color=RED)
save_fig(fig,"02_design_architecture/product_research_boundary",
         title="Product versus frozen research boundary",sources=[README,P0,VISION],
         fields="README research safety; P0 scientific invariants; direct final evaluation artifact",
         calculation="Schematic only",caption="The D: workspace owns product code and contracts, while the mounted G: workspace supplies frozen Vision, ASR, LLM, homography and formal-evaluation evidence through controlled read-only adaptation.",
         guardrail="The displayed absolute workspace paths are provenance labels, not application runtime dependencies.",
         priority="A",placement="Requirements and Design / research boundary")

# Coordinate policy with explicit example geometry and permission gate.
fig,ax=canvas("Coordinate spaces and conditional metric projection",14,6)
node(ax,.03,.65,.22,.18,"MEDIA_SOURCE_SPACE","probed resolution\n3840×2160 in research source",BLUE)
node(ax,.30,.65,.22,.18,"VISION_WORKING_SPACE","1920×1080 tracking plane",TEAL)
node(ax,.57,.65,.22,.18,"Vision observations","working-space bbox / tracks",TEAL)
node(ax,.31,.27,.25,.18,"Canonical source bbox","adapter scales by W/1920, H/1080",BLUE)
node(ax,.62,.27,.23,.18,"Bottom-centre footpoint","box-derived point",BLUE)
for a,b,c,d in [(.25,.74,.30,.74),(.52,.74,.57,.74),(.68,.65,.47,.45),(.56,.36,.62,.36)]:arrow(ax,a,b,c,d)
ax.text(.90,.56,"CALIBRATION\nPERMISSION GATE",ha="center",fontsize=9,fontweight="bold",color=RED)
arrow(ax,.85,.36,.91,.49,RED)
ax.text(.90,.26,"Metric pitch (m)\nonly if approved",ha="center",fontsize=9,color=RED)
ax.text(.5,.08,"Dynamic upload resolution; no automatic reuse of the research-camera homography",ha="center",color=RED,fontweight="bold")
save_fig(fig,"03_methodology/calibration/coordinate_space_flow",
         title="Coordinate-space and homography flow",sources=[P0,ADAPTER,CAL,TRANSPORT],
         fields="coordinate_spaces, adapter_coordinate_policy; calibration authorization; source probe",
         calculation="Schematic; 3840×2160 is the frozen research-source example",
         caption="Vision operates in a 1920×1080 working plane. Its working-space footpoints enter an approved homography for metric projection; adapters separately return bounding boxes to the dynamically probed source space.",
         guardrail="The 3840×2160 source is an example. Generic uploads do not inherit the camera-specific homography; the Phase 6 transport used no metric calibration.",
         priority="B",placement="Methodology / calibration")

# ASR frozen pipeline.
categories=json.loads(P0.read_text(encoding="utf-8"))["asr_contract"]["tactical_taxonomy"]["categories"]
assert categories==["Defensive","Offensive","Pressing","Passing","Positioning / Hold Ground"]
fig,ax=canvas("Frozen ASR to tactical-event pipeline",14,5.4)
asr_nodes=[("Coach audio","private source"),("16 kHz mono","PCM WAV"),("faster-whisper","base.en · CPU int8"),
           ("Transcript","timestamps retained"),("Exact trigger map","deterministic taxonomy"),("Tactical event","category + time")]
for i,(name,detail) in enumerate(asr_nodes):
    x=.025+i*.165;node(ax,x,.53,.145,.20,name,detail,[BLUE,BLUE,TEAL,TEAL,ORANGE,RED][i],title_size=9)
    if i<5:arrow(ax,x+.145,.63,x+.165,.63)
ax.text(.5,.36,"FIVE FROZEN CATEGORIES",ha="center",fontweight="bold",color=NAVY)
for i,name in enumerate(categories):
    x=.035+i*.19
    node(ax,x,.17,.175,.105,name,"",TEAL,title_size=8.4)
ax.text(.5,.065,"Unavailable audio yields explicit failure; no historical transcript fallback",ha="center",color=RED,fontsize=9)
save_fig(fig,"03_methodology/asr/asr_pipeline",title="Frozen ASR methodology pipeline",
         sources=[P0,ASR],fields="asr_contract engine/model/preprocessing/taxonomy; FROZEN_TACTICAL_CATEGORIES",
         calculation="Direct category transcription; schematic stages",
         caption="Coach audio is normalized to 16 kHz mono, transcribed with frozen faster-whisper base.en, and mapped deterministically into the five frozen tactical-event categories.",
         guardrail="A tactical event is an extracted instruction, not proof of the target player or observed response.",
         priority="B",placement="Methodology / ASR")

# Kinematics conditional path and exact exclusion semantics.
fig,ax=canvas("Conditional metric kinematics and exclusion rules",14,5.7)
knodes=[("Footpoint","tracked observation"),("Approved H","camera / geometry check"),("Pitch coordinate","metres only when allowed"),
        ("7-point median","within contiguous segment"),("Displacement","Δt = Δframes / probed FPS"),("Speed","km/h if valid")]
for i,(name,detail) in enumerate(knodes):
    x=.025+i*.165;node(ax,x,.55,.145,.20,name,detail,[BLUE,ORANGE,TEAL,TEAL,BLUE,RED][i],title_size=9)
    if i<5:arrow(ax,x+.145,.65,x+.165,.65)
node(ax,.08,.19,.36,.18,"Gap > 0.5 s","reset continuity; no interpolation",RED,"#fff3f3")
node(ax,.56,.19,.36,.18,"Speed > 36 km/h","reject and exclude; never clamp",RED,"#fff3f3")
ax.text(.5,.08,"Player-level metrics also require a passed persistent-identity safety gate",ha="center",color=RED,fontweight="bold")
save_fig(fig,"03_methodology/calibration/kinematics_pipeline",title="Metric kinematics safety pipeline",
         sources=[P0,KIN,CAL],fields="kinematics thresholds/median/outlier policy; service calculate_steps",
         calculation="Schematic only",caption="Metric movement derives from validated footpoints and approved homography, using seven-observation smoothing and actual probed FPS; gaps and implausible speeds are excluded.",
         guardrail="A >0.5 s gap resets continuity and >36 km/h is rejected, not clamped. No metric output under NO_METRIC_CALIBRATION or failed player identity.",
         priority="B",placement="Methodology / calibration")

# Product lifecycle from currently implemented endpoint/service states.
fig,ax=canvas("Product job lifecycle with durable progress and safe terminal states",14.2,6.2)
tops=[("Upload intent","private media"),("Validate media","probe / authority"),("Create session + job","method + calibration"),
      ("Idempotent dispatch","one active worker"),("Modal worker","real pipeline")]
for i,(name,detail) in enumerate(tops):
    x=.025+i*.195;node(ax,x,.60,.17,.18,name,detail,TEAL,title_size=9)
    if i<4:arrow(ax,x+.17,.69,x+.195,.69)
bottom=[("Progress callback","authenticated"),("Persist result","private artifacts"),("Results UI","read-only review")]
for i,(name,detail) in enumerate(bottom):node(ax,.23+i*.23,.25,.19,.17,name,detail,BLUE,title_size=9)
arrow(ax,.88,.60,.72,.42);arrow(ax,.42,.335,.46,.335);arrow(ax,.65,.335,.69,.335)
ax.text(.5,.12,"Terminal: COMPLETED  ·  COMPLETED_WITH_LIMITATIONS  ·  FAILED (explicit error)",ha="center",color=RED,fontweight="bold")
save_fig(fig,"04_implementation/product_job_lifecycle",title="Implemented product job lifecycle",
         sources=[API,DISPATCH,CALLBACK,WORKER,MAIN],
         fields="media validation/job creation/start/status/results; active-dispatch idempotency; worker callback terminal handling",
         calculation="Schematic only",caption="Validated private media enters a session/job, is dispatched idempotently to Modal, and returns authenticated progress plus persisted results for review.",
         guardrail="COMPLETED_WITH_LIMITATIONS is a successful fail-closed outcome; FAILED carries an explicit error. Diagram does not imply every upload or run succeeds.",
         priority="B",placement="Implementation / job lifecycle")

# Complementary aggregate outcome chart.
vision=pd.read_csv(VISION)
assert list(vision.method)==["method_1","method_2","method_3"]
vision["method"]=["M1","M2","M3-v1"]
fig,ax=plt.subplots(figsize=(9,5))
colors=[BLUE,TEAL,ORANGE]
for j,col in enumerate(["HOTA","MOTA","IDF1"]):
    ax.bar([i+(j-1)*.25 for i in range(3)],vision[col],.25,color=colors[j],label=col)
ax.set_xticks(range(3),vision.method);ax.set_ylim(0,1.07)
ax.set_ylabel("Official complete-system score (0–1)");ax.set_title("Key frozen Vision outcomes across four clips")
ax.legend(ncol=3);ax.grid(axis="y",alpha=.18);ax.set_axisbelow(True)
ax.text(.5,-.19,"Every method failed formal persistent-identity safety",transform=ax.transAxes,ha="center",color=RED,fontweight="bold")
save_fig(fig,"05_evaluation/vision/key_outcome_metrics",title="Key Vision outcome metrics",
         sources=[VISION],fields="COMBINED_SEQ HOTA, MOTA, IDF1",calculation="Direct plotting of frozen aggregate rows",
         caption="M2 led the frozen four-clip complete-system comparison on HOTA, MOTA and IDF1; all three methods nevertheless failed the formal identity-safety gate.",
         guardrail="Project-specific challenge protocol; MOTA and IDF1 are not permission for player-level accumulated analytics.",
         priority="B",placement="Evaluation / Vision",source_data=PACK/"source_data/vision_formal_aggregate.csv")

# Clip positions on the original source-session timebase; primary labels retain exact frame ranges.
proto=json.loads(PROTOCOL.read_text(encoding="utf-8"))
probe=json.loads(TRANSPORT.read_text(encoding="utf-8"))["authoritative_research_source"]["probe"]
video=next(s for s in probe["streams"] if s.get("codec_type")=="video")
num,den=map(int,video["avg_frame_rate"].split("/"));fps=num/den
assert abs(fps-59.972)<.01
rows=[]
for c in proto["clips"]:
    rows.append([c["id"],c["source_start"],c["source_end_inclusive"],c["frames"],
                 c["source_start"]/fps,(c["source_end_inclusive"]+1)/fps])
clip_df=pd.DataFrame(rows,columns=["clip","source_start_frame","source_end_frame_inclusive","scored_frames","start_s","end_exclusive_s"])
clip_data=PACK/"source_data/completion_formal_clip_timeline.csv"
assert not clip_data.exists()
clip_df.to_csv(clip_data,index=False)
fig,ax=plt.subplots(figsize=(10,4.8))
labels=["Re-entry","Occlusion","Same-team interaction","Long-gap re-entry"]
for i,r in clip_df.iterrows():
    ax.barh(i,r.end_exclusive_s-r.start_s,left=r.start_s,height=.56,color=[BLUE,TEAL,ORANGE,RED][i])
    ax.text(r.end_exclusive_s+2,i,f"{r.source_start_frame}–{r.source_end_frame_inclusive}",
            ha="left",va="center",color=NAVY,fontsize=8.5,fontweight="bold")
ax.set_yticks(range(4),labels);ax.invert_yaxis();ax.set_xlim(0,390)
ax.set_xlabel("Original research-session time (s), derived from probed FPS")
ax.set_title("Four frozen independent challenge clips")
ax.text(.5,-.22,"Fresh tracker state per clip · 3,780 scored frames per method",transform=ax.transAxes,ha="center",color=RED,fontweight="bold")
ax.grid(axis="x",alpha=.16);ax.set_axisbelow(True)
save_fig(fig,"03_methodology/vision/formal_clip_timeline",title="Frozen challenge clip timeline",
         sources=[PROTOCOL,TRANSPORT],fields="clips source_start/end/frames; source avg_frame_rate",
         calculation="start_s=start_frame/(3058650/51001); end_exclusive_s=(end_frame+1)/fps",
         caption="The four formal challenge clips occupy distinct positions in the research session and were evaluated with fresh tracker state for 3,780 frames per method.",
         guardrail="This is not a continuous full-session TrackEval run; the Phase 6 transport is excluded from the formal benchmark.",
         priority="B",placement="Methodology / Vision",source_data=clip_data)

# Small-n Likert distributions reveal the counts hidden behind item means.
likert_path=PACK/"source_data/coach_study_likert_aggregates.csv"
lk=pd.read_csv(likert_path).set_index("item")
selected=["Overall usefulness","Report useful","Limitations clear","Withholding explanation","Real-training potential"]
counts=lk.loc[selected,[f"rating_{i}" for i in range(1,6)]]
assert all(counts.sum(axis=1)==6)
fig,ax=plt.subplots(figsize=(10,4.7))
palette=["#b94d4d","#d98b53","#c4cbd0","#65a79e","#16817a"]
left=[0]*len(selected)
for j,c in enumerate(counts.columns):
    values=counts[c].to_list()
    ax.barh(selected,values,left=left,color=palette[j],label=str(j+1),height=.68)
    for i,v in enumerate(values):
        if v:ax.text(left[i]+v/2,i,str(v),ha="center",va="center",fontsize=9,color="white" if j in [0,4] else NAVY,fontweight="bold")
    left=[left[i]+values[i] for i in range(len(left))]
ax.invert_yaxis();ax.set_xlim(0,6);ax.set_xlabel("Respondents (n=6)")
ax.set_title("Selected coach-study response distributions")
ax.legend(title="Rating 1–5",ncol=5,loc="upper center",bbox_to_anchor=(.5,-.17))
save_fig(fig,"05_evaluation/user_study/key_likert_distribution",title="Selected coach-study Likert distributions",
         sources=[likert_path,Path(r"C:\Users\Abdelazim\Downloads\AI-Driven Football Tactical Analysis and Training Evaluation System — Prototype Evaluation.csv.zip")],
         fields="rating_1..rating_5 for five selected items; hash-matched original responses",
         calculation="Stack six integer response counts per item; no inferential statistics",
         caption="Five report-relevant items show their full six-response distributions, including the two neutral ratings for the withholding explanation.",
         guardrail="Small descriptive stakeholder sample (n=6); selection highlights interpretability and is not a population estimate.",
         priority="B",placement="User Study / response detail",source_data=likert_path)

# UI composites: panels are crops of real browser/recorded application screenshots.
HOME=PACK/"screenshots/completion_home_current.png"
OVERVIEW=ROOT/"docs/evaluation/coach_study_iteration/after_coach_overview.png"
EVENTS=ROOT/"docs/evaluation/coach_study_iteration/after_events.png"
VIDEO=ROOT/"docs/evaluation/coach_study_iteration/after_video_early_26.54s.png"
REPORT=ROOT/"docs/evaluation/coach_study_iteration_pass02/after_full_session_summary_rich_report.png"
SHOW=[ROOT/f"docs/evaluation/coach_study_iteration/after_showcase_{c}.png" for c in ("c03","c04","c06")]
assert HOME.is_file()
add([HOME],"Current homepage browser capture","screenshot",[HOME,PKG],
    "localhost:8081 homepage screenshot and current frontend dependency manifest","Unmodified 464-pixel browser viewport capture",
    "Current homepage shows the official project title and navigation to the validated full-session result and showcase.",
    "Mobile-width viewport; this capture is UI evidence, not a scientific result.","B","Implementation / UI capture",
    extra={"capture_url":"http://127.0.0.1:8081/","capture_method":"Codex in-app browser screenshot"})

def panel(ax,path,bounds,label):
    im=Image.open(path).convert("RGB")
    if bounds:
        x0,y0,x1,y1=bounds
        assert x1<=im.width and y1<=im.height,(path,im.size,bounds)
        im=im.crop(bounds)
    ax.imshow(im);ax.set_xticks([]);ax.set_yticks([])
    for spine in ax.spines.values():spine.set_visible(True);spine.set_color("#c9d5da")
    ax.set_title(label,loc="left",fontweight="bold",fontsize=10,color=NAVY,pad=8)

def composite(rel,title,panels,sources,caption,guardrail,priority,placement):
    dest=PACK/rel;dest.parent.mkdir(parents=True,exist_ok=True)
    assert not dest.exists(),dest
    fig,axes=plt.subplots(1,3,figsize=(12,6.5),facecolor="white")
    fig.suptitle(title,fontsize=16,fontweight="bold",color=NAVY)
    for ax,(p,bounds,label) in zip(axes,panels):panel(ax,p,bounds,label)
    fig.subplots_adjust(left=.02,right=.98,top=.87,bottom=.08,wspace=.10)
    fig.savefig(dest,dpi=300,facecolor="white",bbox_inches="tight")
    plt.close(fig)
    add([dest],title,"composite",sources,"Source screenshot pixels and recorded UI context",
        "Crop and panel arrangement only; no UI content fabricated",caption,guardrail,priority,placement,
        extra={"panel_sources":[str(p) for p,_,_ in panels]})

composite("04_implementation/final_ui_workflow.png","Final UI workflow: entry to tactical events",
          [(HOME,None,"A · Home"),(OVERVIEW,(0,0,476,900),"B · Coach overview"),
           (EVENTS,(0,900,476,1800),"C · Tactical events")],
          [HOME,OVERVIEW,EVENTS],
          "Actual current homepage and recorded final coach-overview/event captures show navigation from entry to scoped full-session evidence.",
          "Panels B/C are recorded Pass 01 final-iteration screenshots; mobile-width captures and crops, not fresh backend execution.",
          "A","Implementation / final UI")

# Evidence-review A uses two separate real screenshots without exposing the private video frame.
fig,axes=plt.subplots(1,3,figsize=(12,6.5),facecolor="white")
fig.suptitle("Final UI evidence review and reporting",fontsize=16,fontweight="bold",color=NAVY)
panel(axes[0],EVENTS,(0,980,476,1560),"A · Event → video action")
panel(axes[1],OVERVIEW,(0,250,476,800),"B · Identity safety")
panel(axes[2],REPORT,None,"C · Rich report / provenance")
fig.subplots_adjust(left=.02,right=.98,top=.87,bottom=.08,wspace=.10)
review=PACK/"04_implementation/final_ui_evidence_review.png"
assert not review.exists()
fig.savefig(review,dpi=300,facecolor="white",bbox_inches="tight");plt.close(fig)
add([review],"Final UI evidence review","composite",[EVENTS,OVERVIEW,REPORT,VIDEO],
    "recorded event navigation, withheld identity and Pass 02 rich report screenshots",
    "Crop and panel arrangement only; private video frame omitted",
    "Recorded final UI shows event-to-video navigation, explicit identity withholding and report/provenance presentation.",
    "Recorded UI evidence only; the rich-report panel includes technical provenance and does not claim a new usability measurement.",
    "B","Implementation / final UI",extra={"panel_sources":[str(EVENTS),str(OVERVIEW),str(REPORT)]})

# Case captions are supplied as labels, but all visible UI pixels come from frozen screenshots.
composite("05_evaluation/showcase/showcase_cases.png",
          "MANUALLY VERIFIED / ORACLE-ASSISTED CAPABILITY DEMONSTRATION",
          [(SHOW[0],(0,600,476,1500),"C03 · Hold Position"),
           (SHOW[1],(0,600,476,1500),"C04 · Defensive Marking"),
           (SHOW[2],(0,600,476,1500),"C06 · Pressing Response")],SHOW,
          "The frozen C03, C04 and C06 showcase cases use manually verified identity, targets and tactical meaning; the panels are real recorded UI captures.",
          "Oracle-assisted capability examples are distinct from automated full-session analysis and do not establish safe persistent identity.",
          "A","Evaluation / showcase")

# Append metadata only; do not rebuild the prior pack.
assert len(NEW)==13,len(NEW)
original_count=len(PREVIOUS["assets"])
PREVIOUS["assets"].extend(NEW)
PREVIOUS["asset_count"]=len(PREVIOUS["assets"])
PREVIOUS["completion_pass"]={"added_entries":len(NEW),"original_entries_preserved":original_count,
                            "excluded_as_redundant":[],"new_inference":False}

catalog_csv=PACK/"00_catalog/REPORT_ASSET_CATALOG.csv"
with catalog_csv.open("r",encoding="utf-8",newline="") as f:headers=next(csv.reader(f))
with catalog_csv.open("a",encoding="utf-8",newline="") as f:
    w=csv.DictWriter(f,fieldnames=headers)
    for item in NEW:
        w.writerow({k:json.dumps(item[k],ensure_ascii=False) if isinstance(item.get(k),(list,dict)) else item.get(k,"") for k in headers})

catalog_md=PACK/"00_catalog/REPORT_ASSET_CATALOG.md"
with catalog_md.open("a",encoding="utf-8") as f:
    f.write("\n# Completion pass additions\n\n")
    for i in NEW:
        f.write(f"## {i['title']}\n\n- Files: {', '.join(i['paths'])}\n"
                f"- Source: {', '.join(i['source_paths'])}\n"
                f"- Source SHA-256: {json.dumps(i['source_sha256'],ensure_ascii=False)}\n"
                f"- Fields: {i['source_fields']}\n- Calculation: {i['derived_calculation']}\n"
                f"- Data: {i['source_data'] or 'none (schematic/screenshot/composite)'}\n"
                f"- Caption: {i['caption']}\n- Guardrail: {i['guardrail']}\n"
                f"- Priority / placement: {i['priority']} / {i['placement']}\n\n")

captions=PACK/"00_catalog/REPORT_ASSET_CAPTIONS.md"
with captions.open("a",encoding="utf-8") as f:
    f.write("\n## Completion pass\n\n")
    for i in NEW:
        f.write(f"- **Priority {i['priority']} · {i['title']}** — {i['caption']} "
                f"**Evidence:** {', '.join(Path(p).name for p in i['source_paths'])}. "
                f"**Guardrail:** {i['guardrail']}\n")

placement=PACK/"00_catalog/REPORT_ASSET_PLACEMENT_MAP.md"
with placement.open("a",encoding="utf-8") as f:
    f.write("\n# Completion pass placements\n\n")
    for i in NEW:
        f.write(f"- **{i['placement']}** — `{i['paths'][0]}` (Priority {i['priority']}; "
                f"{'essential' if i['priority']=='A' else 'optional'}). Supports: {i['caption']}\n")

text=json.dumps(PREVIOUS,indent=2,ensure_ascii=False)+"\n"
MANIFEST.write_text(text,encoding="utf-8")
(PACK/"provenance/REPORT_ASSET_MANIFEST.json").write_text(text,encoding="utf-8")

for asset in PREVIOUS["assets"][:original_count]:
    for rel,expected in asset["asset_sha256"].items():
        assert digest(PACK/rel)==expected,rel
print(f"Added {len(NEW)} entries; original {original_count} asset entries remain byte-for-byte unchanged. Total {len(PREVIOUS['assets'])}.")
