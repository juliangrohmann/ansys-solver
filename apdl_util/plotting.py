import os
import sys
import time

PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PARENT_DIR)

from apdl_util.util import get_mapdl


def plot_nodes(input_path, filepath, **kwargs):
    mapdl = get_mapdl(**kwargs)

    mapdl.input(input_path)

    filepath = filepath.replace('\\', '/')
    real_filename, ext = os.path.splitext(filepath)
    ext = ext.replace('.', '')

    print(f"filepath = {filepath}")

    numlines_str = mapdl.inquire("numlines", "LINES", real_filename, ext)
    numlines = int(numlines_str.split('.')[0])
    print(numlines)

    mapdl.dim("node_data", "TABLE", numlines)
    mapdl.tread("node_data", real_filename, ext)
    mapdl.dim("node_arr", "ARRAY", numlines)
    mapdl.vfun("node_arr(1)", "copy", "node_data(1, 0)")

    mapdl.nsel("NONE")

    apdl_code = """
    *DO,i,1,numlines
        NSEL,A,NODE,,node_arr(i),node_arr(i)
    *ENDDO
    """
    mapdl.input_strings(apdl_code)

    mapdl.nplot(True)
