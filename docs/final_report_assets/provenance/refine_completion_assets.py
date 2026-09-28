"""Refine only newly added completion-pass visuals after visual inspection."""
from pathlib import Path
import csv,hashlib,json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,FancyBboxPatch,FancyArrowPatch
from PIL import Image

PACK=Path(__file__).resolve().parent.parent
ROOT=PACK.parent.parent
NAVY="#17324d";BLUE="#2875a8";TEAL="#16817a";ORANGE="#d48325";RED="#b94d4d";GRAY="#607080"
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"svg.fonttype":"none","figure.facecolor":"white"})

def figax(title,w=14,h=6):
    fig,ax=plt.subplots(figsize=(w,h));ax.set_xlim(0,1);ax.set_ylim(0,1);ax.axis("off")
    ax.text(.025,.975,title,ha="left",va="top",fontsize=16,fontweight="bold",color=NAVY)
    return fig,ax
def box(ax,x,y,w,h,title,detail="",color=BLUE,fc="#eef4f7",ts=10):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.007,rounding_size=0.012",linewidth=1.25,edgecolor=color,facecolor=fc))
    ax.text(x+w/2,y+h*.63,title,ha="center",va="center",fontweight="bold",fontsize=ts,color=NAVY)
    if detail:ax.text(x+w/2,y+h*.25,detail,ha="center",va="center",fontsize=8.2,color=GRAY,linespacing=1.2)
def arrow(ax,x1,y1,x2,y2,color=GRAY):
    ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle="-|>",mutation_scale=12,linewidth=1.25,color=color))
def save(fig,rel):
    p=PACK/rel
    fig.savefig(p.with_suffix(".svg"),bbox_inches="tight",facecolor="white")
    fig.savefig(p.with_suffix(".png"),dpi=300,bbox_inches="tight",facecolor="white")
    plt.close(fig)

# Clean swimlanes with orthogonal control path and contained Modal stages.
fig,ax=figax("Final product architecture: control, private storage, and compute",15,7.4)
for y,h,label,fc in [(.76,.15,"PRESENTATION","#f2f8fc"),(.55,.15,"CONTROL PLANE","#f4f8f7"),
                     (.36,.13,"PRIVATE DATA","#f9f7f1"),(.07,.24,"COMPUTE PLANE","#f8f4f4")]:
    ax.add_patch(Rectangle((.02,y),.96,h,facecolor=fc,edgecolor="none"))
    ax.text(.035,y+h+.005,label,color=GRAY,fontsize=9,fontweight="bold",va="bottom")
box(ax,.08,.79,.22,.09,"React + TanStack","upload / status / review",BLUE)
box(ax,.70,.79,.23,.09,"Results UI","GET result via FastAPI",BLUE)
box(ax,.13,.57,.24,.10,"FastAPI control plane","validation / jobs / result endpoints",TEAL)
box(ax,.65,.57,.25,.10,"Job + dispatch","idempotent worker submission",TEAL)
box(ax,.13,.38,.27,.08,"Supabase database","sessions / jobs / results",ORANGE,ts=9)
box(ax,.61,.38,.29,.08,"Private storage","media + output artifacts",ORANGE,ts=9)
arrow(ax,.19,.79,.19,.67)
arrow(ax,.37,.62,.65,.62)
arrow(ax,.25,.57,.25,.46)
ax.plot([.90,.96,.96],[.62,.62,.34],color=GRAY,linewidth=1.2)
arrow(ax,.96,.34,.96,.31)
ax.plot([.37,.46,.46,.70],[.67,.67,.835,.835],color=GRAY,linewidth=1.2)
arrow(ax,.66,.835,.70,.835,color=GRAY)
ax.text(.49,.85,"read persisted result",ha="center",fontsize=8,color=GRAY)
ax.add_patch(Rectangle((.035,.09),.93,.20,fill=False,edgecolor=RED,linewidth=1.4))
ax.text(.05,.275,"MODAL WORKER",fontsize=9,fontweight="bold",color=RED,va="top")
stages=[("Vision",.055,.12),("ASR",.205,.10),("Fusion",.335,.11),
        ("Report + validator",.475,.20),("Validated / fallback",.705,.17),("Persist",.89,.065)]
for name,x,w in stages:box(ax,x,.13,w,.09,name,"",RED,ts=8.2)
for a,b in [(.175,.205),(.305,.335),(.445,.475),(.675,.705),(.875,.89)]:arrow(ax,a,.175,b,.175)
arrow(ax,.92,.22,.79,.38)
ax.text(.5,.025,"Worker callbacks update progress; private outputs are served through the FastAPI result path",ha="center",fontsize=9,color=GRAY)
save(fig,"02_design_architecture/detailed_product_architecture")

