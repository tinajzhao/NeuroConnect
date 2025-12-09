
from shiny import App, ui, render, reactive
from shinywidgets import output_widget, render_plotly
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import io
from pathlib import Path

# Optional heavy deps for realistic MNI surface
try:
    import nibabel as nib
    from templateflow.api import get as tflow_get
    from skimage.measure import marching_cubes
    HAVE_NEURO = True
except Exception:
    HAVE_NEURO = False

APP_TITLE = "🧠 NeuroConnect"

RX, RY, RZ = 90, 120, 80  # ellipsoid radii (mm)

# ---------------------------
# Data helpers
# ---------------------------
def sample_points_in_ellipsoid(n, rx, ry, rz, seed=2025):
    rng = np.random.default_rng(seed)
    pts = []
    while len(pts) < n:
        xyz = rng.uniform([-rx, -ry, -rz], [rx, ry, rz])
        if (xyz[0]**2)/(rx**2) + (xyz[1]**2)/(ry**2) + (xyz[2]**2)/(rz**2) <= 1:
            pts.append(xyz)
    return np.array(pts)

def generate_demo_nodes(n_nodes=120, n_groups=4, seed=2025, with_values=True):
    pts = sample_points_in_ellipsoid(n_nodes, RX*0.9, RY*0.9, RZ*0.9, seed=seed)
    rng = np.random.default_rng(seed)
    df = pd.DataFrame(pts, columns=["x","y","z"])
    df["id"] = [f"Node_{i:03d}" for i in range(n_nodes)]
    df["group"] = rng.integers(1, n_groups+1, size=n_nodes).astype(str)
    if with_values:
        df["value"] = rng.random(n_nodes)  # synthetic value in [0,1]
    return df

def normalize_columns(df):
    cols = {c.lower().strip(): c for c in df.columns}
    required = ["x","y","z"]
    for r in required:
        if r not in cols:
            raise ValueError(f"Missing required column: {r}")
    df = df.rename(columns={cols["x"]:"x", cols["y"]:"y", cols["z"]:"z"})
    if "id" in cols: df = df.rename(columns={cols["id"]:"id"})
    else: df["id"] = [f"node_{i}" for i in range(len(df))]
    if "group" in cols: df = df.rename(columns={cols["group"]:"group"})
    else: df["group"] = "1"
    if "value" in cols: df = df.rename(columns={cols["value"]:"value"})
    return df.dropna(subset=["x","y","z"]).reset_index(drop=True)

def mark_nearest(nodes_df, targets_xyz, radius_mm=8.0):
    pts = nodes_df[["x","y","z"]].to_numpy()
    sel = np.zeros(len(nodes_df), dtype=bool)
    for tx,ty,tz in targets_xyz:
        d = np.sqrt(((pts - np.array([tx,ty,tz]))**2).sum(axis=1))
        sel |= d <= radius_mm
    nodes_df = nodes_df.copy()
    nodes_df["selected"] = nodes_df.get("selected", False) | sel
    return nodes_df

