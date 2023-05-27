#!/usr/bin/env python3

"""
Two run modes:

(a) Take a parallel stream, index + document, and extract sentence {index} from it
(b) Take a stream of documents, and a single index -i {index}, and extract {index}

That is, (b) fixes the index, where (a) it can be variable.

Used for studying the effect of forward and backward context on contragen.
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from docmt import data, DOC_SEPARATOR

def extract_sent(line, separator=DOC_SEPARATOR, index=None, proportional=False):
    if proportional:
        source, target = line.rstrip().split("\t")
        source_pct = len(source.split(separator)[-1].split()) / len(source.split())
        target_tokens = target.split()
        num_target_tokens = int(source_pct * len(target_tokens))
        target = " ".join(target_tokens[-num_target_tokens:])
        # print(source_pct, source, target, sep="\n", file=sys.stderr)
        return target
    else:
        index = index
        if index is None:
            fields = line.split("\t", maxsplit=1)
            index = int(fields[0])
            line = fields[1]

        sents = line.rstrip().split(separator)
        return sents[min(index, len(sents) - 1)].strip()


def main(args):
    for line in sys.stdin:
        print(extract_sent(line, index=args.index, separator=args.separator, proportional=args.proportional))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--proportional", action="store_true", help="Expects source TAB target")
    parser.add_argument("--separator", default=DOC_SEPARATOR)
    parser.add_argument("--index", "-i", type=int, default=None, help="Index to extract; if None, read field from STDIN")
    args = parser.parse_args()

    main(args)