# Working-space footpoints go directly to the permission-gated homography.
fig,ax=figax("Coordinate spaces and conditional metric projection",14,5.9)
items=[("Media source\nspace","dynamic probe\n3840×2160 example",BLUE),
       ("Vision working\nspace","1920×1080",TEAL),
       ("Working-space tracks","bbox / observations",TEAL),
       ("Bottom-centre footpoint","working-space pixel",BLUE),
       ("Approved homography","camera + geometry gate",ORANGE),
       ("Pitch coordinates","metres if permitted",RED)]
for i,(name,detail,color) in enumerate(items):
    x=.02+i*.164
    box(ax,x,.51,.14,.20,name,detail,color,ts=8.2)
    if i<5:arrow(ax,x+.14,.61,x+.164,.61)
box(ax,.34,.20,.32,.15,"Canonical source bbox","adapter scales x by W/1920 and y by H/1080",BLUE,ts=9)
arrow(ax,.43,.51,.43,.35)
ax.text(.5,.075,"Generic uploads never inherit the research-camera homography; Phase 6 transport had no metric calibration",ha="center",color=RED,fontweight="bold",fontsize=9)
save(fig,"03_methodology/calibration/coordinate_space_flow")

def six_boxes(rel,title,items,colors,notes):
    fig,ax=figax(title,14,5.5)
    for i,(name,detail) in enumerate(items):
        x=.02+i*.16
        box(ax,x,.54,.14,.19,name,detail,colors[i],ts=8.7)
        if i<5:arrow(ax,x+.14,.635,x+.16,.635)
    notes(ax)
    save(fig,rel)

def asr_notes(ax):
    ax.text(.5,.38,"FIVE FROZEN CATEGORIES",ha="center",fontweight="bold",color=NAVY)
    for i,name in enumerate(["Defensive","Offensive","Pressing","Passing","Positioning / Hold Ground"]):
        box(ax,.03+i*.19,.19,.175,.105,name,"",TEAL,ts=8.2)
    ax.text(.5,.07,"Unavailable audio yields explicit failure; no historical transcript fallback",ha="center",color=RED,fontsize=9)
six_boxes("03_methodology/asr/asr_pipeline","Frozen ASR to tactical-event pipeline",
          [("Coach audio","private source"),("16 kHz mono","PCM WAV"),("faster-whisper","base.en · CPU int8"),
           ("Transcript","timestamps retained"),("Exact trigger map","deterministic taxonomy"),("Tactical event","category + time")],
          [BLUE,BLUE,TEAL,TEAL,ORANGE,RED],asr_notes)

def kin_notes(ax):
    box(ax,.08,.19,.36,.16,"Gap > 0.5 s","reset continuity; no interpolation",RED,"#fff3f3")
    box(ax,.56,.19,.36,.16,"Speed > 36 km/h","reject and exclude; never clamp",RED,"#fff3f3")
    ax.text(.5,.065,"Player-level metrics also require a passed persistent-identity safety gate",ha="center",color=RED,fontweight="bold",fontsize=9)
six_boxes("03_methodology/calibration/kinematics_pipeline","Conditional metric kinematics and exclusion rules",
          [("Footpoint","tracked observation"),("Approved H","camera / geometry check"),("Pitch coordinate","metres only when allowed"),
           ("7-point median","contiguous segment"),("Displacement","Δt = Δframes / probed FPS"),("Speed","km/h if valid")],
          [BLUE,ORANGE,TEAL,TEAL,BLUE,RED],kin_notes)

fig,ax=figax("Product job lifecycle with durable progress and safe terminal states",14.2,6.1)
tops=[("Upload intent","private media"),("Validate media","probe / authority"),("Create session + job","method + calibration"),
      ("Idempotent dispatch","one active worker"),("Modal worker","real pipeline")]
for i,(name,detail) in enumerate(tops):
    x=.025+i*.195;box(ax,x,.59,.17,.18,name,detail,TEAL,ts=9)
    if i<4:arrow(ax,x+.17,.68,x+.195,.68)
box(ax,.70,.25,.20,.17,"Progress callback","authenticated",BLUE)
box(ax,.43,.25,.20,.17,"Persist result","private artifacts",BLUE)
box(ax,.16,.25,.20,.17,"Results UI","read-only review",BLUE)
arrow(ax,.86,.59,.80,.42)
arrow(ax,.70,.335,.63,.335)
arrow(ax,.43,.335,.36,.335)
ax.text(.5,.10,"Terminal: COMPLETED  ·  COMPLETED_WITH_LIMITATIONS  ·  FAILED (explicit error)",ha="center",color=RED,fontweight="bold")
save(fig,"04_implementation/product_job_lifecycle")

# Put exact frame ranges beside short timeline bars so no digits are clipped.
with (PACK/"source_data/completion_formal_clip_timeline.csv").open(encoding="utf-8",newline="") as f:
    clip_rows=list(csv.DictReader(f))
