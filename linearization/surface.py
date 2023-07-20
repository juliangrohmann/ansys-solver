import os
import sys
import pathlib
import pandas as pd
import numpy as np
import time
from typing import Tuple

PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PARENT_DIR)

from linearization.vinterp import interpolate_nodal_values
from linearization.linearization import APDLIntegrate
from linearization.scl import SCL
from linearization.pair_component_nodes import LSANodePairer


def pair_nodes(write_path: pathlib.PurePath, top_surface_path: str, bottom_surface_path: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    pair the nodes between the two boundaries and save the pairing "map" that maps
    the nodes (indices on the dataframes) between the two sets of nodes

    Parameters
    ----------
    write_path: pathlib.PurePath
        a pathlib object folder, the parent directory where the save the results

    top_surface_path: str
        path to the top surface nodes file

    bottom_surface_path: str
        path to the bottom surface nodes file

    Returns
    ----------
    Tuple[pd.DataFrame,pd.Dataframe]
        the node locations sorted in order according to the determined mapping

    """

    top_surface_nodes = pd.read_csv(top_surface_path, index_col=0, header=None)
    top_surface_nodes.index = top_surface_nodes.index.astype(int)

    bottom_surface_nodes = pd.read_csv(bottom_surface_path, index_col=0, header=None)
    bottom_surface_nodes.index = bottom_surface_nodes.index.astype(int)

    node_pair = LSANodePairer.from_locations(top_surface_nodes,
                                             bottom_surface_nodes)

    paired_loc = node_pair.pair()

    loc1 = top_surface_nodes.loc[paired_loc[:, 0]]
    loc2 = bottom_surface_nodes.loc[paired_loc[:, 1]]

    if write_path is not None:
        np.save(str(write_path.joinpath('paired.npy')), paired_loc)

    return loc1, loc2


def linearize_stresses(write_path: pathlib.PurePath,
                       loc1: pd.DataFrame,
                       loc2: pd.DataFrame,
                       node_sol: pd.DataFrame,
                       all_locs: str,
                       npoints: int,
                       strain) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Linearize stress fields according to the guidelines provided in ASME
    code/ITER SDC document

    Parameters
    ----------
    write_path: pathlib.PurePath
        a pathlib object folder, the parent directory where the save the results

    loc1: pd.DataFrame
        node locations of the first boundary sorted according to the determined mapping

    loc2: pd.DataFrame
        node locations of the second bounary sorted according to the determined mapping

    node_sol: pd.DataFrame
        stress values at all nodes

    all_locs: pd.DataFrame
        path to all comma separated node locations

    npoints: int
        the number of integration points to interpolate the stress tresults to

    Returns
    -------
    Dict[membrane: np.ndarray,
          bending: np.ndarray,
          peak: np.ndarray]

    membrane,bending, and peak are the membrane,bending and peak bending stresses
    at all intermediate poitns on the plane between the two boundaries
    """

    scl_apdl = SCL(loc1.to_numpy(), loc2.to_numpy())
    scl_points = scl_apdl(npoints, flattened=True)
    
    node_loc = pd.read_csv(all_locs, index_col=0, header=None)
    node_loc = node_loc.loc[node_sol.index]

    scl_sol = interpolate_nodal_values(node_loc.to_numpy(),
                                       node_sol.to_numpy(),
                                       scl_points)
    
    apdl_int = APDLIntegrate(scl_sol, scl_points, npoints)
    membrane = apdl_int.membrane_vm(averaged=True, strain=strain)
    bending = apdl_int.bending_vm(averaged=True, strain=strain)
    peak = apdl_int.peak_vm(averaged=True)
    principal = apdl_int.linearized_principal_stress(averaged=True)
    triaxility_factor = apdl_int.triaxiality_factor(averaged=True)
    location = (loc1.to_numpy() + loc2.to_numpy()) / 2

    if write_path is not None:
        for a, name in zip([membrane, bending, peak, location, principal, triaxility_factor],
                           ['membrane', 'bending', 'peak', 'location', 'principal', 'triaxility_factor']):
            np.save(str(write_path.joinpath(name + '.npy')), a)

    return {
        'membrane': membrane,
        'bending': bending,
        'peak': peak,
        'location': location,
        'principal': principal,
        'triaxility_factor': triaxility_factor
    }


def linearize_surface(top_surface_path, bottom_surface_path, solution, all_locs_path, write_path, strain, npoints=47):
    platform = str(sys.platform)
    if platform == 'unix' or platform == 'posix' or platform == 'linux':
        _path = pathlib.PosixPath
    else:
        _path = pathlib.WindowsPath

    write_path = None if write_path is None else _path(write_path)

    loc1, loc2 = pair_nodes(write_path, top_surface_path, bottom_surface_path)
    return linearize_stresses(write_path, loc1, loc2, solution, all_locs_path, npoints, strain)
