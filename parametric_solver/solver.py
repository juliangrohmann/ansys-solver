import abc
import pickle
import os
import time
import sys
import hashlib
import json
import enum
import numpy as np
import pandas as pd
import shutil
from ansys.mapdl.core.errors import MapdlExitedError

PARENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(PARENT_DIR)

import parametric_solver.inp as inp
from parametric_solver.apdl_result import APDLResult
from apdl_util.util import get_mapdl
from apdl_util import util

class ParametricSolver(abc.ABC):
    """
    Base class for parametric solving.
    Implements PyMAPDL interface.
    """
    def __init__(self, write_path="", **kwargs):
        """
        Initializes the solver and processes the input file.

        Parameters
        ----------
        inp_file: str
            The path to the Ansys Mechanical *.input file that will be used as a baseline
            before any parametric values are modified.

        write_path: str, optional
            The path at which solutions will be stored, and from which previous solutions are read.

        **kwargs:
            Keyword arguments to be passed during PyMAPDL instance creation. See PyMAPDL documentation (launch_mapdl).

        Notes:
            An initial input file in the correct format can be exported from Ansys Mechanical or APDL.
            The input file will be modified to exclude solving.
        """
        self._samples = []
        self._write_path = write_path
        self._mapdl_kwargs = kwargs

    @property
    def samples(self):
        """
        Accessor to the sample list.

        Returns
        -------
        list
            The list containing all added samples at which a solution is to be obtained, or has already been obtained.
        """
        return self._samples

    def result_from_name(self, name):
        """
        Parameters
        ----------
        Name of the sample for which to retrieve the result.

        Returns
        -------
        `:class:`APDLResult
            The result that corresponds to the sample with the given name.
            If the no sample with the given name exists, or if the sample is
            unsolved, returns None.
        """
        target_sample = None
        for sample in self._samples:
            if sample.name == name:
                target_sample = sample
                break

        if target_sample:
            filepath = os.path.join(self._write_path, self._eval_filename(target_sample))
            if os.path.exists(filepath):
                with open(filepath, "rb") as f:
                    print(f"Loading cached result from {filepath} ...")
                    return pickle.load(f)

        return None

    def solve(self, read_cache=True, verbose=False, kill=False):
        """
        Solves all added samples and writes the results to the write directory.

        Parameters
        -------
        read_cache: bool, optional
            If True, reads existing result from the write directory when available instead of resolving,
            otherwise solves the sample again and overwrites the existing result.

        verbose: bool, optional
            If True, prints additional output for debugging to the console,
            otherwise only prints minimal output.

        Notes
        -----
        This method can also be used to load and access the existing results if they have already been solved
        at the provided samples and are located in the write directory.
        """
        i = 1
        n = len(self._samples)

        for sample in self._samples:
            print(f"Solving [{i}/{n}]")
            print(f"Sample: {sample}")

            filepath = os.path.join(self._write_path, self._eval_filename(sample))
            if read_cache and os.path.exists(filepath):
                print(f"Cached result available.")
            else:
                while True:
                    try:
                        result = self._solve_sample(
                                sample,
                                verbose=verbose,
                                kill=kill)
                        break
                    except MapdlExitedError:
                        print("MAPDL Exited Error. Continuing ...")
                        util.clear_mapdl()
                        
                with open(filepath, "wb") as f:
                    print(f"Caching result at {filepath} ...")
                    pickle.dump(result, f)

            i += 1

    @abc.abstractmethod
    def _setup_solve(self, sample, mat_ids, mapdl_inst):
        pass

    @abc.abstractmethod
    def _eval_filename(self, sample):
        pass

    def _solve_sample(self, sample, mat_ids=(2, 4, 6), verbose=False, kill=False):
        _mapdl = get_mapdl(kill=kill, **self._mapdl_kwargs)

        if not inp.is_inp_valid(sample.input):
            print(f"Unprocessed input file: {sample.input}")
            print("Processing ...")
            inp.process_invalid_inp(sample.input)

        _mapdl.clear()
        _mapdl.input(sample.input)

        self._setup_solve(sample, mat_ids, _mapdl)

        _mapdl.finish()
        _mapdl.slashsolu()

        print(f"Starting to solve sample {sample} ...")
        _mapdl.solve(verbose=verbose)
        print(f"Done solving sample {sample}.")

        _mapdl.finish()

        return APDLResult(_mapdl.result)


