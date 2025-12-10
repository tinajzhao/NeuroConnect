#!/usr/bin/env python3
"""
Component 2: Tract Coordinate Extraction
Extracts start, end, and centroid coordinates for 53 JHU white matter tracts

Requirements: FSL (>=5.0, optional), numpy, pandas, nibabel, scikit-learn
Output: jhu_coordinates.csv with coordinates for all tracts
"""
import os
from pathlib import Path
import numpy as np
import pandas as pd
import nibabel as nib
from sklearn.decomposition import PCA

# 48 base tracts from JHU atlas (ROIs 1-48)
base_tracts = [
    (1, 'ATR_L'), (2, 'ATR_R'),
    (3, 'CST_L'), (4, 'CST_R'),
    (5, 'CGC_L'), (6, 'CGC_R'),
    (7, 'CGH_L'), (8, 'CGH_R'),
    (9, 'FX_MAJOR'), (10, 'FX_MINOR'),
    (11, 'IFO_L'), (12, 'IFO_R'),
    (13, 'ILF_L'), (14, 'ILF_R'),
    (15, 'SLF_L'), (16, 'SLF_R'),
    (17, 'UNC_L'), (18, 'UNC_R'),
    (19, 'SLF_T_L'), (20, 'SLF_T_R'),
    (21, 'ALIC_L'), (22, 'ALIC_R'),
    (23, 'PLIC_L'), (24, 'PLIC_R'),
    (25, 'RLIC_L'), (26, 'RLIC_R'),
    (27, 'ACR_L'), (28, 'ACR_R'),
    (29, 'SCR_L'), (30, 'SCR_R'),
    (31, 'PCR_L'), (32, 'PCR_R'),
    (33, 'PTR_L'), (34, 'PTR_R'),
    (35, 'SS_L'), (36, 'SS_R'),
    (37, 'EC_L'), (38, 'EC_R'),
    (39, 'FX_L'), (40, 'FX_R'),
    (41, 'FXST_L'), (42, 'FXST_R'),
    (43, 'SFO_L'), (44, 'SFO_R'),
    (45, 'TAP_L'), (46, 'TAP_R'),
    (47, 'SCC'), (48, 'GCC'),
]

# 4 additional composite tracts
composite_tracts = ['BCC', 'CC', 'IC', 'CR']


def find_atlas():
    """
    Locate JHU atlas file on system.

    Searches common locations for the JHU white matter atlas.

    Returns
    -------
    str
        Full path to JHU-ICBM-labels-1mm.nii.gz

    Raises
    ------
    FileNotFoundError
        If atlas file not found in any location
    """
    search_paths = [
        Path(__file__).parent.parent.parent / 'data' / 'JHU-ICBM-labels-1mm.nii.gz',
        Path.cwd() / 'data' / 'JHU-ICBM-labels-1mm.nii.gz',
        Path(os.environ.get('FSLDIR', '/usr/share/fsl'))
        / 'data'
        / 'atlases'
        / 'JHU'
        / 'JHU-ICBM-labels-1mm.nii.gz',
    ]

    for path in search_paths:
        if path.exists():
            return str(path)

    # Not found - raise error with download instructions
    raise FileNotFoundError(
        '\nJHU atlas not found!\n'
        'Download: https://neurovault.org/images/1401/\n'
        'Place at: ../../data/JHU-ICBM-labels-1mm.nii.gz\n'
    )


# extracting single tract coordinate

def voxel_to_mni(voxel_coords, affine):
    """
    Transform voxel coordinates to MNI space.

    Parameters
    ----------
    voxel_coords : np.ndarray
        Voxel coordinates [x, y, z]
    affine : np.ndarray
        4x4 affine transformation matrix

    Returns
    -------
    np.ndarray
        MNI coordinates [x, y, z] in millimeters
    """
    homogeneous = np.append(voxel_coords, 1)
    mni_coords = affine @ homogeneous
    return mni_coords[:3]


def extract_tract_coords(atlas_data, atlas_affine, roi_number):
    """
    Extract coordinates for one tract using PCA.

    Parameters
    ----------
    atlas_data : numpy.ndarray
        3D array with integer ROI labels
    atlas_affine : numpy.ndarray
        4x4 voxel-to-MNI transformation matrix
    roi_number : int
        ROI label to extract (1-48)

    Returns
    -------
    dict or None
        Dictionary with 'start', 'end', 'centroid' keys, each containing
        3-element array [x, y, z] in MNI mm; or None if tract has no voxels
    """
    # Find all voxels belonging to this ROI
    mask = atlas_data == roi_number
    voxels = np.argwhere(mask)

    # Check if tract exists
    if len(voxels) == 0:
        return None

    # Locate centroid
    centroid_voxel = voxels.mean(axis=0)

    # Use PCA to find tract direction
    if len(voxels) > 2:
        pca = PCA(n_components=1)
        pca.fit(voxels)
        projections = pca.transform(voxels)

        start_voxel = voxels[projections.argmin()]
        end_voxel = voxels[projections.argmax()]
    else:
        start_voxel = voxels[0]
        end_voxel = voxels[-1]

    return {
        'start': voxel_to_mni(start_voxel, atlas_affine),
        'end': voxel_to_mni(end_voxel, atlas_affine),
        'centroid': voxel_to_mni(centroid_voxel, atlas_affine),
    }


