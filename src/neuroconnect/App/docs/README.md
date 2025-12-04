# 🧠 Neuroconnect 

## Overview
This interactive web app visualizes and compares two 3D brain models — for example, a healthy brain vs. a sick brain — using coordinate-based node data.
It supports:
- Side-by-side visualization
- Brain differences (Δ = Sick − Healthy)
- Edge visualization (kNN or distance-based)
- Ellipsoid or realistic MNI surface rendering
- Dark mode toggle

## Quickstart
```bash
python -m venv venv
source venv/bin/activate  # on Windows: venv\Scripts\activate
pip install -r requirements_shiny_neuroconnect.txt
shiny run --reload app_shiny_neuroconnect.py
```

For MNI realistic rendering, install neuro dependencies:
```bash
pip install nibabel templateflow scikit-image
```

## Data format
CSV must include at least `x, y, z` columns (mm). Optional columns: `id, group, value`.
Example:
```csv
x,y,z,id,group,value
-30,-60,40,Node_001,2,0.54
12,40,8,Node_002,1,0.78
```

## License
This project is released under the MIT License. See `LICENSE` for details.