class BilinearSolver(ParametricSolver):
    """
    Parametric solver for sampling of elasticity and bilinear plasticity.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def add_sample(self, elastic_mod, yield_strength, tangent_mod):
        """
        Adds a sample to the solver.

        Parameters
        ----------
        elastic_mod: int
            The elastic modulus in the input file's units.

        yield_strength: int
            The yield strength in the input file's units.

        tangent_mod: int
            The tangent modulus in the input file's units.
        """
        self.samples.append((elastic_mod, yield_strength, tangent_mod))

    def _eval_filename(self, sample):
        return f"e{_num_to_identifier(sample[0])}_" \
               f"y{_num_to_identifier(sample[1])}_" \
               f"t{_num_to_identifier(sample[2])}.pkl"

    def _setup_solve(self, sample, mat_ids, mapdl_inst):
        elastic_mod, yield_strength, tangent_mod = sample

        for mat_id in mat_ids:
            _set_property_value(elastic_mod, MatProp.ELASTIC_MODULUS, mat_id, mapdl_inst)
            _set_bilinear_plasticity_values(yield_strength, tangent_mod, mat_id, mapdl_inst)


class PowerLawSolver(ParametricSolver):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def add_sample(self, elastic_mod, yield_strength, exponent):
        """
        Adds a sample to the solver.

        Parameters
        ----------
        elastic_mod: int
            The elastic modulus in the input file's units.

        yield_strength: int
            The yield strength in the input file's units.

        exponent: float
            The power law's exponent.

        Notes
        -----
        The power law equation used to model plasticity:

        stress = yield_strength * (plastic_strain ** exponent)
        """
        self.samples.append((elastic_mod, yield_strength, exponent))

    def _eval_filename(self, sample):
        return f"e{_num_to_identifier(sample[0])}_" \
               f"y{_num_to_identifier(sample[1])}_" \
               f"n{_num_to_identifier(sample[2])}.pkl"

    def _setup_solve(self, sample, mat_ids, mapdl_inst):
        elastic_mod, yield_strength, exponent = sample

        for mat_id in mat_ids:
            _set_property_value(elastic_mod, MatProp.ELASTIC_MODULUS, mat_id, mapdl_inst)
            _set_power_law_plasticity_values(yield_strength, exponent, mat_id, mapdl_inst)


class BilinearThermalSolver(ParametricSolver):
    """
    Parametric solver for sampling of:
        - Elasticity
        - Plasticity (Bilinear)
        - Pressure loads
        - Thermal loads
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def add_sample(self, sample):
        """
        Adds a sample to the solver.

        Parameters
        ----------
        sample: `:class:`BilinearThermalSample
            Instance of BilinearThermalSample that specifies the properties of the sample.
            All properties are optional; to leave a property unchanged from the provided input file, omit setting it in the sample.
        """
        self.samples.append(sample)

    def _eval_filename(self, sample):
        return f"{sample}.pkl"

    def _setup_solve(self, sample, mat_ids, mapdl_inst):
        for mat_id in mat_ids:
            for prop in MatProp:
                value = sample.get_property(prop)
                if value is None:
                    continue

                if isinstance(value, np.ndarray) and value.shape[0] > 1:
                    _set_temperature_table(value, prop.value, mat_id, mapdl_inst)
                else:
                    _set_property_value(value, prop.value, mat_id, mapdl_inst)

            if sample.hill is not None:
                _set_hill_table(sample.hill, mat_id, mapdl_inst)

            if sample.plasticity is not None:
                if isinstance(sample.plasticity, np.ndarray) and sample.plasticity.shape[0] > 1:
                    _set_bilinear_plasticity_table(sample.plasticity, mat_id, mapdl_inst)
                else:
                    _set_bilinear_plasticity_values(sample.plasticity[0], sample.plasticity[1], mat_id, mapdl_inst)
            else:
                _remove_plasticity(mat_id, mapdl_inst)

        if sample.pressure_loads:
            for pressure in sample.pressure_loads:
                _add_pressure_load(*pressure, mapdl_inst)

        if sample.thermal_loads:
            for thermal in sample.thermal_loads:
                _add_thermal_load(thermal, mapdl_inst)