# base tracts loop

def extract_base_tracts(atlas_data, atlas_affine):
    """
    Iterate through base_tracts list and extract coordinates for each ROI.

    Calls extract_tract_coords() for each ROI and compiles results into
    a dataframe.

    Parameters
    ----------
    atlas_data : numpy.ndarray
        3D array with integer ROI labels
    atlas_affine : numpy.ndarray
        4x4 voxel-to-MNI transformation matrix

    Returns
    -------
    pandas.DataFrame
        DataFrame with columns 'roi', 'start_x/y/z', 'end_x/y/z', 
        'centroid_x/y/z'
    """
    results = []

    for roi_num, tract_name in base_tracts:
        coords = extract_tract_coords(atlas_data, atlas_affine, roi_num)

        if coords:
            results.append({
                'roi': tract_name,
                'start_x': coords['start'][0],
                'start_y': coords['start'][1],
                'start_z': coords['start'][2],
                'end_x': coords['end'][0],
                'end_y': coords['end'][1],
                'end_z': coords['end'][2],
                'centroid_x': coords['centroid'][0],
                'centroid_y': coords['centroid'][1],
                'centroid_z': coords['centroid'][2],
            })
            print(f'{tract_name} complete ')
        else:
            print(f'! {tract_name} (no voxels)')

    return pd.DataFrame(results)


# calculate composite tracts

def get_tract_from_df(df, tract_name):
    """
    Get a single tract's coordinates from DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with tract coordinates
    tract_name : str
        Name of the tract to retrieve (e.g., 'CST_L', 'GCC')

    Returns
    -------
    pd.Series or None
        Tract data if found, None otherwise
    """
    match = df[df['roi'] == tract_name]
    return match.iloc[0] if len(match) > 0 else None


def average_tract_coords(*tracts):
    """
    Average coordinates from multiple tracts.

    Parameters
    ----------
    *tracts : pd.Series
        Variable number of tract Series to average

    Returns
    -------
    dict
        Dictionary with averaged coordinates for start, end, and centroid
    """
    n = len(tracts)
    result = {}
    coord_keys = ['start_x', 'start_y', 'start_z',
                  'end_x', 'end_y', 'end_z',
                  'centroid_x', 'centroid_y', 'centroid_z']

    for key in coord_keys:
        result[key] = sum(t[key] for t in tracts) / n

    return result


def calculate_bcc(gcc, scc):
    """
    Calculate body of corpus callosum (BCC) coordinates.

    Computes the midpoint between genu and splenium of corpus callosum.

    Parameters
    ----------
    gcc : pd.Series
        Genu of corpus callosum coordinates
    scc : pd.Series
        Splenium of corpus callosum coordinates

    Returns
    -------
    dict
        BCC coordinates (midpoint between GCC and SCC)
    """
    return {
        'roi': 'BCC',
        'start_x': 0,
        'start_y': (gcc['start_y'] + scc['start_y']) / 2,
        'start_z': (gcc['start_z'] + scc['start_z']) / 2,
        'end_x': 0,
        'end_y': (gcc['end_y'] + scc['end_y']) / 2,
        'end_z': (gcc['end_z'] + scc['end_z']) / 2,
        'centroid_x': 0,
        'centroid_y': (gcc['centroid_y'] + scc['centroid_y']) / 2,
        'centroid_z': (gcc['centroid_z'] + scc['centroid_z']) / 2,
    }


def calculate_full_cc(gcc, bcc, scc):
    """
    Calculate full corpus callosum (CC) coordinates.

    Computes the average of genu, body, and splenium coordinates.

    Parameters
    ----------
    gcc : pd.Series
        Genu of corpus callosum coordinates
    bcc : dict
        Body of corpus callosum coordinates
    scc : pd.Series
        Splenium of corpus callosum coordinates

    Returns
    -------
    dict
        Full CC coordinates (average of GCC, BCC, SCC)
    """
    return {
        'roi': 'CC',
        'start_x': 0,
        'start_y': (gcc['start_y'] + bcc['start_y'] + scc['start_y']) / 3,
        'start_z': (gcc['start_z'] + bcc['start_z'] + scc['start_z']) / 3,
        'end_x': 0,
        'end_y': (gcc['end_y'] + bcc['end_y'] + scc['end_y']) / 3,
        'end_z': (gcc['end_z'] + bcc['end_z'] + scc['end_z']) / 3,
        'centroid_x': 0,
        'centroid_y': (gcc['centroid_y'] + bcc['centroid_y'] + scc['centroid_y']) / 3,
        'centroid_z': (gcc['centroid_z'] + bcc['centroid_z'] + scc['centroid_z']) / 3,
    }


