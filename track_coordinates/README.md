## General uses

This package uses the preprocessed & analyzed DTI metrics from the ADNI dataset (citation).

The FA image from the JHU DTI atlas (Mori et al., 2008) is registered to each subject

The node coordinates are extracetd based on the JHU atlas template using the extract_coordinates.py. The start, end, and centroid coordinates (x,y,z) for each of the 54 tracts (see table for reference) is stored in jhu_coordinates_adni.csv. 


## To use the package on a separate dataset

* If the data is processed in the same manner as ADNI (citation) and registered to the JHU atlas, used the same coordinates file;
* If using a different atlas for white matter tracts, use the extract_coordinates.py for the corresponding atlas. 


## Components in extract_coordinates.py

1. Name: altas loader
What it does: 
Inputs (with type information): 
Outputs (with type information): 
How it uses other components: 
Side effects: 

2. 



## References
Mori S, Oishi K, Jiang H, Jiang L, Li X, Akhter K, Hua K, Faria AV, Mahmood A, Woods R, Toga AW, Pike GB, Neto PR, Evans A, Zhang J, Huang H, Miller MI, van Zijl P, Mazziotta J (Stereotaxic white matter atlas based on diffusion tensor imaging in an ICBM template. Neuroimage 40:570-582.2008).