class BilinearThermalSample:
    def __init__(self):
        self._name = None
        self._input = None
        self._plasticity = None
        self._hill = None
        self._properties = {}
        self._pressure_loads = []
        self._thermal_loads = []

    @property
    def name(self):
        """
        Returns
        -------
        str
            Name of the sample. This name will be used as the solution filename, and to
            determine if the sample has already been solved.

        Notes
        -----
        If the name is unassigned in the sample, a unique name based on the remaining properties
        will be used.
        """
        return self._name

    @name.setter
    def name(self, value):
        """
        Parameters
        -------
        value: str
            Name to assign to the sample. This name will be used as the solution filename, and to
            determine if the sample has already been solved.

        Notes
        -----
        If the name is unassigned in the sample, a unique name based on the remaining properties
        will be used.
        """
        self._name = value

    @property
    def input(self):
        return self._input

    @input.setter
    def input(self, value):
        self._input = value

    def get_property(self, mat_prop):
        """
        Parameters
        ----------
        mat_prop: `:class:`MatProp
            The MatProp enum constant that defines the property type to retrieve.

        Returns
        -------
        float or np.array
            The float value specified for the property, or an (n x 2) array that represents the
            temperature table of the property. If undefined, returns None.

        Notes
        -----
        Units are determined by the input file of the parametric solver to which the sample is added.
        """
        if mat_prop.value in self._properties:
            return self._properties[mat_prop.value]
        else:
            return None

    def set_property(self, mat_prop, value):
        """
        Parameters
        ----------
        mat_prop: `:class:`MatProp
            The MatProp enum constant that defines the property type to retrieve.

        value: float or np.array
            The value to assign to the property, or the (n x 2) temperature table
            if defining temperature dependent behavior.

        Returns
        -------
        float or np.array
            The float value specified for the property, or an (n x 2) array that represents the
            temperature table of the property. If undefined, returns None.

        Notes
        -----
        Units are determined by the input file of the parametric solver to which the sample is added.
        Set to None to clear a previously set property.
        """
        self._properties[mat_prop.value] = value

    @property
    def plasticity(self):
        """
        Returns
        -------
        collection
            For temperature dependent behavior, returns an (n x 3) np.array in
            the following format:
                Column 0: Temperatures
                Column 1: Yield strengths
                Column 2: Tangent modulus (strain-hardening modulus)

            Otherwise, returns a (1 x 2) collection in the
            format (yield_strength, tangent_modulus).

            If undefined, returns None.

        Notes
        -----
        Units are determined by the input file of the parametric solver to which the sample is added.
        """
        return self._plasticity

    @plasticity.setter
    def plasticity(self, value):
        """
        Parameters
        ----------
        value: collection
            For temperature dependent behavior, a (n x 3) np.array in
            the following format:
                Column 0: Temperatures
                Column 1: Yield strengths
                Column 2: Tangent modulus (strain-hardening modulus)

            Otherwise, a (1 x 2) collection in the
            format (yield_strength, tangent_modulus).

            Set to None to clear previously set plasticity values.

        Notes
        -----
        Units are determined by the input file of the parametric solver to which the sample is added.
        """
        self._plasticity = value

    @property
    def hill(self):
        return self._hill

    @hill.setter
    def hill(self, value):
        self._hill = value

    @property
    def pressure_loads(self):
        """
        Returns
        -------
        list of tuple
            A list of 2-tuples where each tuple represents a pressure load applied to a component in
            the format (pressure_filepath, component_name).
        """
        return self._pressure_loads

    def add_pressure_load(self, filepath, component):
        """
        Parameters
        ----------
        filepath: str
            Path to the file that defines the pressure load. The extensions of the file should be included.
            Should be an absolute directory if the file is not in the working directory.

        component: str
            Name of the component to which the load is applied. Provided component name needs to be defined
            in the input file of the parametric solver to which the sample is added.
        """
        self._pressure_loads.append((filepath, component))

    def clear_pressure_loads(self):
        """
        Removes all pressure loads from the sample.
        """
        self._pressure_loads.clear()

    @property
    def thermal_loads(self):
        """
        Returns
        -------
        list of lists
            A list of lists where each inner list represents a pressure load applied to a component.
            The general format is [[pressure_filepath, component_name], [...]].
        """
        return self._thermal_loads

    def add_thermal_load(self, filepath):
        """
        Parameters
        ----------
        filepath: str
            Path to the file that defines the thermal load. The extensions of the file should be included.
            Should be an absolute directory if the file is not in the working directory.
        """
        self._thermal_loads.append(filepath)

    def clear_thermal_loads(self):
        """
        Removes all thermal loads from the sample.
        """
        self._thermal_loads.clear()

    def to_json(self):
        data = {
            '_name': self._name,
            '_plasticity': np.array(self._plasticity).tolist() if self._plasticity is not None else None,
            '_properties': {key: np.array(value).tolist() if isinstance(value, (list, tuple, np.ndarray)) else value
                            for key, value in self._properties.items()},
            '_pressure_loads': self._pressure_loads,
            '_thermal_loads': self._thermal_loads
        }

        return json.dumps(data)

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)

        instance = cls()
        instance._name = data['_name']
        instance._plasticity = np.array(data['_plasticity']) if data['_plasticity'] is not None else None
        instance._properties = {key: np.array(value) if isinstance(value, list) else value for key, value in data['_properties'].items()}
        instance._pressure_loads = data['_pressure_loads']
        instance._thermal_loads = data['_thermal_loads']

        return instance

    def __hash__(self):
        input_str = self.__str__()
        input_bytes = input_str.encode()

        hash_obj = hashlib.sha256()
        hash_obj.update(input_bytes)
        unique_hash = hash_obj.digest()

        return int.from_bytes(unique_hash, byteorder='big')

    def __str__(self):
        if self._name:
            return self._name

        input_str = ""

        for prop in MatProp:
            if self.get_property(prop) is not None:
                input_str += str(self.get_property(prop))

        if self.plasticity is not None:
            input_str += str(self.plasticity)

        if self._pressure_loads:
            for load in self._pressure_loads:
                input_str += f"p{_file_to_checksum(load[0], digits=6)}_c{load[1]}_"

        if self._thermal_loads:
            for load in self._thermal_loads:
                input_str += f"t{_file_to_checksum(load, digits=6)}_"

        hash_obj = hashlib.sha256()
        hash_obj.update(input_str.encode())
        unique_hash = hash_obj.hexdigest()
        return unique_hash


