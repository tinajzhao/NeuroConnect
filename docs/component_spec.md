# Component Specification

## Software Components

### Component 1: Data Preparation

#### Sub-component 1.1: Data Loading

**Name:** CSV Data Loader

**What it does:**  
Reads diagnosis and DTI data from CSV files stored in the data folder.

**Inputs (with type information):**
- `diagnosis_path`: string, file path to diagnosis.csv
- `dti_path`: string, file path to DTI.csv

**Outputs (with type information):**
- `diagnosis_df`: dataframe with columns `participant_id` (string), `diagnosis` (string: AD/CN/MCI/etc.)
- `dti_df`: dataframe with columns `participant_id` (string) and 212 metric columns (53 tracts × 4 metrics)

**Components used:**  
pandas.read_csv()

**Side effects:**  
None - read-only operation

---

#### Sub-component 1.2: Data Cleaning

**Name:** Data Merger and Filter

**What it does:**  
Merges diagnosis and DTI data on participant ID, filters for AD and CN groups only, removes subjects with missing data, and extracts only FA columns.

**Inputs (with type information):**
- `diagnosis_df`: dataframe from Sub-component 1.1
- `dti_df`: dataframe from Sub-component 1.1
- `metric_filter`: string, metric to extract (e.g., "FA")

**Outputs (with type information):**
- `clean_df`: dataframe with columns `participant_id` (string), `diagnosis` (string), and 53 FA columns with stripped names (e.g., `ACR_L`, `GCC`)
- Number of subjects removed: integer

**Components used:**  
merge (join on participant_id), dropna(), string manipulation for column renaming

**Side effects:**  
Excludes MCI and other subjects from analysis. Removes participants missing diagnosis or DTI data. Prints number of subjects excluded to console.

---

#### Sub-component 1.3: Summary Statistics Calculator

**Name:** Group-Level Tract Statistics

**What it does:**  
Calculates mean FA and MD values for each tract, separately for AD and CN groups.

**Inputs (with type information):**
- `clean_df`: dataframe from Sub-component 1.2
- `metrics`: list of strings, metrics to summarize (e.g., ["FA", "MD"])

**Outputs (with type information):**
- `summary_stats`: dataframe with columns:
  - `tract_label` (string): ADNI abbreviation
  - `FA_mean_AD` (float): Mean FA for AD group
  - `FA_mean_CN` (float): Mean FA for CN group
  - `MD_mean_AD` (float): Mean MD for AD group
  - `MD_mean_CN` (float): Mean MD for CN group
  - `n_AD` (int): Number of AD subjects
  - `n_CN` (int): Number of CN subjects

**Components used:**  
pandas groupby(), mean(), aggregate functions

**Side effects:**  
None - computation only

---

#### Sub-component 1.4: Summary Data Output

**Name:** Summary Statistics Writer

**What it does:**  
Saves calculated summary statistics to CSV file for use by visualization component.

**Inputs (with type information):**
- `summary_stats`: dataframe from Sub-component 1.3
- `output_path`: string, file path for output (default: "summary_stats.csv")

**Outputs (with type information):**
- CSV file written to disk at `output_path`
- Boolean: True if write successful, False otherwise

**Components used:**  
pandas to_csv()

**Side effects:**  
Creates or overwrites file at output_path. File becomes input for Component 3.

---

### Component 2: Tract Coordinate Extraction

#### Sub-component 2.1: Atlas File Locator

**Name:** JHU Atlas Locator

**What it does:**  
Searches common file system locations to find the JHU white matter atlas NIfTI file.

**Inputs (with type information):**
- Environment variable `FSLDIR`: String, optional FSL installation directory
- Search paths: List of strings, directories to check (FSL dir, /usr/local/fsl, ~/nilearn_data)

**Outputs (with type information):**
- `atlas_path`: string, full file path to JHU-ICBM-labels-1mm.nii.gz
- Raises `FileNotFoundError` if atlas not found with download instructions

**Components used:**  
os.environ.get(), pathlib.Path.exists()

**Side effects:**  
If atlas not found, prints error message with download link to console.

---

#### Sub-component 2.2: Single Tract Coordinate Extractor

**Name:** PCA-Based Tract Endpoint Calculator

**What it does:**  
For one tract ROI, finds all voxels, calculates centroid, uses PCA to find tract direction, and extracts start/end points along principal axis. Converts voxel coordinates to MNI space.

**Inputs (with type information):**
- `atlas_data`: numpy array (3D), atlas image data with integer labels
- `atlas_affine`: numpy array (4×4), voxel-to-MNI transformation matrix
- `roi_number`: integer (1-48), ROI label to extract