def load_tract_data(clean_csv_path=None, coords_csv_path=None):
    """
    Load and merge clean.csv and jhu_coordinates.csv into node format.
    
    :param clean_csv_path: Path to clean.csv (default: data/clean.csv)
    :param coords_csv_path: Path to jhu_coordinates.csv (default: data/jhu_coordinates.csv)
    :return: Dictionary with 'CN' and 'AD' keys, each containing DataFrame with x,y,z,id,group,value
    """
    if clean_csv_path is None:
        clean_csv_path = Path(__file__).parent.parent.parent / 'data' / 'clean.csv'
    if coords_csv_path is None:
        coords_csv_path = Path(__file__).parent.parent.parent / 'data' / 'jhu_coordinates.csv'
    
    clean_df = pd.read_csv(clean_csv_path)
    coords_df = pd.read_csv(coords_csv_path)
    
    # Get tract columns (exclude diagnosis)
    tract_cols = [c for c in clean_df.columns if c != 'diagnosis']
    
    results = {}
    for diagnosis in clean_df['diagnosis'].unique():
        diag_row = clean_df[clean_df['diagnosis'] == diagnosis].iloc[0]
        nodes = []
        
        for tract_name in tract_cols:
            value = diag_row[tract_name]
            if pd.isna(value):
                continue
            
            # Match tract name in coordinates (handle exact match or variations)
            coord_match = coords_df[coords_df['roi'] == tract_name]
            if len(coord_match) == 0:
                # Try case-insensitive match
                coord_match = coords_df[coords_df['roi'].str.upper() == tract_name.upper()]
            
            if len(coord_match) > 0:
                coord_row = coord_match.iloc[0]
                nodes.append({
                    'id': tract_name,
                    'x': coord_row['centroid_x'],
                    'y': coord_row['centroid_y'],
                    'z': coord_row['centroid_z'],
                    'group': '1',  # Can be customized later
                    'value': float(value)
                })
        
        results[diagnosis] = pd.DataFrame(nodes)
    
    return results

# ---------------------------
# Surface helpers
# ---------------------------
def ellipsoid_mesh(rx, ry, rz, side="both", u_steps=40, v_steps=40):
    u = np.linspace(0, np.pi, u_steps)
    v = np.linspace(0, 2*np.pi, v_steps)
    u, v = np.meshgrid(u, v)
    x = rx*np.sin(u)*np.cos(v)
    y = ry*np.sin(u)*np.sin(v)
    z = rz*np.cos(u)
    if side in ("L","R"):
        mask = x<0 if side=="L" else x>0
        x,y,z = np.where(mask,x,np.nan),np.where(mask,y,np.nan),np.where(mask,z,np.nan)
    pts = np.vstack([x.ravel(), y.ravel(), z.ravel()]).T
    i,j,k=[],[],[]
    def idx(ui,vi): return ui*v_steps+vi
    for ui in range(u_steps-1):
        for vi in range(v_steps-1):
            if not (np.isnan(x[ui,vi]) or np.isnan(x[ui+1,vi]) or np.isnan(x[ui,vi+1]) or np.isnan(x[ui+1,vi+1])):
                i += [idx(ui,vi), idx(ui+1,vi)]
                j += [idx(ui+1,vi), idx(ui+1,vi+1)]
                k += [idx(ui,vi+1), idx(ui,vi+1)]
    return pts,i,j,k

def make_ellipsoid_traces(opacity=0.15):
    traces=[]
    for side,name in [("L","Left"),("R","Right")]:
        pts,i,j,k=ellipsoid_mesh(RX,RY,RZ,side)
        traces.append(go.Mesh3d(x=pts[:,0],y=pts[:,1],z=pts[:,2],
                                i=i,j=j,k=k,name=f"{name} Hemisphere",
                                opacity=opacity,flatshading=True,showscale=False,hoverinfo="skip"))
    return traces

def load_mni_mask_path():
    candidates = [
        dict(template="MNI152NLin2009cAsym", desc="brain", resolution=1, suffix="mask", extension="nii.gz"),
        dict(template="MNI152NLin2009cAsym", desc="brain", resolution=2, suffix="mask", extension="nii.gz"),
        dict(template="MNI152NLin2009cAsym", resolution=1, suffix="mask", extension="nii.gz"),
    ]
    for kw in candidates:
        try:
            path = tflow_get(**kw)
            if path:
                return str(path)
        except Exception:
            continue
    return None

