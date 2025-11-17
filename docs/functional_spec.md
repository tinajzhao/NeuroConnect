# Functional Specification

## User Profile

---

## Data Sources
* What data you will use and how it is structured.

---

### Alzheimer's Disease Neuroimaging Initiative (ADNI) 

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

#### Dataset Used in NeuroConnect
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


---

## Use Cases