def calculate_composite_tracts(base_df):
    """
    Calculate composite tracts commonly used in DTI studies.

    Computes coordinates for 4 composite tracts: BCC (body of corpus 
    callosum), CC (full corpus callosum), IC (internal capsule), and 
    CR (corona radiata).

    Parameters
    ----------
    base_df : pd.DataFrame
        DataFrame containing base tract coordinates

    Returns
    -------
    list of dict
        List of composite tract dictionaries
    """
    composite = []

    # Get corpus callosum tracts
    gcc = get_tract_from_df(base_df, 'GCC')
    scc = get_tract_from_df(base_df, 'SCC')

    # 1. BCC: Body of corpus callosum
    if gcc is not None and scc is not None:
        bcc = calculate_bcc(gcc, scc)
        composite.append(bcc)
        print('BCC complete')

        # 2. CC: Full corpus callosum
        full_cc = calculate_full_cc(gcc, bcc, scc)
        composite.append(full_cc)
        print('CC complete')

    # 3. IC: Internal Capsule
    ic_tract_names = ['ALIC_L', 'ALIC_R', 'PLIC_L', 'PLIC_R', 'RLIC_L', 'RLIC_R']
    ic_tracts = [get_tract_from_df(base_df, name) for name in ic_tract_names]
    ic_tracts = [t for t in ic_tracts if t is not None]

    if len(ic_tracts) >= 4:
        composite.append({'roi': 'IC', **average_tract_coords(*ic_tracts)})
        print('IC complete')

    # 4. CR: Corona Radiata
    cr_tract_names = ['ACR_L', 'ACR_R', 'SCR_L', 'SCR_R', 'PCR_L', 'PCR_R']
    cr_tracts = [get_tract_from_df(base_df, name) for name in cr_tract_names]
    cr_tracts = [t for t in cr_tracts if t is not None]

    if len(cr_tracts) >= 4:
        composite.append({'roi': 'CR', **average_tract_coords(*cr_tracts)})
        print('CR complete')

    return composite


def save_coordinates(base_df, composite_list, output_file='jhu_coordinates.csv'):
    """
    Save all tract coordinates to CSV file.

    Combines base and composite tract coordinates and saves to the specified
    output location. If output_file is an absolute path, uses it directly.
    Otherwise, saves to the data/ directory relative to the project root.

    Parameters
    ----------
    base_df : pandas.DataFrame
        DataFrame with 48 base tracts
    composite_list : list
        List of dictionaries with composite tract coordinates
    output_file : str, optional
        Output filename (default: 'jhu_coordinates.csv')

    Returns
    -------
    pandas.DataFrame
        Combined DataFrame with all tracts
    """
    # Combine base and additional tracts
    if composite_list:
        composite_df = pd.DataFrame(composite_list)
        combined_df = pd.concat([base_df, composite_df], ignore_index=True)
    else:
        combined_df = base_df

    # Save to CSV
    if os.path.isabs(output_file):
        output_path = output_file
    else:
        project_root = Path(__file__).parent.parent.parent
        data_dir = project_root / 'data'
        data_dir.mkdir(parents=True, exist_ok=True)
        output_path = data_dir / output_file

    combined_df.to_csv(output_path, index=False)

    print(f'\nSaved to: {output_file}')
    print(f'Total tracts: {len(combined_df)}')

    return combined_df


def main():
    """
    Main execution function.

    Loads the JHU white matter atlas, extracts coordinates for 48 base tracts
    and 4 composite tracts, then saves all results to CSV.
    """
    # Locate atlas
    atlas_path = find_atlas()
    print(f'Atlas path: {atlas_path}')

    # Load atlas file
    atlas_img = nib.load(atlas_path)
    atlas_data = atlas_img.get_fdata()
    atlas_affine = atlas_img.affine
    print(f'Shape: {atlas_data.shape}')
    print(f'ROI labels: 1-{int(atlas_data.max())}')

    # Extract 48 base tracts
    base_df = extract_base_tracts(atlas_data, atlas_affine)

    # Calculate 5 additional ROIs
    composite_list = calculate_composite_tracts(base_df)

    # Save all coordinates
    combined_df = save_coordinates(base_df, composite_list)

    # Summary
    print(f'Extracted {len(combined_df)} total tracts')
    print(f'  - {len(base_df)} base tracts')
    print(f'  - {len(composite_list)} additional bilateral/combined ROIs')


if __name__ == '__main__':
    main()