def make_mni_surface_trace(isovalue=0.5, step_size=2, opacity=0.15):
    if not HAVE_NEURO:
        raise RuntimeError("nibabel/templateflow/scikit-image not available")
    nii_path = load_mni_mask_path()
    if not nii_path:
        raise RuntimeError("Could not fetch MNI brain mask via TemplateFlow")
    img = nib.load(nii_path)
    data = img.get_fdata()
    verts, faces, normals, values = marching_cubes(data, level=isovalue, step_size=int(step_size))
    verts_mm = nib.affines.apply_affine(img.affine, verts)
    x, y, z = verts_mm.T
    i, j, k = faces.T
    return go.Mesh3d(x=x, y=y, z=z, i=i, j=j, k=k, name="MNI Surface",
                     opacity=opacity, flatshading=True, showscale=False, hoverinfo="skip")

def make_aoi_mesh_trace(x,y,z,r,opacity=0.12):
    u=np.linspace(0,np.pi,25)
    v=np.linspace(0,2*np.pi,30)
    u,v=np.meshgrid(u,v)
    X=x+r*np.sin(u)*np.cos(v)
    Y=y+r*np.sin(u)*np.sin(v)
    Z=z+r*np.cos(u)
    pts=np.vstack([X.ravel(),Y.ravel(),Z.ravel()]).T
    i,j,k=[],[],[]
    def idx(ui,vi): return ui*30+vi
    for ui in range(24):
        for vi in range(29):
            i+=[idx(ui,vi),idx(ui+1,vi)]
            j+=[idx(ui+1,vi),idx(ui+1,vi+1)]
            k+=[idx(ui,vi+1),idx(ui,vi+1)]
    return go.Mesh3d(x=pts[:,0],y=pts[:,1],z=pts[:,2],i=i,j=j,k=k,
                     name="AOI",opacity=opacity,flatshading=True,showscale=False,hoverinfo="skip")

# ---------------------------
# Edges
# ---------------------------
def build_edges_knn(df: pd.DataFrame, k: int = 4, max_edges: int = 5000):
    pts = df[["x","y","z"]].to_numpy()
    n = len(pts)
    if n == 0: return []
    edges = set()
    for i in range(n):
        d = np.sqrt(((pts - pts[i])**2).sum(axis=1))
        idx = np.argpartition(d, k+1)[:k+1]  # include self
        for j in idx:
            if i == j: continue
            a, b = (i, j) if i < j else (j, i)
            edges.add((a, b))
        if len(edges) > max_edges:
            break
    return list(edges)

def build_edges_distance(df: pd.DataFrame, max_dist: float = 25.0, max_edges: int = 10000):
    pts = df[["x","y","z"]].to_numpy()
    n = len(pts)
    edges = []
    for i in range(n):
        d = np.sqrt(((pts[i+1:] - pts[i])**2).sum(axis=1))
        js = np.where(d <= max_dist)[0] + (i+1)
        for j in js:
            edges.append((i, j))
            if len(edges) >= max_edges:
                return edges
    return edges

def edges_to_plotly_lines(df: pd.DataFrame, edges: list):
    xs, ys, zs = [], [], []
    for i, j in edges:
        xi, yi, zi = df.loc[i, ["x","y","z"]]
        xj, yj, zj = df.loc[j, ["x","y","z"]]
        xs += [xi, xj, None]
        ys += [yi, yj, None]
        zs += [zi, zj, None]
    return xs, ys, zs

CAMERAS = {
    "isometric": dict(eye=dict(x=1.25, y=1.25, z=1.25)),
    "left":      dict(eye=dict(x=-2, y=0, z=0)),
    "right":     dict(eye=dict(x= 2, y=0, z=0)),
    "anterior":  dict(eye=dict(x=0, y= 2, z=0)),
    "posterior": dict(eye=dict(x=0, y=-2, z=0)),
    "superior":  dict(eye=dict(x=0, y=0, z=2)),
    "inferior":  dict(eye=dict(x=0, y=0, z=-2)),
}

