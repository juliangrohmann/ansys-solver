import abc
import pickle
import os
import time
import sys
import hashlib

sys.path.append('..')
from ansys.mapdl.core import launch_mapdl

import parametric_solver.inp as inp
from parametric_solver.apdl_result import APDLResult


_mapdl = None


class ParametricSolver(abc.ABC):
    def __init__(self, inp_file, write_path="", **kwargs):
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
        return self._samples

    @property
    def results(self):
        return self._results

    def solve(self, read_cache=True, verbose=False):
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
        _mapdl.solve(verbose=verbose)
        _mapdl.finish()

        return APDLResult(_mapdl.result)


class BilinearSolver(ParametricSolver):
    def __init__(self, inp_file, **kwargs):
        super().__init__(inp_file, **kwargs)

    def add_sample(self, elastic_mod, yield_strength, tangent_mod):
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


class BilinearDictSolver(ParametricSolver):
    def __init__(self, inp_file, **kwargs):
        super().__init__(inp_file, **kwargs)

    def add_sample(self, sample_dict):
        """
        Parameters
        ----------
        sample_dict: dict
            Dictionary that specifies the properties of the sample.
            All keys are optional; to leave a property unchanged from the provided input file, omit the key.

            Possible keys:
                'elastic_mod': int
                'yield_strength': int
                'tangent_mod': int
                'pressure': list of 2-tuples, for example [(<filename>, <component_name>), ...]
                'thermal': List of 2-tuples, for example [(<filename>, <component_name>), ...]

            'pressure' -> Pressure loads specified in <filename> applied to <component_name>
            'thermal' -> Thermal loads specified in <filename> applied to <component_name>,

        Notes
        -----
        Extensions should be included in filenames.
        Filename should be an absolute directory if the file is not in the working directory.

        Example sample dictionary format (omit keys that should not be set):

        sample_dict = {
            'elastic_mod': 200e9,
            'yield_strength': 250e6,
            'tangent_mod': 100e6,
            'pressure': [
                ('pressure_file1.out', 'component1'),
                ('pressure_file2.out', 'component2'),
                ('pressure_file3.out', 'component3'),
                ('pressure_file4.out', 'component4'),
            ]
            'thermal': [
                ('thermal_file1.node.cfdtemp', 'component1'),
                ('thermal_file2.node.cfdtemp', 'component2'),
            ]
        }
        """
        self.samples.append(sample_dict)

    def _eval_filename(self, sample):
        filename = ''

        if 'elastic_mod' in sample:
            filename += f"e{_num_to_identifier(sample['elastic_mod'])}_"

        if 'yield_strength' in sample:
            filename += f"y{_num_to_identifier(sample['yield_strength'])}_"

        if 'tangent_mod' in sample:
            filename += f"t{_num_to_identifier(sample['tangent_mod'])}_"

        if 'pressure' in sample:
            for pressure in sample['pressure']:
                filename += f"p{_file_to_checksum(pressure[0], digits=6)}_"

        if 'thermal' in sample:
            for thermal in sample['thermal']:
                filename += f"p{_file_to_checksum(thermal[0], digits=6)}_"

        filename.rstrip('_')
        return filename + '.pkl'

    def _setup_solve(self, sample, mat_ids, mapdl_inst):
        for mat_id in mat_ids:
            if 'elastic_mod' in sample:
                _set_elastic_mod(sample['elastic_mod'], mat_id, mapdl_inst)

            if 'yield_strength' in sample and 'tangent_mod' in sample:
                _set_bilinear_plasticity(sample['yield_strength'], sample['tangent_mod'], mat_id, mapdl_inst)

            if 'pressure' in sample:
                for pressure in sample['pressure']:
                    _set_pressure_loads(*pressure, mapdl_inst)

            if 'thermal' in sample:
                for thermal in sample['thermal']:
                    _set_thermal_loads(*thermal, mapdl_inst)


class PowerLawSolver(ParametricSolver):
    def __init__(self, inp_file, **kwargs):
        super().__init__(inp_file, **kwargs)

    def add_sample(self, elastic_mod, yield_strength, exponent):
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


def _set_elastic_mod(elastic_mod, mat_id, mapdl_inst):
    mapdl_inst.prep7()

    mapdl_inst.mp("EX", mat_id, elastic_mod)

    mapdl_inst.finish()


def _set_bilinear_plasticity(yield_strength, tangent_mod, mat_id, mapdl_inst):
    mapdl_inst.prep7()

    mapdl_inst.tbdele("PLAS", mat_id)
    mapdl_inst.tb("PLAS", mat_id, "", "", "BISO")
    mapdl_inst.tbdata(1, yield_strength, tangent_mod)

    mapdl_inst.finish()


def _set_power_law_plasticity(yield_strength, exponent, mat_id, mapdl_inst):
    mapdl_inst.prep7()

    mapdl_inst.tbdele("PLAS", mat_id)
    mapdl_inst.tb("PLAS", mat_id, "", "", "NLISO")
    mapdl_inst.tbdata(1, yield_strength, exponent)

    mapdl_inst.finish()


def _set_pressure_loads(filename, component, mapdl_inst):
    mapdl_inst.slashmap()

    mapdl_inst.ftype("CSV", 0)
    mapdl_inst.read(filename, 1, "", 1, 2, 3, 4)
    mapdl_inst.target(component)

    mapdl_inst.finish()


def _set_thermal_loads(filename, component, mapdl_inst):
    print(os.getcwd())
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
    print(numlines)

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

    # ext = 'cfdtemp'
    # real_filename = filename.rstrip('.' + ext)
    # parent_dir = os.path.dirname(_curr_dir())
    # repl_path = real_filename\
    #     .replace("\\", "__slash__")\
    #     .replace("/", "__slash__")\
    #     .replace(":", "__colon__")\
    #     .replace(".", "__dot__")
    #
    # macro_path = os.path.join(parent_dir, 'macros', 'MITTSN.mac')
    #
    # mapdl_inst.cmsel("S", component)
    # mapdl_inst.nsle("S", "ACTIVE")
    #
    # print("Using macro:", macro_path, "with", repl_path)
    # mapdl_inst.use(macro_path, repl_path, ext)


def _curr_dir():
    return os.path.dirname(os.path.abspath(__file__))


class NodeContext:
    def __init__(self, inp_file):
        self._inp_file = inp_file
        self._components = []
        self._component_map = {}

    def add_component(self, component):
        self._components.append(component)

    def run(self):
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