**Outputs (with type information):**
- Dictionary with keys:
  - `start`: numpy array (3,) with [x, y, z] in MNI mm
  - `end`: numpy array (3,) with [x, y, z] in MNI mm  
  - `centroid`: numpy array (3,) with [x, y, z] in MNI mm
- Returns `None` if tract has no voxels

**Components used:**  
numpy argwhere() for voxel extraction, sklearn.decomposition.PCA for finding principal axis, numpy matrix multiplication for coordinate transformation

**Side effects:**  
None - pure computation

---

#### Sub-component 2.3: Base Tract Loop

**Name:** Batch Tract Extractor

**What it does:**  
Iterates through all 48 base JHU tracts using the BASE_TRACTS list, calls single tract extractor for each, and compiles results into dataframe.

**Inputs (with type information):**
- `atlas_img`: nibabel Nifti1Image object, loaded atlas
- `BASE_TRACTS`: list of 48 tuples (roi_number: int, adni_label: string)

**Outputs (with type information):**
- `df`: dataframe with columns:
  - `roi` (string): ADNI abbreviation (e.g., "ACR_L", "GCC")
  - `start_x`, `start_y`, `start_z` (float): Start coordinates in MNI mm
  - `end_x`, `end_y`, `end_z` (float): End coordinates in MNI mm
  - `centroid_x`, `centroid_y`, `centroid_z` (float): Centroid coordinates in MNI mm
- Progress printed to console: "ACR_L complete" or "! ACR_L (no voxels)"

**Components used:**  
Sub-component 2.2, dataframe constructor

**Side effects:**  
Prints extraction progress to console. Skips tracts with no voxels (prints "! no voxels").

---

#### Sub-component 2.4: Additional Tract Calculator

**Name:** Bilateral and Combined ROI Generator

**What it does:**  
Calculates 5 additional tract coordinates (GCCB, SCCB, BCC, FULLCC, SUMFX) by averaging left/right hemispheres or combining corpus callosum sub-regions.

**Inputs (with type information):**
- `df`: dataframe from Sub-component 2.3 with 48 base tracts
- `ADDITIONAL_ROIS`: list of 5 strings: ["GCCB", "BCC", "SCCB", "FULLCC", "SUMFX"]

**Outputs (with type information):**
- `additional`: list of 5 dictionaries with same structure as base tracts:
  - `roi` (string): ADNI abbreviation
  - 9 coordinate columns (start/end/centroid x/y/z as float)

**Components used:**  
dataframe filtering with df[df['roi'] == label], avg_coords() helper function for coordinate averaging

**Side effects:**  
Prints calculation progress ("SUMFX complete").

---

#### Sub-component 2.5: Coordinate File Writer

**Name:** Tract Coordinate CSV Exporter

**What it does:**  
Combines base (48) and additional (5) tract coordinates into single DataFrame and exports to CSV.

**Inputs (with type information):**
- `df`: dataframe with 48 base tracts from Sub-component 2.3
- `additional`: list of 5 dictionaries from Sub-component 2.4
- `output_file`: string, filename (default: "jhu_coordinates.csv")

**Outputs (with type information):**
- CSV file with 53 rows, 10 columns written to disk:
  - Column 1: `roi` (string)
  - Columns 2-10: start_x/y/z, end_x/y/z, centroid_x/y/z (float)

**Components used:**  
pandas concat(), to_csv()

**Side effects:**  
Creates or overwrites file at output_file location. Prints confirmation message: "COMPLETE! Extracted 53 tracts. Saved to: jhu_coordinates.csv"


---

### Component 3: Brain Visualization Manager

#### Sub-component 3.1: Coordinate File Loader

**Name:** Tract Coordinate Reader

**What it does:**  
Loads tract coordinate CSV file and parses into coordinate arrays for visualization.

**Inputs (with type information):**
- `coord_path`: string, path to jhu_coordinates.csv from Component 2

**Outputs (with type information):**
- `coords_df`: dataframe with all tract data
- `node_coords`: numpy array of shape (N, 3) with start/end points
  - N = 2 × number of tracts (start and end for each)
- `tract_labels`: list of strings, ADNI labels for each tract

**Components used:**  
pandas read_csv(), numpy array stacking

**Side effects:**  
None - read-only operation

---

#### Sub-component 3.2: DTI Metrics Loader

**Name:** DTI Statistics Loader