# ---------------------------
# UI
# ---------------------------
app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.h4("Data — Cognitively Normal (CN) vs Alzheimer's Disease (AD)"),
        ui.input_file("csvA","CN CSV (x,y,z[,id,group,value])",accept=[".csv"]),
        ui.input_file("csvB","AD CSV (x,y,z[,id,group,value])",accept=[".csv"]),
        ui.input_action_button("demoA","Use demo (CN)"),
        ui.input_action_button("demoB","Use demo (AD)"),
        ui.input_action_button("load_tract_data","Load tract data (CN/AD)"),
        ui.hr(),
        ui.h4("View mode"),
        ui.input_select("view_mode", "Mode", ["Side-by-side", "Brain differences"], selected="Side-by-side"),
        ui.hr(),
        ui.h4("Highlighting & AOI"),
        ui.input_text("ids","IDs to highlight",""),
        ui.input_text("group","Group to highlight","2"),
        ui.input_numeric("aoi_x","AOI x (mm)",30.0),
        ui.input_numeric("aoi_y","AOI y (mm)",50.0),
        ui.input_numeric("aoi_z","AOI z (mm)",20.0),
        ui.input_slider("aoi_r","AOI radius (mm)",1,30,10),
        ui.hr(),
        ui.h4("Nodes & Edges"),
        ui.input_slider("node_size","Base node size",2,12,6),
        ui.input_slider("node_alpha","Node opacity",1,10,9),
        ui.input_select("edge_mode","Edges mode",["off","kNN","distance"],selected="off"),
        ui.input_numeric("edge_k","k for kNN",4),
        ui.input_numeric("edge_maxdist","Max dist (mm) for distance",25.0),
        ui.input_slider("edge_width","Edge width",1,8,2),
        ui.input_slider("edge_alpha","Edge opacity",1,10,6),
        ui.input_slider("edge_max","Max edges (cap)",100,20000,5000, step=100),
        ui.hr(),
        ui.h4("Surface & View"),
        ui.input_select("surface_mode","Brain surface",["Ellipsoid (fast)","MNI realistic (requires neuro libs)"],selected="Ellipsoid (fast)"),
        ui.input_slider("surface_step","MNI surface step (MNI only)",1,5,2),
        ui.input_select("camera","Camera view",list(CAMERAS.keys()),selected="isometric"),
        ui.input_switch("sync_cam","Sync camera for both", True),
        ui.input_action_button("render","Render / Update"),
        width="360px"
    ),
    ui.panel_conditional(
        "input.view_mode == 'Side-by-side'",
        ui.layout_columns(
            ui.card(
                ui.card_header("Cognitively Normal (CN)"),
                output_widget("p3d_A"),
            ),
            ui.card(
                ui.card_header("Alzheimer's Disease (AD)"),
                output_widget("p3d_B"),
            ),
            col_widths=[6,6]
        )
    ),
    ui.panel_conditional(
        "input.view_mode == 'Brain differences'",
        ui.card(
            ui.card_header("Brain differences (value_B - value_A)"),
            output_widget("p3d_DIFF"),
        )
    ),
    ui.hr(width="50%"),
    ui.div(
    ui.h4("Comparison table"),
    ui.output_data_frame("compare_table"),
    style="height:250px; overflow-y:auto; border:1px solid #ddd; padding:5px;"
),
    title=APP_TITLE
)

