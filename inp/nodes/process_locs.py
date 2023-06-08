def extract_nodes(file_path):
    out = ""
    with open(file_path, 'r') as f:
        for line in f:
            elements = line.split(',')
            out += ''.join(elements[:2]) + '\n'

    with open(file_path + '.node', 'w') as f:
        f.write(out)


extract_nodes('ts.node.loc')
