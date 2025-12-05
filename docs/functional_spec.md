# Functional Specification

## User Profile

NeuroConnect was developed with the idea of wanting to *make neuroimaging visualizations more approachable and interactive* for non-experts in the field as well as those with limited technical backgrounds. 

#### Primary Audience
* students
* educators
* science communicators 

#### Secondary Audience
* researchers
* collaborators on neuro-related projects (i.e. data scientists)
* neuroimaging specialists 

#### Example User Stories
**Sam**
* Sam is a undergraduate student. They have been learning about Alzheimer's Disease and need to create a presentation on it. They want to show differences in the structure of the brain. They want a simple visualization but feel intimidated on where to start. 

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
* Given the sensitive nature of personal health information (PHI) and its protection under HIPAA, the specific data used in this project cannot be made publicly available. However, we have provided instructions for requesting access to obtain the same datasets used in our project.

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

#### Specific Dataset Used in NeuroConnect
* ADNI_DTIROI_V1

DTI = Diffusion Tensor Imaging
* type of MRI modality that measures water diffusion in the brain to provide information on the structure of white matter tracts

ROI = Region of Interest 
* specific area or volume within a medical image that is selected for analysis

#### Structure of Dataset

Information Within Dataset (242 Columns Total):
* Participant ID
* Imaging Exam Information (e.g. Date of Visit)
* MRI Biomarkers, which are further subdivided by ROI and brain hemisphere (Left/Right):
    * Axial Diffusivity (AD)
        - Measures diffusion of water along (***parallel to***) the axon's primary direction
        - Related to the health and integrity of axons
    * Radial Diffusivity (RD) 
        - Measures diffusion of water moves across (***perpendicular to***) the axon's primary direction
        - Related to the health of the myelin sheath surrounding the axons
    * Mean Diffusivity (MD)
        - Measures the average rate of water diffusion in all directions
        - Related to overall tissue density and cellular structure
    * Fractional Anisotropy (FA) 
        - Measures the degree of directionality of water diffusion
        - Ranges from 0 (completely random) to 1 (highly directional)
        - Related to white matter organization and integrity 

#### How to Access Data
1. Create and log in to account for Image and Data Archive (IDA)
    https://ida.loni.usc.edu/login.jsp

2. 

### 2. JHU White Matter Atlas


---

## Use Cases

**1. View brain connectivity**
* User profiles: educators, students, science communicators, general public
* Components: user data, data validation and processing, brain visualization, user interaction


**2. Compare brains (healthy vs. disease)**
* User profiles: educators, students, science communicators
* Components: user data, data validation and processing, brain visualization, user interaction


**3. Upload and visualize data**
* User profiles: researchers, data scientists collaborating on brain projects
* Components: user data, data validation and processing, brain visualization, user interaction

**4. Export brain images**
* User profiles: science communicators, researchers, students
* Components: user data, data validation and processing, brain visualization, user interaction, export data


**5. Validate Data Quality or Preprocessing Results (we might not get here by the end of the project)**
* User profiles: technical researchers, neuroimaging staff
* Components: QC visualizers