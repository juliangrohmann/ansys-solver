import abc
import pickle
import os
import time
import sys
import hashlib
import json

sys.path.append('..')
from ansys.mapdl.core import launch_mapdl

import parametric_solver.inp as inp
from parametric_solver.apdl_result import APDLResult


_mapdl = None


class ParametricSolver(abc.ABC):
    """
    Base class for parametric solving.
    Implements PyMAPDL interface.
    """
    def __init__(self, inp_file, write_path="", **kwargs):
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
        self._inp_file = inp_file
        self._samples = []
        self._results = {}
        self._write_path = write_path
        self._mapdl_kwargs = kwargs

        if not inp.is_inp_valid(inp_file):
            print("Unprocessed input file. Processing ...")
            inp.process_invalid_inp(inp_file)

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

    @property
    def results(self):
        """
        Accessor to the result dictionary.

        Returns
        -------
        dict
            The dictionary containing all obtained results. Keys are sample tuples, values are APDLResult objects.
        """
        return self._results

    def solve(self, read_cache=True, verbose=False):
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
        start_time = time.time()
        i = 1
        n = len(self._samples)

        for sample in self._samples:
            print(f"Solving [{i}/{n}]\t\tTime Remaining: {_eval_remaining_time(start_time, i - 1, n - i + 1)}")
            print(f"Sample: {sample}")

            filepath = os.path.join(self._write_path, self._eval_filename(sample))
            if read_cache and os.path.exists(filepath):
                with open(filepath, "rb") as f:
                    print(f"Caching result at {filepath} ...")
                    result = pickle.load(f)
            else:
                result = self._solve_sample(
                    sample,
                    self._inp_file,
                    verbose=verbose)

                with open(filepath, "wb") as f:
                    print(f"Caching result at {filepath} ...")
                    pickle.dump(result, f)

            self._results[sample] = result
            i += 1

    @abc.abstractmethod
    def _setup_solve(self, sample, mat_ids, mapdl_inst):
        pass

    @abc.abstractmethod
    def _eval_filename(self, sample):
        pass

    def _solve_sample(self, sample, inp_path, mat_ids=(2, 4, 6), verbose=False):
        global _mapdl

        if not _mapdl:
            _mapdl = _init_mapdl(**self._mapdl_kwargs)

        _mapdl.clear()
        _mapdl.input(inp_path)

        self._setup_solve(sample, mat_ids, _mapdl)

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
    def __init__(self, inp_file, **kwargs):
        super().__init__(inp_file, **kwargs)

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
            _set_elastic_mod(elastic_mod, mat_id, mapdl_inst)
            _set_bilinear_plasticity(yield_strength, tangent_mod, mat_id, mapdl_inst)


class BilinearThermalSolver(ParametricSolver):
    """
    Parametric solver for sampling of:
        - Elasticity
        - Plasticity (Bilinear)
        - Pressure loads
        - Thermal loads
    """
    def __init__(self, inp_file, **kwargs):
        super().__init__(inp_file, **kwargs)

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
            if sample.elastic_mod:
                _set_elastic_mod(sample.elastic_mod, mat_id, mapdl_inst)

            if sample.yield_strength and sample.tangent_mod:
                _set_bilinear_plasticity(sample.yield_strength, sample.tangent_mod, mat_id, mapdl_inst)

        if sample.pressure_loads:
            for pressure in sample.pressure_loads:
                _set_pressure_loads(*pressure, mapdl_inst)

        if sample.thermal_loads:
            for thermal in sample.thermal_loads:
                _set_thermal_loads(*thermal, mapdl_inst)


class PowerLawSolver(ParametricSolver):
    def __init__(self, inp_file, **kwargs):
        super().__init__(inp_file, **kwargs)

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
            _set_elastic_mod(elastic_mod, mat_id, mapdl_inst)
            _set_power_law_plasticity(yield_strength, exponent, mat_id, mapdl_inst)