class MatProp(enum.Enum):
    DENSITY = 'DENS'
    POISSONS_RATIO = 'NUXY'
    ELASTIC_MODULUS = 'EX'
    THERMAL_EXPANSION = 'CTEX'
    THERMAL_CONDUCTIVITY = 'KXX'


def _set_property_value(value, mat_prop, mat_id, mapdl_inst):
    print(f"Setting property {mat_prop} for material id {mat_id} ...")
    print(f"Value: {value}")

    mapdl_inst.prep7()
    mapdl_inst.mp(mat_prop, mat_id, value)
    mapdl_inst.finish()


def _set_temperature_table(table, mat_prop, mat_id, mapdl_inst):
    print(f"Setting temperature table property {mat_prop} for material id {mat_id} ...")
    print("Table:")
    print(table)

    mapdl_inst.prep7()

    mapdl_inst.mptemp()
    for i, temp in enumerate(table[:, 0]):
        print(f"Adding table temperature: {i + 1}, {temp}")
        mapdl_inst.mptemp(i + 1, temp)
    for i, value in enumerate(table[:, 1]):
        print(f"Adding table {mat_prop} value: {i + 1}, {value}")
        mapdl_inst.mpdata(mat_prop, mat_id, i + 1, value)

    mapdl_inst.finish()


def _set_bilinear_plasticity_values(yield_strength, tangent_mod, mat_id, mapdl_inst):
    _set_bilinear_plasticity_table(np.array([[22, yield_strength, tangent_mod]]), mat_id, mapdl_inst)


def _set_bilinear_plasticity_table(table, mat_id, mapdl_inst):
    print(f"Setting bilinear plasticity for material id {mat_id} ...")
    print("Table:")
    print(table)

    mapdl_inst.prep7()

    n = table.shape[0]

    mapdl_inst.tbdele("PLAS", mat_id)
    mapdl_inst.tb("PLAS", mat_id, n, "", "BISO")

    for i in range(n):
        mapdl_inst.tbtemp(table[i, 0])
        mapdl_inst.tbdata(1, table[i, 1], table[i, 2])

    mapdl_inst.finish()


def _set_hill_table(table, mat_id, mapdl_inst):
    print(f"Setting hill table for material id {mat_id} ...")
    print("Table:")
    print(table)

    mapdl_inst.prep7()

    n = table.shape[0]

    mapdl_inst.tbdele("HILL", mat_id)
    mapdl_inst.tb("HILL", mat_id, n)

    for i in range(n):
        mapdl_inst.tbtemp(table[i, 0])
        mapdl_inst.tbdata(1, table[i, 1], table[i, 2], table[i, 3], table[i, 4], table[i, 5], table[i, 6])

    mapdl_inst.finish()