assert len(clip_rows)==4
fig,ax=plt.subplots(figsize=(10,4.8))
labels=["Re-entry","Occlusion","Same-team interaction","Long-gap re-entry"]
for i,r in enumerate(clip_rows):
    start=float(r["start_s"]);end=float(r["end_exclusive_s"])
    ax.barh(i,end-start,left=start,height=.56,color=[BLUE,TEAL,ORANGE,RED][i])
    ax.text(end+2,i,f'{r["source_start_frame"]}–{r["source_end_frame_inclusive"]}',
            ha="left",va="center",color=NAVY,fontsize=8.5,fontweight="bold")
ax.set_yticks(range(4),labels);ax.invert_yaxis();ax.set_xlim(0,390)
ax.set_xlabel("Original research-session time (s), derived from probed FPS")
ax.set_title("Four frozen independent challenge clips")
ax.text(.5,-.22,"Fresh tracker state per clip · 3,780 scored frames per method",
        transform=ax.transAxes,ha="center",color=RED,fontweight="bold")
ax.grid(axis="x",alpha=.16);ax.set_axisbelow(True)
save(fig,"03_methodology/vision/formal_clip_timeline")

# Replace two completion-only composites with more focused real screenshot crops.
EVENTS=ROOT/"docs/evaluation/coach_study_iteration/after_events.png"
OVERVIEW=ROOT/"docs/evaluation/coach_study_iteration/after_coach_overview.png"
REPORT=ROOT/"docs/evaluation/coach_study_iteration_pass02/after_full_session_summary_rich_report.png"
SHOW=[ROOT/f"docs/evaluation/coach_study_iteration/after_showcase_{c}.png" for c in ("c03","c04","c06")]
def panel(ax,p,bounds,label):
    im=Image.open(p).convert("RGB").crop(bounds)
    ax.imshow(im);ax.set_xticks([]);ax.set_yticks([])
    for sp in ax.spines.values():sp.set_visible(True);sp.set_color("#c9d5da")
    ax.set_title(label,loc="left",fontweight="bold",fontsize=10,color=NAVY,pad=8)
def composite(rel,title,panels,h=6.5):
    fig,axes=plt.subplots(1,3,figsize=(12,h),facecolor="white")
    fig.suptitle(title,fontsize=16,fontweight="bold",color=NAVY)
    for ax,(p,b,label) in zip(axes,panels):panel(ax,p,b,label)
    fig.subplots_adjust(left=.02,right=.98,top=.87,bottom=.08,wspace=.10)
    fig.savefig(PACK/rel,dpi=300,facecolor="white",bbox_inches="tight");plt.close(fig)
composite("04_implementation/final_ui_evidence_review.png","Final UI evidence review and reporting",
          [(EVENTS,(0,1080,476,1660),"A · Event → video action"),
           (OVERVIEW,(0,250,476,800),"B · Identity safety"),
           (REPORT,(0,0,459,450),"C · Summary / rich report")])
composite("05_evaluation/showcase/showcase_cases.png",
          "MANUALLY VERIFIED / ORACLE-ASSISTED CAPABILITY DEMONSTRATION",
          [(SHOW[0],(0,1700,476,2030),"C03 · Hold Position"),
           (SHOW[1],(0,2850,476,3180),"C04 · Defensive Marking"),
           (SHOW[2],(0,1700,476,1990),"C06 · Pressing Response")],h=4.8)

manifest_path=PACK/"FINAL_REPORT_ASSET_PACK_MANIFEST.json"
d=json.loads(manifest_path.read_text(encoding="utf-8"))
updated={
    "02_design_architecture/detailed_product_architecture.svg",
    "03_methodology/calibration/coordinate_space_flow.svg",
    "03_methodology/asr/asr_pipeline.svg",
    "03_methodology/calibration/kinematics_pipeline.svg",
    "04_implementation/product_job_lifecycle.svg",
    "03_methodology/vision/formal_clip_timeline.svg",
    "04_implementation/final_ui_evidence_review.png",
    "05_evaluation/showcase/showcase_cases.png"}
for a in d["assets"]:
    if a["paths"][0] in updated:
        for rel in a["paths"]:a["asset_sha256"][rel]=hashlib.sha256((PACK/rel).read_bytes()).hexdigest()
text=json.dumps(d,indent=2,ensure_ascii=False)+"\n"
manifest_path.write_text(text,encoding="utf-8")
(PACK/"provenance/REPORT_ASSET_MANIFEST.json").write_text(text,encoding="utf-8")
catalog_path=PACK/"00_catalog/REPORT_ASSET_CATALOG.csv"
with catalog_path.open(encoding="utf-8",newline="") as f:
    reader=csv.DictReader(f);fieldnames=reader.fieldnames;catalog=list(reader)
asset_by_id={a["id"]:a for a in d["assets"]}
for row in catalog:
    asset=asset_by_id[row["id"]]
    if asset["paths"][0] in updated:
        row["asset_sha256"]=json.dumps(asset["asset_sha256"],ensure_ascii=False)
with catalog_path.open("w",encoding="utf-8",newline="") as f:
    writer=csv.DictWriter(f,fieldnames=fieldnames);writer.writeheader();writer.writerows(catalog)
print("Refined eight completion-pass entries; original asset files remain unchanged.")
