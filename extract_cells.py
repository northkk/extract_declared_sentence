import os
import sys
import pickle

import tools


def main():
    DIR = sys.argv[1]
    if os.path.isdir(DIR):
        dn, _, fns = next(os.walk(DIR))
        paths = (os.path.join(dn, fn) for fn in fns if not fn.startswith('.'))
    elif os.path.isfile(DIR):
        paths = [DIR]
    else:
        print('only accept a file or a dir path')
        return

    cells_per_doc = []
    for path in paths:
        with open(path) as f:
            text = f.read()

            cells_per_doc.append(list(tools.extract_cells(text)))

    return cells_per_doc


if __name__ == "__main__":
    res = main()
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "cells_per_doc.pickle"), "wb") as f:
        pickle.dump(res, f, 2)