# ---------------------------
# Server
# ---------------------------
def server(input, output, session):
    demoA = reactive.Value(False)
    demoB = reactive.Value(False)
    use_tract_data = reactive.Value(False)
    tract_data_cache = reactive.Value(None)

    @reactive.Effect
    @reactive.event(input.load_tract_data)
    def _load_tract_data():
        try:
            data = load_tract_data()
            tract_data_cache.set(data)
            use_tract_data.set(True)
            demoA.set(False)
            demoB.set(False)
        except Exception as e:
            print(f"Error loading tract data: {e}")

    @reactive.Effect
    @reactive.event(input.demoA)
    def _demoA():
        demoA.set(True)
        use_tract_data.set(False)

    @reactive.Effect
    @reactive.event(input.demoB)
    def _demoB():
        demoB.set(True)
        use_tract_data.set(False)

    def prepare_nodes(raw_df: pd.DataFrame) -> pd.DataFrame:
        df = normalize_columns(raw_df)
        df["selected"] = False
        ids = [s.strip() for s in input.ids().split(",") if s.strip()]
        if ids:
            df.loc[df["id"].isin(ids), "selected"] = True
        if input.group():
            df.loc[df["group"] == input.group(), "selected"] = True
        df = mark_nearest(df, [(input.aoi_x(), input.aoi_y(), input.aoi_z())], radius_mm=float(input.aoi_r()))
        return df

    @reactive.Calc
    def df_A():
        if use_tract_data.get() and tract_data_cache.get() is not None:
            data = tract_data_cache.get()
            if 'CN' in data:
                return prepare_nodes(data['CN'])
        if input.csvA() and not demoA.get() and not use_tract_data.get():
            file = input.csvA()[0]
            raw = pd.read_csv(io.BytesIO(file.read()))
            return prepare_nodes(raw)
        base = generate_demo_nodes(seed=2025, with_values=True)
        return prepare_nodes(base)

    @reactive.Calc
    def df_B():
        if use_tract_data.get() and tract_data_cache.get() is not None:
            data = tract_data_cache.get()
            if 'AD' in data:
                return prepare_nodes(data['AD'])
        if input.csvB() and not demoB.get() and not use_tract_data.get():
            file = input.csvB()[0]
            raw = pd.read_csv(io.BytesIO(file.read()))
            return prepare_nodes(raw)
        base = generate_demo_nodes(seed=2026, with_values=True)
        if "value" in base.columns:
            base["value"] = np.clip(base["value"] + 0.15*np.sin(np.linspace(0, 4*np.pi, len(base))), 0, 1)
        return prepare_nodes(base)

    def build_surface_traces():
        mode = input.surface_mode()
        if mode == "MNI realistic (requires neuro libs)":
            if not HAVE_NEURO:
                return make_ellipsoid_traces(0.12), "Ellipsoid (install nibabel, templateflow, scikit-image for MNI surface)"
            try:
                return [make_mni_surface_trace(isovalue=0.5, step_size=int(input.surface_step()), opacity=0.15)], "MNI Realistic Surface"
            except Exception as e:
                return make_ellipsoid_traces(0.12), f"Ellipsoid (MNI surface error: {e})"
        else:
            return make_ellipsoid_traces(0.15), "Ellipsoid"

    def add_edges_if_needed(traces, df):
        if input.edge_mode() == "off" or len(df) < 2:
            return
        if input.edge_mode() == "kNN":
            edges = build_edges_knn(df, k=int(input.edge_k()), max_edges=int(input.edge_max()))
        else:
            edges = build_edges_distance(df, max_dist=float(input.edge_maxdist()), max_edges=int(input.edge_max()))
        if edges:
            xs, ys, zs = edges_to_plotly_lines(df, edges)
            traces.append(go.Scatter3d(
                x=xs, y=ys, z=zs, mode="lines",
                line=dict(width=int(input.edge_width())),
                opacity=float(input.edge_alpha())/10.0,
                name=f"Edges ({len(edges)})",
                hoverinfo="skip"
            ))

    def add_nodes(traces, df, tag=""):
        base_size = int(input.node_size())
        alpha = float(input.node_alpha())/10
        if "value" in df.columns:
            val_arr = df["value"].to_numpy()
            scale = np.ptp(val_arr) if np.ptp(val_arr) > 0 else 1.0
            sizes = base_size + 6*(val_arr - np.min(val_arr)) / (scale + 1e-9)
        else:
            sizes = np.full(len(df), base_size)

        hi_mask = df["selected"].to_numpy()
        lo_mask = ~hi_mask

        if lo_mask.any():
            lo = df[lo_mask]
            traces.append(go.Scatter3d(
                x=lo["x"], y=lo["y"], z=lo["z"], mode="markers",
                marker=dict(size=sizes[lo_mask].astype(float), opacity=alpha),
                name=f"{tag}Nodes",
                text=[f"{r.id} | group {r.group}" + (f" | value {getattr(r,'value'):.3f}" if hasattr(r,'value') else "") for r in lo.itertuples(index=False)],
                hoverinfo="text"
            ))
        if hi_mask.any():
            hi = df[hi_mask]
            traces.append(go.Scatter3d(
                x=hi["x"], y=hi["y"], z=hi["z"], mode="markers",
                marker=dict(size=(sizes[hi_mask] + 3).astype(float), symbol="diamond", opacity=1.0),
                name=f"{tag}Highlighted",
                text=[f"{r.id} | group {r.group}" + (f" | value {getattr(r,'value'):.3f}" if hasattr(r,'value') else "") for r in hi.itertuples(index=False)],
                hoverinfo="text"
            ))

    def make_fig_for_df(df, tag=""):
        traces, surf_label = build_surface_traces()
        traces.append(make_aoi_mesh_trace(input.aoi_x(), input.aoi_y(), input.aoi_z(), input.aoi_r()))
        add_edges_if_needed(traces, df)
        add_nodes(traces, df, tag)
        fig = go.Figure(traces)
        fig.update_layout(title=f"{tag} — {surf_label}", scene=dict(aspectmode="data"), legend=dict(itemsizing="constant"))
        return fig

    # --------- Differences view helpers ---------
    @reactive.Calc
    def df_DIFF():
        A = df_A().copy()
        B = df_B().copy()
        # Merge by id; keep positions (x,y,z) from A where available, else from B.
        keep = ["id","x","y","z","value","group"]
        A2 = A[[c for c in keep if c in A.columns]].rename(columns={c: f"{c}_A" for c in keep if c!="id"})
        B2 = B[[c for c in keep if c in B.columns]].rename(columns={c: f"{c}_B" for c in keep if c!="id"})
        m = pd.merge(A2, B2, on="id", how="outer", indicator=True)

        # Coordinates: prefer A else B
        x = m["x_A"].fillna(m["x_B"])
        y = m["y_A"].fillna(m["y_B"])
        z = m["z_A"].fillna(m["z_B"])

        # Value diff (B - A); if one missing, leave NaN
        valA = m.get("value_A")
        valB = m.get("value_B")
        if valA is not None and valB is not None:
            diff = valB - valA
        else:
            diff = pd.Series([np.nan]*len(m))

        out = pd.DataFrame({
            "id": m["id"],
            "x": x, "y": y, "z": z,
            "value_diff": diff
        })
        # Carry a selection flag based on user inputs
        out["selected"] = False
        ids = [s.strip() for s in input.ids().split(",") if s.strip()]
        if ids:
            out.loc[out["id"].isin(ids), "selected"] = True
        out = mark_nearest(out, [(input.aoi_x(), input.aoi_y(), input.aoi_z())], radius_mm=float(input.aoi_r()))
        return out.dropna(subset=["x","y","z"]).reset_index(drop=True)

    def make_fig_for_DIFF(df):
        traces, surf_label = build_surface_traces()
        traces.append(make_aoi_mesh_trace(input.aoi_x(), input.aoi_y(), input.aoi_z(), input.aoi_r()))

        # Nodes colored by value_diff (diverging). Size scales with |diff|.
        base_size = int(input.node_size())
        alpha = float(input.node_alpha())/10
        d = df["value_diff"].to_numpy()
        absd = np.abs(np.nan_to_num(d, nan=0.0))
        scale = np.ptp(absd) if np.ptp(absd) > 0 else 1.0
        sizes = base_size + 6*(absd - absd.min())/(scale + 1e-9)

        # Split selected vs others
        hi_mask = df["selected"].to_numpy()
        lo_mask = ~hi_mask

        def scatter_for(mask, name, symbol=None, opacity=None):
            if not mask.any():
                return
            sub = df[mask]
            traces.append(go.Scatter3d(
                x=sub["x"], y=sub["y"], z=sub["z"], mode="markers",
                marker=dict(
                    size=sizes[mask].astype(float),
                    opacity=1.0 if opacity is None else opacity,
                    color=sub["value_diff"],
                    colorscale="RdBu",
                    cmin=-np.nanmax(absd) if np.nanmax(absd) > 0 else -1,
                    cmax= np.nanmax(absd) if np.nanmax(absd) > 0 else 1,
                    colorbar=dict(title="Δ value (B - A)") if name=="Nodes" else None,
                    symbol=symbol if symbol else "circle"
                ),
                name=name,
                text=[f"{r.id} | Δ {getattr(r,'value_diff'):.3f}" if not np.isnan(getattr(r,'value_diff')) else f"{r.id} | Δ N/A" for r in sub.itertuples(index=False)],
                hoverinfo="text"
            ))

        if lo_mask.any():
            scatter_for(lo_mask, "Nodes", opacity=alpha)
        if hi_mask.any():
            scatter_for(hi_mask, "Highlighted", symbol="diamond", opacity=1.0)

        fig = go.Figure(traces)
        fig.update_layout(title=f"Brain differences — {surf_label}", scene=dict(aspectmode='data'))
        return fig

    # --------- Outputs ---------
    @output
    @render_plotly
    @reactive.event(input.render)
    def p3d_A():
        if input.view_mode() != "Side-by-side":
            return go.Figure()
        fig = make_fig_for_df(df_A(), "Cognitively Normal (CN)")
        fig.update_scenes(camera=CAMERAS.get(input.camera(), CAMERAS["isometric"]))
        return fig

    @output
    @render_plotly
    @reactive.event(input.render)
    def p3d_B():
        if input.view_mode() != "Side-by-side":
            return go.Figure()
        fig = make_fig_for_df(df_B(), "Alzheimer's Disease (AD)")
        if input.sync_cam():
            fig.update_scenes(camera=CAMERAS.get(input.camera(), CAMERAS["isometric"]))
        return fig

    @output
    @render_plotly
    @reactive.event(input.render)
    def p3d_DIFF():
        if input.view_mode() != "Brain differences":
            return go.Figure()
        fig = make_fig_for_DIFF(df_DIFF())
        fig.update_scenes(camera=CAMERAS.get(input.camera(), CAMERAS["isometric"]))
        return fig

    @output
    @render.data_frame
    def compare_table():
        A = df_A().copy()
        B = df_B().copy()
        keep = ["id","group","x","y","z","value"] if "value" in A.columns else ["id","group","x","y","z"]
        A = A[keep].rename(columns={c: f"{c}_A" for c in keep if c!="id"})
        B = B[keep].rename(columns={c: f"{c}_B" for c in keep if c!="id"})
        merged = pd.merge(A, B, on="id", how="outer", indicator=True)
        if "value_A" in merged.columns and "value_B" in merged.columns:
            merged["value_diff"] = merged["value_B"].fillna(0) - merged["value_A"].fillna(0)
        if all(c in merged.columns for c in ["x_A","y_A","z_A","x_B","y_B","z_B"]):
            xyzA = merged[["x_A","y_A","z_A"]].to_numpy()
            xyzB = merged[["x_B","y_B","z_B"]].to_numpy()
            diff = np.sqrt(np.nansum((xyzB - xyzA)**2, axis=1))
            merged["coord_dist_mm"] = diff
        cat_cols = [c for c in merged.columns if str(merged[c].dtype) == "category"]
        for c in cat_cols:
            merged[c] = merged[c].astype(object)
        merged = merged.fillna("")
        return merged

app = App(app_ui, server)
