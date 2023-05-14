import abc
import pickle
import os
import time
from ansys.mapdl.core import launch_mapdl

import parametric_solver.inp as inp
from parametric_solver.apdl_result import APDLResult


_mapdl = None


class ParametricSolver(abc.ABC):
    def __init__(self, inp_file):
        self._inp_file = inp_file
        self._samples = []
        self._results = {}

        if not inp.is_inp_valid(inp_file):
            print("Unprocessed input file. Processing ...")
            inp.process_invalid_inp(inp_file)

    @property
    def samples(self):
        return self._samples

    @property
    def results(self):
        return self._results

    def solve(self, write_path="", read_cache=True, verbose=False):
        start_time = time.time()
        i = 1
        n = len(self._samples)

        for sample in self._samples:
            print(f"Solving [{i}/{n}]\t\tTime Remaining: {_eval_remaining_time(start_time, i - 1, n - i + 1)}")
            print(f"Sample: {sample}")

            filepath = os.path.join(write_path, self._eval_filename(sample))
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
    def _set_mat_props(self, sample, mat_ids, mapdl_inst):
        pass

    @abc.abstractmethod
    def _eval_filename(self, sample):
        pass

    def _solve_sample(self, sample, inp_path, mat_ids=(2, 4, 6), verbose=False):
        global _mapdl

        if not _mapdl:
            _mapdl = _init_mapdl()

        _mapdl.clear()
        _mapdl.input(inp_path)
        _mapdl.prep7()

        for mat_id in mat_ids:
            self._set_mat_props(sample, mat_id, _mapdl)

        _mapdl.finish()

        _mapdl.slashsolu()
        _mapdl.solve(verbose=verbose)
        _mapdl.finish()

        return APDLResult(_mapdl.result)


class BilinearSolver(ParametricSolver):
    def __init__(self, inp_file):
        super().__init__(inp_file)

    def add_sample(self, elastic_mod, yield_strength, tangent_mod):
        self.samples.append((elastic_mod, yield_strength, tangent_mod))

    def _eval_filename(self, sample):
        return f"e{_num_to_identifier(sample[0])}_" \
               f"y{_num_to_identifier(sample[1])}_" \
               f"t{_num_to_identifier(sample[2])}.pkl"

    def _set_mat_props(self, sample, mat_id, mapdl_inst):
        elastic_mod, yield_strength, tangent_mod = sample

        mapdl_inst.tbdele("PLAS", mat_id)
        mapdl_inst.mp("EX", mat_id, elastic_mod)
        mapdl_inst.tb("PLAS", mat_id, "", "", "BISO")
        mapdl_inst.tbdata(1, yield_strength, tangent_mod)


class PowerLawSolver(ParametricSolver):
    def __init__(self, inp_file):
        super().__init__(inp_file)

    def add_sample(self, elastic_mod, yield_strength, exponent):
        self.samples.append((elastic_mod, yield_strength, exponent))

    def _eval_filename(self, sample):
        return f"e{_num_to_identifier(sample[0])}_" \
               f"y{_num_to_identifier(sample[1])}_" \
               f"n{_num_to_identifier(sample[2])}.pkl"

    def _set_mat_props(self, sample, mat_id, mapdl_inst):
        elastic_mod, yield_strength, exponent = sample

        mapdl_inst.tbdele("PLAS", mat_id)
        mapdl_inst.mp("EX", mat_id, elastic_mod)
        mapdl_inst.tb("PLAS", mat_id, "", "", "NLISO")
        mapdl_inst.tbdata(1, yield_strength, exponent)


def _init_mapdl():
    print("Connecting to APDL ...")
    mapdl_inst = launch_mapdl(loglevel='INFO')
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

    exponent = int(num_str.split("e")[-1])

    return f"{significant_digits}e{exponent}"
