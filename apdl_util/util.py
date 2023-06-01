from ansys.mapdl.core import launch_mapdl


_mapdl = None


def get_mapdl(**kwargs):
    global _mapdl

    if not _mapdl:
        _mapdl = init_mapdl(**kwargs)

    return _mapdl


def init_mapdl(**kwargs):
    print("Connecting to APDL ...")
    mapdl_inst = launch_mapdl(**kwargs)
    print("Connected.")
    return mapdl_inst