class BilinearThermalSample:
    def __init__(self):
        self._name = None
        self._elastic_mod = None
        self._yield_strength = None
        self._tangent_mod = None
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
    def elastic_mod(self):
        """
        Returns
        -------
        int
            Elastic modulus of the sample.

        Notes
        -----
        Units are determined by the input file of the parametric solver to which the sample is added.
        """
        return self._elastic_mod

    @elastic_mod.setter
    def elastic_mod(self, value):
        """
        Parameters
        -------
        value: int
            Elastic modulus to set in the sample.

        Notes
        -----
        Units are determined by the input file of the parametric solver to which the sample is added.
        """
        self._elastic_mod = value

    @property
    def yield_strength(self):
        """
        Returns
        -------
        int
            Yield strength of the sample.

        Notes
        -----
        Units are determined by the input file of the parametric solver to which the sample is added.
        """
        return self._yield_strength

    @yield_strength.setter
    def yield_strength(self, value):
        """
        Parameters
        -------
        value: int
            Yield strength to set in the sample.

        Notes
        -----
        Units are determined by the input file of the parametric solver to which the sample is added.
        """
        self._yield_strength = value

    @property
    def tangent_mod(self):
        """
        Returns
        -------
        int
            Tangent modulus (strain hardening modulus) of the sample.

        Notes
        -----
        Units are determined by the input file of the parametric solver to which the sample is added.
        """
        return self._tangent_mod

    @tangent_mod.setter
    def tangent_mod(self, value):
        """
        Parameters
        -------
        value: int
            Tangent modulus (strain hardening modulus) to set in the sample.

        Notes
        -----
        Units are determined by the input file of the parametric solver to which the sample is added.
        """
        self._tangent_mod = value

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
        Returns
        -------
        list of tuple
            A list of 2-tuples where each tuple represents a thermal load applied to a component in
            the format (thermal_filepath, component_name).
        """
        self._pressure_loads.clear()

    @property
    def thermal_loads(self):
        """
        Returns
        -------
        list of tuple
            A list of 2-tuples where each tuple represents a pressure load applied to a component in
            the format (pressure_filepath, component_name).
        """
        return self._thermal_loads

    def add_thermal_load(self, filepath, component):
        """
        Parameters
        ----------
        filepath: str
            Path to the file that defines the thermal load. The extensions of the file should be included.
            Should be an absolute directory if the file is not in the working directory.

        component: str
            Name of the component to which the load is applied. Provided component name needs to be defined
            in the input file of the parametric solver to which the sample is added.
        """
        self._thermal_loads.append((filepath, component))

    def clear_thermal_loads(self):
        """
        Removes all thermal loads from the sample.
        """
        self._thermal_loads.clear()

    def to_json(self):
        data = {
            "elastic_mod": self._elastic_mod,
            "yield_strength": self._yield_strength,
            "tangent_mod": self._tangent_mod,
            "pressure_loads": self._pressure_loads,
            "thermal_loads": self._thermal_loads
        }
        return json.dumps(data)

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        sample = cls()
        sample._elastic_mod = data.get("elastic_mod")
        sample._yield_strength = data.get("yield_strength")
        sample._tangent_mod = data.get("tangent_mod")
        sample._pressure_loads = data.get("pressure_loads", [])
        sample._thermal_loads = data.get("thermal_loads", [])
        return sample

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

        sample_name = ""
        if self._elastic_mod:
            sample_name += f"e{_num_to_identifier(self._elastic_mod)}_"

        if self._yield_strength:
            sample_name += f"e{_num_to_identifier(self._yield_strength)}_"

        if self._tangent_mod:
            sample_name += f"e{_num_to_identifier(self._tangent_mod)}_"

        if self._pressure_loads:
            for load in self._pressure_loads:
                sample_name += f"p{_file_to_checksum(load[0], digits=6)}_c{load[1]}_"

        if self._thermal_loads:
            for load in self._thermal_loads:
                sample_name += f"t{_file_to_checksum(load[0], digits=6)}_c{load[1]}_"

        sample_name = sample_name.rstrip('_')
        return sample_name


def _set_elastic_mod(elastic_mod, mat_id, mapdl_inst):
    print(f"Setting elastic modulus for material id {mat_id} to {elastic_mod} ...")

    mapdl_inst.prep7()

    mapdl_inst.mp("EX", mat_id, elastic_mod)

    mapdl_inst.finish()


def _set_bilinear_plasticity(yield_strength, tangent_mod, mat_id, mapdl_inst):
    print(f"Setting bilinear plasticity for material id {mat_id}:")
    print(f"Yield strength = {yield_strength}")
    print(f"Tangent modulus = {tangent_mod}")

    mapdl_inst.prep7()

    mapdl_inst.tbdele("PLAS", mat_id)
    mapdl_inst.tb("PLAS", mat_id, "", "", "BISO")
    mapdl_inst.tbdata(1, yield_strength, tangent_mod)

    mapdl_inst.finish()


def _set_power_law_plasticity(yield_strength, exponent, mat_id, mapdl_inst):
    print(f"Setting power law plasticity for material id {mat_id}:")
    print(f"Yield strength = {yield_strength}")
    print(f"Exponent = {exponent}")

    mapdl_inst.prep7()

    mapdl_inst.tbdele("PLAS", mat_id)
    mapdl_inst.tb("PLAS", mat_id, "", "", "NLISO")
    mapdl_inst.tbdata(1, yield_strength, exponent)

    mapdl_inst.finish()


def _set_pressure_loads(filename, component, mapdl_inst):
    print(f"Applying pressure load at {filename} to {component} ...")

    mapdl_inst.slashmap()

    mapdl_inst.ftype("CSV", 0)
    mapdl_inst.read(filename, 1, "", 1, 2, 3, 4)
    mapdl_inst.target(component)

    mapdl_inst.finish()


def _set_thermal_loads(filename, component, mapdl_inst):
    print(f"Applying thermal load at {filename} to {component} ...")

    print(f"Working dir = {os.getcwd()}")
    filename = filename.replace('\\', '/')
    real_filename, ext = os.path.splitext(filename)
    ext = ext.replace('.', '')
    print(f"Real filename = {real_filename}")

    mapdl_inst.cmsel("S", component)
    mapdl_inst.nsle("S", "ACTIVE")

    mapdl_inst.prep7()

    skiplines = 1
    numlines_str = mapdl_inst.inquire("numlines", "LINES", real_filename, ext)
    numlines = int(numlines_str.split('.')[0])

    mapdl_inst.dim("node_data", "TABLE", numlines - skiplines)
    mapdl_inst.tread("node_data", real_filename, ext, skiplines)

    mapdl_inst.dim("extnode", "ARRAY", numlines - skiplines)
    mapdl_inst.dim("extdat", "ARRAY", numlines - skiplines)

    mapdl_inst.vfun("extnode(1)", "copy", "node_data(1, 0)")
    mapdl_inst.vfun("extdat(1)", "copy", "node_data(1, 1)")

    apdl_code = """
    *DO,i,1,numlines - skiplines
        BF,extnode(i),TEMP,extdat(i) - 273.15
    *ENDDO
    """

    mapdl_inst.run(f"skiplines = {skiplines}")
    mapdl_inst.input_strings(apdl_code)

    mapdl_inst.esel("ALL")
    mapdl_inst.nsel("ALL")

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

    def add_component(self, component):
        """
        Registers a component name for which to retrieve and store nodal information.

        Parameters
        ----------
        component: str
            The name of the component.
        """
        self._components.append(component)

    def run(self):
        """
        Retrieves and stores the nodal information for each registered component name.
        """
        global _mapdl

        if not _mapdl:
            _mapdl = _init_mapdl()

        _mapdl.clear()
        _mapdl.input(self._inp_file)

        for component in self._components:
            print(f"Caching {component} ...")
            _mapdl.esel("S", "ENAME", component)
            _mapdl.nsle("S", "ACTIVE")
            _mapdl.nsle("U", "MID")

            nodes = {}
            for line in _mapdl.nlist():
                vals = line.split()[:4]
                vals = [int(val) for val in vals]
                nodes[vals[0]] = (vals[1], vals[2], vals[3])

            self._components[component] = nodes


def _init_mapdl(**kwargs):
    print("Connecting to APDL ...")
    mapdl_inst = launch_mapdl(**kwargs)
    print("Connected.")
    return mapdl_inst


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
