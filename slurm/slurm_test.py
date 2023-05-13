import numpy as np
import sys
import pkgutil

sys.path.append('../parametric_solver')

# Iterate over all modules in the Python path
for module in pkgutil.iter_modules():
    print(module.name)

print("TESTING")