def _set_power_law_plasticity_values(yield_strength, exponent, mat_id, mapdl_inst):
    print(f"Setting power law plasticity for material id {mat_id}:")
    print(f"Yield strength = {yield_strength}")
    print(f"Exponent = {exponent}")

    mapdl_inst.prep7()

    mapdl_inst.tbdele("PLAS", mat_id)
    mapdl_inst.tb("PLAS", mat_id, "", "", "NLISO")
    mapdl_inst.tbdata(1, yield_strength, exponent)

    mapdl_inst.finish()


def _remove_plasticity(mat_id, mapdl_inst):
    print(f"Removing plasticity for material id {mat_id} ...")
    mapdl_inst.prep7()
    mapdl_inst.tbdele("PLAS", mat_id)
    mapdl_inst.finish()


def _add_pressure_load(filename, component, mapdl_inst):
    print(f"Applying pressure load at {filename} to {component} ...")
    name = os.path.basename(filename)

    mapdl_inst.slashmap()

    mapdl_inst.ftype("CSV", 0)
    mapdl_inst.read(filename, 1, "", 2, 3, 4, 5)
    mapdl_inst.target(component)
    mapdl_inst.map()
    mapdl_inst.show()
    mapdl_inst.plgeom()

    temp_dir = os.path.join(os.getcwd(), 'temp')
    if not os.path.exists(temp_dir):
        os.mkdir(temp_dir)

    temp_file = os.path.join(temp_dir, name)
    mapdl_inst.writemap(temp_file)
    mapdl_inst.finish()

    mapdl_inst.slashsolu()
    mapdl_inst.input(temp_file)
    mapdl_inst.finish()

    shutil.rmtree(temp_dir)


def _add_thermal_load(filename, mapdl_inst):
    print(f"Applying thermal load at {filename} ...")

    # print(f"Working dir = {os.getcwd()}")
    # filename = filename.replace('\\', '/')
    # real_filename, ext = os.path.splitext(filename)
    # ext = ext.replace('.', '')
    # print(f"Real filename = {real_filename}")
    #
    # mapdl_inst.cmsel("S", component)
    # mapdl_inst.nsle("R", "ACTIVE")
    #
    # mapdl_inst.prep7()
    #
    # skiplines = 1
    # numlines_str = mapdl_inst.inquire("numlines", "LINES", real_filename, ext)
    # numlines = int(numlines_str.split('.')[0])
    # print(f"numlines_str = {numlines_str}, numlines = {numlines}")
    #
    # mapdl_inst.dim("temp_data", "TABLE", numlines - skiplines - 1, 4)
    # mapdl_inst.tread("temp_data", real_filename, ext, skiplines)
    #
    # # mapdl_inst.starstatus("temp_data")
    #
    # mapdl_inst.dim("locs", "ARRAY", numlines - skiplines, 3)
    # mapdl_inst.dim("near_nodes", "ARRAY", numlines - skiplines)
    # mapdl_inst.dim("temp_vals", "ARRAY", numlines - skiplines)
    #
    # mapdl_inst.vfun("locs(1,1)", "copy", "temp_data(0, 1)")
    # mapdl_inst.vfun("locs(1,2)", "copy", "temp_data(0, 2)")
    # mapdl_inst.vfun("locs(1,3)", "copy", "temp_data(0, 3)")
    # mapdl_inst.vfun("temp_vals(1)", "copy", "temp_data(0, 4)")
    #
    # # mapdl_inst.starstatus("locs")
    # # mapdl_inst.starstatus("temp_vals")
    #
    # mapdl_inst.starvget("interp_nodes", "NODE", "", "NLIST")
    #
    # interp_count = mapdl_inst.get("interp_count", "NODE", "", "COUNT")
    # print(f"interp_count = {interp_count}")
    # mapdl_inst.dim("interp_locs", "ARRAY", interp_count, 3)
    #
    # # mapdl_inst.starstatus("near_nodes")
    #
    # loc_code = """
    # *DO,i,1,interp_count
    #     *GET,interp_locs(i,1),NODE,interp_nodes(i),LOC,X
    #     *GET,interp_locs(i,2),NODE,interp_nodes(i),LOC,Y
    #     *GET,interp_locs(i,3),NODE,interp_nodes(i),LOC,Z
    # *ENDDO
    # """
    #
    # mapdl_inst.input_strings(loc_code)
    #
    # for i in range(1, 10):
    #     print(mapdl_inst.com(f"X %interp_locs({i},1)% Y %interp_locs({i},2)% Z %interp_locs({i},3)%"))
    #
    # mapdl_inst.moper("interp_temp", "interp_locs", "MAP", "temp_vals", "locs")
    #
    # mapdl_inst.starstatus("interp_temp")
    #
    # mapdl_inst.bf("", "TEMP", "%temp_data%")

    # legacy:
    # mapdl_inst.dim("extnode", "ARRAY", numlines - skiplines)
    # mapdl_inst.dim("extdat", "ARRAY", numlines - skiplines)
    #
    # mapdl_inst.vfun("extnode(1)", "copy", "node_data(1, 0)")
    # mapdl_inst.vfun("extdat(1)", "copy", "node_data(1, 1)")
    #
    # apdl_code = """
    # *DO,i,1,numlines - skiplines
    #     BF,extnode(i),TEMP,extdat(i) - 273.15
    # *ENDDO
    # """

    # mapdl_inst.run(f"skiplines = {skiplines}")
    # mapdl_inst.input_strings(apdl_code)

    # mapdl_inst.esel("ALL")
    # mapdl_inst.nsel("ALL")
    #
    # mapdl_inst.finish()

    filename = filename.replace('\\', '/')

    mapdl_inst.slashsolu()
    mapdl_inst.input(filename)
    mapdl_inst.finish()