**What it does:**  
Loads mean DTI metrics (FA) for each diagnosis group and tract from summary statistics file.

**Inputs (with type information):**
- `stats_path`: string, path to summary_stats.csv from Component 1
- `diagnosis_group`: string, group to load (i.e. "AD" or "CN")
- `metrics`: list of strings, metrics to extract (i.e. ["FA"])

**Outputs (with type information):**
- `tract_metrics_df`: dataframe with columns:
  - `tract_label` (string)
  - `FA` (float): Mean FA for selected group

**Components used:**  
pandas read_csv(), column selection and renaming

**Side effects:**  
None - read-only operation

---

#### Sub-component 3.3: Node-Edge Mapper

**Name:** Node-Edge Mapper

**What it does:**  
Creates network graph structure by mapping each tract to start/end nodes and assigns FA values as edge properties.

**Inputs (with type information):**
- `coords_df`: dataframe from sub-component 3.1
- `tract_metrics_df`: dataframe from sub-component 3.2
- `n_tracts`: integer, number of tracts to visualize

**Outputs (with type information):**
- `adjacency_matrix`: numpy array of shape (2N, 2N) where N = n_tracts
  - Entry [i, j] contains FA value if nodes i and j are connected by a tract
  - Symmetric matrix (FA[i,j] = FA[j,i])
- `edge_metadata`: dictionary with:
  - `edge_colors`: list of floats (FA values)
  - `tract_names`: list of strings

**Components used:**  
numpy zeros() for matrix creation, pandas merge for matching coordinates to metrics

**Side effects:**  
None - pure computation

---

#### Sub-component 3.4: Edge Value Scaler

**Name:** DTI Metric to Visual Property Mapper

**What it does:**  
Scales FA values to color range suitable for visualization.

**Inputs (with type information):**
- `fa_values`: numpy array (N,) with FA values (typically 0.2-0.6)
- `color_range`: ******complete this later***

**Outputs (with type information):**
- `scaled_colors`: numpy array (N,) with FA values clipped to color_range

**Components used:**  
numpy clip(), linear scaling (min-max normalization)

**Side effects:**  
None - pure computation

---

#### Sub-component 3.5: Visualization Renderer

**Name:** Visualization Renderer

**What it does:**  
Takes node coordinates, adjacency matrix, and edge properties and renders using plotly.

**Inputs (with type information):**
- `node_coords`: numpy array (N, 3) from Sub-component 3.3
- `adjacency_matrix`: numpy array (N, N) from Sub-component 3.3
- `edge_colors`: numpy array from Sub-component 3.4

**Outputs (with type information):**
- Interactive plot object:
  - plotly: plotly.graph_objects.Figure
- Plot can be displayed, saved, or embedded in Shiny app

**Components used:**  
plotly

**Side effects:**  
Displays interactive plot in browser/notebook. May save figure to disk if save_path provided.

---

#### Sub-component 3.6: Group Difference Calculator

**Name:** Group Difference Calculator

**What it does:**  
Calculates difference in FA values between AD and CN groups for each tract, to be visualized with diverging colormap.

**Inputs (with type information):**
- `fa_ad`: numpy array (N,) with AD group FA values
- `fa_cn`: numpy array (N,) with CN group FA values
- `difference_type`: string, "raw" or "percent" (default: "raw")

**Outputs (with type information):**
- `fa_difference`: numpy array (N,) with differences (AD - CN)
  - Negative values = lower FA in AD (worse integrity)
  - Positive values = higher FA in AD (rare)
- `colormap_config`: *******complete this later**

**Components used:**  
numpy subtraction

**Side effects:**  
None - pure computation

---

#### Sub-component 3.7: Comparison Overlay Visualizer

**Name:** Side-by-Side Group Comparison Plotter

**What it does:**  
Creates multi-panel visualization showing AD brain, CN brain, and difference map side-by-side.

**Inputs (with type information):**
- `node_coords`: numpy array (N, 3)
- `adjacency_matrix`: numpy array (N, N)
- `fa_ad`: numpy array (N,)
- `fa_cn`: numpy array (N,)
- `fa_diff`: numpy array (N,) from Sub-component 3.6

**Outputs (with type information):**
- Multi-panel figure with 3 subplots:
  - Left: AD connectome (red colormap)
  - Right: CN connectome (red colormap)
  - Mid: Difference map (blue-white-red diverging)

**Components used:**  
Sub-component 3.5 called three times with different data, plotly.subplots

**Side effects:**  
Displays three brain views in single figure window.




## Interactions


## Preliminary Plan