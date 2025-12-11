# Functional Specification

## Table of Contents
- [Background](#background)
- [User Profile](#user-profile)
  - [Primary Audience](#primary-audience)
  - [Secondary Audience](#secondary-audience)
  - [Example User Stories](#example-user-stories)
- [Data Sources](#data-sources)
  - [ADNI DTI Data](#1-alzheimers-disease-neuroimaging-initiative-adni)
  - [JHU White Matter Atlas](#2-jhu-white-matter-atlas)
- [Use Cases](#use-cases)
  - [1: View and Explore Brain Connectivity](#1-view-and-explore-brain-connectivity)
  - [2: Compare Brains](#2-compare-brains-healthy-control-vs-alzheimers)
  - [3: Upload and Visualize Custom Data](#3-upload-and-visualize-custom-data)
  - [4: Export Brain Images](#4-export-brain-images-optional)
  - [5: Validate Data Quality](#5-validate-data-quality-or-preprocessing-results-advanced---optional)

---

## Background

White matter tract connectivity patterns are critical indicators of brain health and cognitive function, particularly in neurodegenerative diseases like Alzheimer's Disease (AD). Diffusion Tensor Imaging (DTI) provides quantitative measures of white matter integrity through metrics such as Fractional Anisotropy (FA) and Mean Diffusivity (MD). However, visualizing these complex 3D structural connectivity patterns remains inaccessible to non-specialists due to: (1) steep learning curves for traditional neuroimaging softwares, (2) technical barriers including programming requirements, and (3) lack of interactive visualization tools designed for educational contexts.

**NeuroConnect addresses this accessibility gap** by providing an interactive visualization tool that makes DTI connectivity data interpretable without specialized training. 
The tool displays 53 major white matter tracts in standardized MNI space, enables comparison across diagnostic groups (i.e. healthy controls vs. AD). By processing ADNI data and presenting it through an intuitive Shiny interface with Plotly 3D rendering, NeuroConnect bridges the gap between complex neuroimaging analysis and accessible visualization for educators, students, researchers, and science communicators.

---

## User Profile


#### Primary Audience

**Students**, **Educators**, and **Science Communicators**. 
These users have varying levels of neuroscience domain knowledge (students learning basic neuroanatomy, professors teaching advanced courses, but share limited neuroimaging technical expertise). They are comfortable with web applications and basic file management but do not have programming skills. Their common need is access to visually compelling, scientifically accurate brain visualizations for presentations, lectures, articles, and educational materials without the barrier of learning complex neuroimaging software. They require real research-grade data (ADNI) to ensure credibility, interactive 3D exploration to enhance understanding of spatial relationships, and the ability to export publication-quality images for their communication purposes.

#### Secondary Audience

**Researchers** (cognitive neuroscience, psychology, neurology), **Data Scientists** collaborating on neuroscience projects, and **Neuroimaging Technical Staff**. 
These users range from PhD students with basic Python skills exploring publicly available DTI data, to data scientists with strong programming backgrounds but limited neuroscience knowledge, to core facility managers with expert-level neuroimaging expertise. Their needs include exploratory data visualization, quality control checks of preprocessing pipelines, custom data upload capabilities, and tools to communicate findings with collaborators of varying technical backgrounds. Unlike primary users, they may upload custom datasets, require programmatic validation of tract extraction quality, and need detailed comparison tables for quantitative analysis alongside visual inspection.

#### Example User Stories
**Sam**
* Sam is an undergraduate student. They have been learning about Alzheimer's Disease and need to create a presentation on it. They want to show differences in the structure of the brain. They want a simple visualization but feel intimidated on where to start. 

**Riley**
* Riley is a researcher. They want to expose their mentees to brain imaging and have them interact with examples. 

**Mike**
* Mike is a neuroscience professor teaching a unit on Alzheimer's Disease. He wants to demonstrate how white matter connectivity deteriorates in AD compared to healthy controls. He needs a simple interface to generate these visualizations for his lectures. Mike is an AD expert but has no experience with diffusion imaging analysis.

**Maria**
* Maria writes about neuroscience for a general audience publication. She wants to create visuals for an article on Alzheimer's research. Maria needs to generate accurate brain images without going through weeks of neuroimaging training. She has science communication skills but no technical imaging background.

**Alex**
* Alex teaches AP Psychology and wants to introduce students to brain imaging techniques. They're looking for an accessible tool that can show real brain data without requiring students to install software or learn programming. Alex has strong teaching skills but limited technical background in neuroimaging.

**Taylor (technical)**
* Taylor runs a university neuroimaging core facility that preprocesses DTI data for multiple research labs. They need to demonstrate data quality to investigators and validate that tract extraction pipelines are working correctly across different studies. Taylor wants automated visualization reports showing tract-level metrics across groups. They're experienced with neuroimaging pipelines but need tools that generate shareable QC reports without custom coding for each project.

**Jordan**
* Jordan is a cognitive neuroscience PhD student writing their literature review on aging and cognition. They want to explore publicly available DTI data to better understand connectivity patterns reported in papers. Jordan has basic Python skills but finds existing neuroimaging software overwhelming and poorly documented.

**Casey**
* Casey is a data scientist collaborating with a neurology research group. They want to test multple glass brain models to identify which best highlights differences between patients and controls. Casey has strong coding skills but limited neuroscience background.
---

## Data Sources

**Privacy Notice:**  
* ADNI data contains Protected Health Information (PHI) and is protected under HIPAA regulations. The data cannot be redistributed and must be obtained directly from ADNI. However, we have provided instructions for requesting access to obtain the same datasets used in our project.

---

### 1. Alzheimer's Disease Neuroimaging Initiative (ADNI) 

<p> Data used in this project was obtained from the Alzheimer’s Disease
Neuroimaging Initiative (ADNI) database (adni.loni.usc.edu). ADNI was launched in
2003 as a public-private partnership, led by Principal Investigator Michael W. Weiner,
MD. The primary goal of ADNI has been to test whether serial magnetic resonance imaging
(MRI), positron emission tomography (PET), other biological markers, and clinical and
neuropsychological assessment can be combined to measure the progression of mild
cognitive impairment (MCI) and early Alzheimer’s disease (AD). The longitudinal, multi-site, observational study, which spans across the U.S. and Canada, consists of older adult participants between the ages of 55 and 90 as they represent the population most at-risk for Alzheimer's Disease. For up-to-date information,
see www.adni-info.org.

A complete listing of ADNI investigators can be found at:
http://adni.loni.usc.edu/wp-content/uploads/how_to_apply/ADNI_Acknowledgement_List.pdf </p>


**For up-to-date information:**  
www.adni-info.org


#### Specific Dataset Used in NeuroConnect
* All_Subjects_DTIROI_MEAN

**What is DTI?**  
Diffusion Tensor Imaging (DTI) is an MRI modality that measures water diffusion in the brain to provide quantitative information about white matter tract structure and integrity.

**What is ROI?**  
Region of Interest (ROI) refers to a specific area or volume within a medical image that is selected for analysis. In this dataset, ROIs correspond to white matter tracts defined by the JHU atlas.


#### Structure of Dataset
The All_Subjects_DTIROI_MEAN dataset contains **298 columns** organized as follows:

**Administrative Columns:**
- Participant ID (RID): Unique subject identifier
- Visit code (VISCODE): Study visit identifier
- Exam date (EXAMDATE): Date of MRI scan

**DTI Metrics:**

For each of 73 white matter tract ROIs, four diffusion metrics are provided:

1. **Fractional Anisotropy (FA)**
   - Ranges from 0 (completely random diffusion) to 1 (highly directional diffusion)
   - Higher values indicate more organized white matter structure
   - Sensitive to white matter integrity and organization
   - Primary metric used in NeuroConnect visualizations

2. **Mean Diffusivity (MD)**
   - Measures the average rate of water diffusion in all directions (mm²/s)
   - Related to overall tissue density and cellular structure
   - Increases with tissue damage or loss of cellular barriers
   - Complementary to FA for assessing white matter health

3. **Radial Diffusivity (RD)**
   - Measures diffusion perpendicular to axon's primary direction (mm²/s)
   - Specifically related to myelin sheath integrity
   - Increases when myelin is damaged or degraded
   - Useful for detecting demyelination

4. **Axial Diffusivity (AD)**
   - Measures diffusion parallel to axon's primary direction (mm²/s)
   - Related to axonal integrity
   - Decreases with axonal damage or beading
   - Complements RD for characterizing specific pathology

**Tract Coverage:**  
Out of the 73 tracts, we can visualize 53 total tracts in NeuroConnect: 48 base tracts from JHU ICBM-DTI-81 atlas + 5 composite regions (GCCB, BCC, SCCB, FULLCC, SUMFX)

**Column Naming Convention:**  
Columns are named as `{TRACT_ABBREVIATION}_{METRIC}`, for example:
- `ACR_L_FA`: Left Anterior Corona Radiata, Fractional Anisotropy
- `GCC_MD`: Genu of Corpus Callosum, Mean Diffusivity


#### How to Access Data
1. Register at [ADNI IDA](https://ida.loni.usc.edu/login.jsp)
2. Submit data use agreement
3. Download "DTI Analysis Summary" (DTIROI spreadsheet)
   - Navigate to: **Download** → **Study Files**
   - Go to **Imaging Data** → **MR Image Analysis** → to download `All_Subjects_DTIROI_MEAN.csv`
   - Select **"Subjects"** → **"Study Entry"** to download `All_Subjects_Study_Entry.csv`
4. Place in `data/` directory


### 2. JHU White Matter Atlas

**Atlas Name:** JHU ICBM-DTI-81 White Matter Labels

**Purpose:** Provides standardized anatomical labels and coordinates for white matter tracts in MNI152 space, enabling NeuroConnect to map ADNI DTI metrics to 3D spatial positions.

**Citation:**
> Mori, S., Oishi, K., Jiang, H., et al. (2008). Stereotaxic white matter atlas based on diffusion tensor imaging in an ICBM template. *NeuroImage*, 40(2), 570-582.

#### How to Access JHU Atlas

**Option A - If you have FSL Installation:**
```bash
# Atlas automatically available at:
$FSLDIR/data/atlases/JHU/JHU-ICBM-labels-1mm.nii.gz
```

**Option B - Manual Download:**
1. Download from [NeuroVault](https://neurovault.org/images/1401/)
2. Place `JHU-ICBM-labels-1mm.nii.gz` in `data/` directory

**Note:** NeuroConnect repository includes pre-extracted coordinates (`jhu_coordinates.csv`), so most users do not need to download the atlas file unless they want to:
- Re-run coordinate extraction with different parameters
- Modify the tract selection
- Adapt the tool for a different atlas


#### Tract Mapping in NeuroConnect

NeuroConnect uses the JHU atlas to extract 3D coordinates (start, end, centroid) for each tract, stored in `data/jhu_coordinates.csv`. The coordinate extraction uses srcript src/neuroconnect/extract_coords.py:

1. Loads the JHU atlas NIfTI file
2. For each ROI label (1-48), extracts all voxels belonging to that tract
3. Uses PCA to determine tract directionality and compute start/end points
4. Converts voxel coordinates to MNI millimeter coordinates using the affine transformation
5. Computes tract centroid (center of mass)
6. Calculates 5 additional composite regions by averaging bilateral tracts or combining corpus callosum subregions

**Output:** `jhu_coordinates.csv` with 53 rows (tracts) × 10 columns (roi, start_xyz, end_xyz, centroid_xyz)

---

## Use Cases

### 1: View and Explore Brain Connectivity

**Objective:** A user wants to visualize white matter tract connectivity patterns to understand brain structure or prepare educational materials.

**User profiles:** Educators, students, science communicators, general public

**Expected Interactions:**
1. User opens NeuroConnect web application
2. System displays default demo CN data with 3D brain visualization
3. User clicks and drags to rotate brain view
4. System updates rendering in real-time
5. User enters tract IDs (e.g., "GCC, BCC") in highlight field
6. User clicks "Render / Update"
7. System highlights specified tracts with increased visibility
8. User adjusts camera view using dropdown menu
9. System changes perspective to selected view

**Components:** User data, data validation and processing, brain visualization, user interaction

---

### 2: Compare Brains (Healthy Control vs. Alzheimer's)

**Objective:** A user wants to compare white matter connectivity patterns between Cognitively Normal (CN) and Alzheimer's Disease (AD) groups to identify structural differences characteristic of neurodegeneration.

**User profiles:** Educators, students, science communicators

**Expected Interactions:**
1. User clicks "Use demo (CN)" button
2. System loads CN dataset and displays confirmation
3. User clicks "Use demo (AD)" button
4. System loads AD dataset and displays confirmation
5. User selects "Side-by-side" view mode
6. User clicks "Render / Update"
7. System generates two 3D visualizations (CN left, AD right)
8. User rotates both brains simultaneously
9. User switches to "Brain differences" view mode
10. User clicks "Render / Update"
11. System computes FA differences (AD - CN) and displays with diverging colormap
12. User reviews comparison table showing quantitative differences

**Components:** User data, data validation and processing, brain visualization, user interaction

---

### 3: Upload and Visualize Custom Data

**Objective:** A researcher or technical user wants to upload their own DTI coordinate and metric data to visualize connectivity patterns for a custom dataset (e.g., from a different study, atlas, or patient population).

**User profiles:** Researchers, data scientists collaborating on brain projects

**Expected Interactions:**
1. User prepares CSV file with columns: x, y, z, id, group, value
2. User clicks "Browse..." button for CN CSV upload
3. System opens file selection dialog
4. User selects custom CSV file
5. System validates required columns (x, y, z)
6. System displays confirmation: "File uploaded: [filename] (N nodes)"
7. If validation fails, system displays error message specifying missing columns
8. User clicks "Render / Update"
9. System normalizes data and generates 3D visualization

**Components:** User data upload, data validation and processing, brain visualization, user interaction

---

### 4: Export Brain Images (Optional)

**Objective:** A user wants to export high-quality brain visualization images for use in presentations, publications, or educational materials.

**User profiles:** Science communicators, researchers, students

**Expected Interactions:**
1. User configures visualization with desired settings
2. User clicks "Render / Update"
3. System displays final visualization
4. User hovers over visualization to reveal Plotly toolbar
5. User clicks camera icon for export options
6. User selects "Download plot as png"
7. System exports PNG file
8. User saves file with descriptive name

**Components:** Brain visualization, user interaction, export functionality

---

### 5: Validate Data Quality or Preprocessing Results (Advanced - Optional)

**Objective:** A technical user (neuroimaging staff, core facility manager) wants to perform quality control checks on preprocessed DTI data to ensure tract extraction pipelines worked correctly.

**User profiles:** Neuroimaging technical staff, core facility managers, experienced researchers

**Expected Interactions:**
1. User uploads preprocessed DTI CSV file
2. System validates and computes group-level statistics
3. User clicks "Render / Update"
4. System displays tract connectivity visualization
5. User identifies anomalous FA values visually
6. User reviews comparison table for quantitative outliers
7. User exports QC visualizations for reporting

**Components:** Data validation and processing, quality control panels, brain visualization
