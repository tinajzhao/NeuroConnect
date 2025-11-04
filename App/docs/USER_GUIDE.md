# User Guide
## Modes
- **Side-by-side:** view two brains independently.
- **Brain differences:** single view, coloring nodes by Δ = value_B - value_A.

## Controls
- **AOI:** define an Area of Interest (x,y,z,radius).
- **Edges:** kNN (connect k nearest nodes) or distance threshold.
- **Surface:** Ellipsoid (fast) or MNI realistic (needs neuro libs).
- **Camera:** preset viewpoints (isometric, left, right, etc.).

## Tips
- Reduce surface detail (step_size ↑) for speed.
- Cap edges for performance.
- Keep node count ≤ 500 for real-time rendering.
