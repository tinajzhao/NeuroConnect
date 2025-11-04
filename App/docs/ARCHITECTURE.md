# Architecture
## Overview
- **UI:** Shiny for Python (reactive inputs, sidebar, panels).
- **3D Rendering:** Plotly `Mesh3d` for surfaces + `Scatter3d` for nodes/edges.
- **Data Flow:** CSV → DataFrames (A, B) → DIFF merge → Plotly traces.

## Modules
- `edges.py`: edge creation (kNN, distance).
- `meshes.py`: ellipsoid + MNI surface generation.
- `diff.py`: merge and compute Δ (B−A).
- `plotting.py`: Plotly layout, dark theme, cameras.
