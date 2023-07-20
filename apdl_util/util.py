import psutil
from ansys.mapdl.core import launch_mapdl


_mapdl = None


def get_mapdl(kill=False, **kwargs):
    global _mapdl

    if not _mapdl:
        _mapdl = init_mapdl(kill=kill, **kwargs)

    return _mapdl


def init_mapdl(kill=False, **kwargs):
    if kill:
        kill_ansys()

    print("Connecting to APDL ...")
    mapdl_inst = launch_mapdl(**kwargs)
    print("Connected.")
    return mapdl_inst


def clear_mapdl():
    global _mapdl
    _mapdl = None


def kill_ansys():
    print("Killing all ANSYS processes ...")
    _kill_processes_by_name("ANSYS.exe")


def _kill_processes_by_name(name):
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == name:
            try:
                proc.kill()
                print(f'Killed process {name} with PID: {proc.pid}')
            except psutil.NoSuchProcess:
                print(f'No such process: {name} with PID: {proc.pid}')
            except psutil.AccessDenied:
                print(f'Access denied to kill process: {name} with PID: {proc.pid}')
            except Exception as e:
                print(f'Error occurred while killing process: {name} with PID: {proc.pid}, error: {str(e)}')