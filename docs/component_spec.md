# Component Specification

## Table of Contents
- [Software Components](#software-components)
  - [Component 1: Data Preparation](#component-1-data-preparation)
  - [Component 2: Tract Coordinate Extraction](#component-2-tract-coordinate-extraction)
  - [Component 3: Brain Visualization Manager](#component-3-brain-visualization-manager)
- [Interactions](#interactions)
- [Preliminary Plan](#preliminary-plan)

---

## Software Components

### Component 1: Data Preparation

**High-level Description:**  
The Data Preparation component processes raw ADNI DTI data and diagnostic information into clean, analysis-ready formats. 

**What it does:**
- Loads and validates CSV files containing diagnosis and DTI data
- Merges datasets on participant ID
- Filters for CN and AD diagnostic groups
- Removes participants with missing data
- Calculates mean FA/MD values per tract for each diagnostic group
- Computes group differences for difference map visualizations
- Exports cleaned and summarized data

**Inputs:**
- `All_Subjects_Study_Entry_diagnosis.csv`: Participant IDs and diagnostic labels (CN/MCI/AD)
- `All_Subjects_DTIROI_MEAN.csv`: Tract-level DTI metrics (FA, MD, RD, AD) for all participants

**Outputs:**
- `clean.csv`: Merged dataset with complete cases only
- `summary_stats.csv`: Group-level mean values for each tract
- Console feedback on data quality and filtering

---

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

#### Sub-component 1.5: Group Difference Calculator

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

**Components used:**  
numpy subtraction

**Side effects:**  
None - pure computation

---

### Component 2: Tract Coordinate Extraction

**High-level Description:**  
The Tract Coordinate Extraction component processes the JHU white matter atlas to extract 3D spatial coordinates for each white matter tract in MNI standard space. It uses Principal Component Analysis (PCA) to determine tract directionality and computes start, end, and centroid coordinates for 48 base tracts plus 5 composite regions (53 total). This component runs once as a preprocessing step and outputs a standardized coordinate file used by all visualizations.

**What it does:**
- Locates JHU atlas NIfTI file in the file system
- Loads atlas image data and affine transformation matrix
- Extracts voxel coordinates for each tract ROI
- Uses PCA to determine tract principal axis and endpoints
- Converts voxel coordinates to MNI millimeter space
- Calculates bilateral and composite tract coordinates
- Exports all coordinates to CSV

**Inputs:**
- JHU ICBM-DTI-81 atlas NIfTI file (`JHU-ICBM-labels-1mm.nii.gz`)
- Tract label mappings (hardcoded in BASE_TRACTS dictionary)

**Outputs:**
- `jhu_coordinates.csv`: 53 tracts × 10 columns (roi, start_xyz, end_xyz, centroid_xyz)
- Console progress messages during extraction

---

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

**High-level Description:**  
The Brain Visualization Manager component creates interactive 3D visualizations of brain connectivity using Plotly. It loads tract coordinates and DTI metrics, maps them to a node-edge network structure, scales metric values to visual properties (color, size), and renders side-by-side or difference visualizations. This component integrates with the Shiny web interface to provide real-time interactive exploration of connectivity patterns across diagnostic groups.

**What it does:**
- Loads tract coordinates from Component 2 output
- Loads DTI metrics from Component 1 output or user uploads
- Creates node-edge network graph structure
- Scales FA/MD values to visual properties (color intensity, node size)
- Renders interactive 3D brain visualizations using Plotly
- Supports side-by-side comparison and difference mapping
- Displays visualizations in Shiny web interface

**Inputs:**
- `jhu_coordinates.csv`: Tract spatial coordinates from Component 2
- `clean.csv` or user-uploaded CSV: DTI metrics
- User interaction parameters (camera angle, highlighted tracts, etc.)

**Outputs:**
- Interactive Plotly Figure object displayed in Shiny app
- Optional: Exported PNG/HTML files for publication

---

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
- `color_range`: *complete this later*

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

#### Sub-component 3.6: Comparison Overlay Visualizer

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

---

## Interactions
Example of interactions for 'Upload and Visualize Data' Use Case

**Flow Description:**

When a user uploads custom DTI data to visualize brain connectivity, the three main components interact in the following sequence:

**Step 1 & 2: Data Input and Processing (I/O)**

1. **User action:** Uploads `diagnosis.csv` and `dti.csv` files via Shiny web interface
2. **Component 1 - Data Preparation** receives the uploaded files:
   - **Sub-component 1.1 (Data Loader)** reads both CSV files into pandas DataFrames
   - **Sub-component 1.2 (Data Cleaning)** merges the datasets on participant ID, filters for CN and AD groups, removes missing data, and extracts FA columns
   - Output: `clean.csv` containing merged and validated data
   - **Sub-component 1.4 (Summary Statistics Writer)** optionally saves group-level statistics for quick access
   - Output: `summary_stats.csv`

3. **Component 2 - Tract Coordinate Extraction** (pre-computed):
   - **Sub-component 2.1 (Atlas Locator)** finds the JHU white matter atlas file
   - **Sub-component 2.2 & 2.3** extract voxel coordinates and convert to MNI space for all 48 base tracts
   - **Sub-component 2.4** computes 5 additional composite tract coordinates
   - **Sub-component 2.5 (Coordinate File Writer)** saves results
   - Output: `tract_coordinate.csv` (pre-exists, loaded when needed)

**Step 3: Visualization Generation (I/O)**

4. **Component 3 - Brain Visualization Manager** creates the interactive display:
   - **Sub-component 3.1 (Coordinate Loader)** reads `tract_coordinate.csv` to get spatial positions
   - **Sub-component 3.2 (DTI Metrics Loader)** reads `clean.csv` to get FA values for the uploaded data
   - **Sub-component 3.3 (Node-Edge Mapper)** matches tract coordinates with FA values, creating node positions and edge properties
   - **Sub-component 3.4 (Value Scaler)** maps FA values to color intensities using appropriate color scale
   - **Sub-component 3.5 (Renderer)** generates Plotly Figure with 3D scatter plot of nodes and connecting edges
   - Output: Interactive 3D visualization displayed in Shiny app browser window

5. **User interaction:** Views visualization in browser, can rotate, zoom, and interact with the 3D brain model


**Data Flow Summary:**

```
User Uploads
    ↓
diagnosis.csv + dti.csv 
    ↓
Component 1 (Data Preparation)
    ├─ 1.1: Load CSVs → DataFrames
    ├─ 1.2: Clean & Merge → clean.csv
    └─ 1.4: Summary Stats → summary_stats.csv (optional)
    ↓
Component 2 (Tract Coordinates) - Pre-computed
    └─ 2.5: Provides → tract_coordinate.csv
    ↓
Component 3 (Brain Visualization)
    ├─ 3.1: Load coordinates
    ├─ 3.2: Load clean.csv metrics  
    ├─ 3.3: Create node-edge network
    ├─ 3.4: Scale FA → colors
    └─ 3.5: Render → Plotly Figure
    ↓
Shiny App Display (Interactive 3D brain)
```

**Visual Diagram:**

![Diagram showing interactions for upload and visualize data use case](../images/nc_interactions.png)

---

## Preliminary Plan

1a. Functions for Components 1, 2, 3 (Data preparation, Tract coordinate extraction, Brain visualization)
1b. Tests for Components 1, 2, 3 (Data preparation, Tract coordinate extraction, Brain visualization)

2. Write Components for User Data and Export Data

3a. Functions for Components for User Data and Export Data
3b. Tests for Components for User Data and Export Data

4. Connect Different Components

### Phase 1: Core Component Development

**1. Component 1: Data Preparation** **(COMPLETE)**
   - 2a. Implement CSV data loader (Sub-component 1.1)
   - 2b. Implement data merger and filter (Sub-component 1.2)
   - 2c. Implement summary statistics calculator (Sub-component 1.3)
   - 2d. Implement group difference calculator (Sub-component 1.5)
   - 2e. Implement summary data output writer (Sub-component 1.4)
   - 2f. Write unit tests for each sub-component
   - 2g. Integration test: Validate clean.csv and summary_stats.csv outputs

**2. Component 2: Tract Coordinate Extraction** **(COMPLETE)**
   - 1a. Implement atlas file locator (Sub-component 2.1)
   - 1b. Implement PCA-based coordinate extractor (Sub-component 2.2)
   - 1c. Implement batch tract loop (Sub-component 2.3)
   - 1d. Implement additional tract calculator (Sub-component 2.4)
   - 1e. Implement CSV exporter (Sub-component 2.5)
   - 1f. Write comprehensive unit tests 
   - 1g. Validate output: `jhu_coordinates.csv` with 53 tracts


**3. Component 3: Brain Visualization Manager** **(IN PROGRESS)**
   - 3a. Implement coordinate file loader (Sub-component 3.1)
   - 3b. Implement DTI metrics loader (Sub-component 3.2)
   - 3c. Implement node-edge mapper (Sub-component 3.3)
   - 3d. Implement edge value scaler (Sub-component 3.4)
   - 3e. Implement basic Plotly renderer (Sub-component 3.5)
   - 3f. Implement comparison overlay visualizer (Sub-component 3.6)
   - 3g. Write unit tests for visualization logic
   - 3h. Integration test: Verify end-to-end visualization pipeline

### Phase 2: Integration & User Interface

**4. Shiny Application Development** 🚧 **(IN PROGRESS)**
   - 4a. Design UI layout with file upload, controls, and visualization panels
   - 4b. Implement reactive data loading and validation
   - 4c. Connect Component 1 to file upload interface
   - 4d. Connect Component 3 to visualization output
   - 4e. Implement side-by-side and difference view modes
   - 4f. Add interactive controls (camera, highlighting, AOI selection)
   - 4g. Implement demo data loading functionality
   - 4h. Test user workflows for all use cases

**5. Testing & Quality Assurance**
   - 5a. End-to-end integration testing (all components working together)
   - 5b. User acceptance testing with target audience members
   - 5c. Performance testing with large datasets
   - 5d. Cross-browser compatibility testing
   - 5e. Code coverage analysis and gap filling
   - 5f. Code quality checks (pylint, formatting standards)

### Phase 3: Documentation & Deployment

**6. Documentation**
   - 6a. API documentation for all functions
   - 6b. User guide with examples and screenshots
   - 6c. README with installation and quick start
   - 6d. Example notebooks demonstrating common workflows

**7. Deployment & Distribution**
   - 7a. Package configuration (pyproject.toml)
   - 7b. Continuous integration setup (GitHub Actions)
   - 7c. Release preparation and version tagging
   - 7d. Publication of demo application

### Phase 4: Future Enhancements (Optional)

**8. Advanced Features** 📋 **(PLANNED)**
   - 8a. Additional DTI metrics support (MD, RD, AD)
   - 8b. Statistical comparison overlays
   - 8c. Batch processing for multiple subjects
   - 8d. Quality control visualization module
   - 8e. Export functionality enhancements (high-res images, videos)

---

**Current Status:** Phase 1 (Component 1 & 2 complete, Components 3 in development) & Phase 2 (Shiny app in active development)

**Next Priority:** Finalize Component 3 integration with Shiny app