def _curr_dir():
    return os.path.dirname(os.path.abspath(__file__))


class NodeContext:
    """
    Retrieves and stores the following information relating to the nodes of the model:
        - The ids of the nodes belonging to each component
        - The coordinates of each node
    """
    def __init__(self, inp_file):
        """
        Parameters
        ----------
        inp_file: str
            The path to the Ansys Mechanical *.input file from which the nodes will be read.
        """
        self._inp_file = inp_file
        self._components = []
        self._component_map = {}

    def add_component(self, component, inactive=True, mid=True, elements=False):
        """
        Registers a component name for which to retrieve and store nodal information.

        Parameters
        ----------
        component: str
            The name of the component.

        inactive: bool
            Whether to store inactive nodes

        mid: bool
            Whether to store mid-nodes

        elements: bool
            Whether the named selection is defined as an element selection
        """
        self._components.append((component, inactive, mid, elements))

    def result(self, component):
        return self._component_map[component]

    def write(self, component, path, mult=None):
        self._component_map[component].to_csv(path)
        # out = ""
        # locs = self.location_map(component)
        #
        # for node in locs.keys():
        #     vals = locs[node]
        #
        #     if mult is not None:
        #         vals = [val * mult for val in vals]
        #
        #     str_locs = [str(loc) for loc in vals]
        #     out += ','.join([str(node), *str_locs]) + '\n'
        #
        # with open(path, 'w') as f:
        #     f.write(out)

    def run(self, **kwargs):
        """
        Retrieves and stores the nodal information for each registered component name.
        """
        _mapdl = get_mapdl(**kwargs)

        _mapdl.clear()
        _mapdl.input(self._inp_file)

        for component, inactive, mid, elements in self._components:
            print(f"Caching {component} ...")

            if component.lower() == 'all':
                _mapdl.esel("ALL")
            else:
                _mapdl.cmsel("S", component)

            if elements:
                _mapdl.nsle("S", "ALL")

            if not inactive:
                _mapdl.nsle("R", "ACTIVE")

            if not mid:
                _mapdl.nsle("U", "MID")

            data = []
            node_list = _mapdl.nlist()
            for line in node_list.split('\n'):
                vals = line.split()[:4]
                if len(vals) < 4:
                    continue

                try:
                    vals = [int(vals[0]), float(vals[1]), float(vals[2]), float(vals[3])]
                except ValueError:
                    continue

                data.append(vals)

            df = pd.DataFrame(data, columns=['node', 'x', 'y', 'z'])
            df.set_index(df.columns[0], inplace=True)
            self._component_map[component] = df


def _eval_remaining_time(start_time, completed, remaining):
    if completed == 0:
        return "Unknown"

    elapsed = time.time() - start_time
    dt = elapsed / elapsed
    return _seconds_to_str(remaining * dt)


def _seconds_to_str(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:2d}h:{minutes:02d}m:{seconds:02d}s"


def _num_to_identifier(num):
    if num == 0:
        return "0e0"

    num_str = "{:.10e}".format(abs(num))
    significant_digits = ""
    count = 0

    for char in num_str:
        if char.isdigit():
            count += 1
            significant_digits += char
            if count == 3:
                break

    exponent = int(num_str.split("e")[-1]) - 2

    return f"{significant_digits}e{exponent}"


def _file_to_checksum(file_path, digits=-1):
    sha256_hash = hashlib.sha256()

    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)

    return sha256_hash.hexdigest()[:digits]
