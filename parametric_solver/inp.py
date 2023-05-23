import os


def is_inp_valid(inp_path):
    """
    Checks whether an input file is valid for use with a parametric solver.

    Parameters
    ----------
    inp_path: str
    :return:
    """
    with open(inp_path, 'r') as f:
        ignore = False

        for line in f:
            if not ignore and "WB SOLVE COMMAND" in line:
                ignore = True

            if ignore and line and line[0] != '!':
                return False

        return True


def process_invalid_inp(inp_path):
    with open(inp_path, 'r+') as file:
        file.seek(0, os.SEEK_END)
        position = file.tell()

        while position >= 0:
            ignore = True
            line = ''
            while position >= 0:
                file.seek(position)
                char = file.read(1)
                position -= 1

                if char == '\n' and line:
                    break
                else:
                    line = char + line

            if ignore and "WB SOLVE COMMAND" in line:
                file.seek(position + 1)
                file.truncate()
                file.write("fini\n")
                position = -1

    if is_inp_valid(inp_path):
        print("Successfully processed inp file.")
    else:
        print("Failed to process inp file.")
