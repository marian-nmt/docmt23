#!/usr/bin/env python3

"""Creates documents from monolingual data.  Used to transform
sentences into sentences-with-context for document translation sytems.

There are two modes: chunking input lines within a document (--chunk),
or applying a sliding window (default).

The output is four columns: the docid, the start and end lines in the
original document, and the merged document string.

Context length is infinite by default, but controlled by two variables:

--max-tokens: the maximum number of tokens in the entire line
--max-sents: the maximum number of sentences (including the current one)

Length is determined by white-space-delimited tokens or by sentence-
piece tokens, if --spm-model is applied.

By default, separates sentences on a line with " <eos>", but you can
override this with "--separator".

Example usage:

    # sliding window, separate with spaces
    paste source.txt docids.txt \
      | pack.py --max-sents 5 --max-tokens 200 --spm-model /path/to/spm --separator " "

    # chunked, no sentence limit, separate with " <eos>"
    paste source.txt docids.txt \
      | pack.py --chunk --max-tokens 200 --spm-model /path/to/spm
"""

import os
import sys

from typing import List, Iterable, Tuple

sys.path.append(os.path.join(os.path.dirname(sys.argv[0]), ".."))
from docmt import read_docs


def main(args):

    spm = None
    if args.spm_model is not None:
        import sentencepiece as sp
        spm = sp.SentencePieceProcessor(model_file=args.spm_model)

    def count_tokens(line):
        return len(spm.encode(line) if spm else line.split())

    def get_context(line: str,
                    context: List[Tuple]):
        """
        Takes the line, and adds context until max_tokens is reached.

        :return: The merged line, and the number of lines removed from the context.
        """

        num_lines_context = len(context)
        lines = [text[0] for text in context] + [line]
        lens = [count_tokens(line) + 1 for line in lines]  # add 1 for <eos> token
        while len(lines) > 1 and sum(lens) > args.max_tokens:
            lens.pop(0)
            lines.pop(0)
        if args.max_sents is not None:
            while len(lines) > args.max_sents + 1:
                lines.pop(0)
        return args.separator.join(lines), num_lines_context - (len(lines) - 1)

    def chunk_doc(doc: List[Tuple]):
        """
        :return: The chunked document, number of lines.
        """
        lens = [count_tokens(line[0]) + 1 for line in doc]
        subdoc = []
        subdoclen = 0
        for segment in doc:
            segmentlen = count_tokens(segment[0]) + 1

            if (args.max_tokens != 0 and (subdoclen + segmentlen > args.max_tokens)) or \
                (args.max_sents is not None and len(subdoc) >= args.max_sents):

                yield args.separator.join(subdoc), len(subdoc)
                subdoc = []
                subdoclen = 0

            subdoc.append(segment[0])
            subdoclen += segmentlen

        if len(subdoc):
            yield args.separator.join(subdoc), len(subdoc)

    lineno = 1
    for docno, doc in enumerate(read_docs(args.infile, docfield=args.docid_field)):
        docid = doc[0][-1]
        if args.chunk:
            for subdoc, subdoclen in chunk_doc(doc):
                print(docid, lineno, lineno + subdoclen - 1, subdoc, sep="\t")
                lineno += subdoclen
        else:
            doci = 0
            for docj, line in enumerate(doc):
                line_with_context, num_deleted = get_context(line[0], doc[doci:docj])
                doci += num_deleted
                # print(docno, count_tokens(line_with_context), args.max_tokens, line_with_context)
                print(docid, lineno + doci, lineno + docj, line_with_context, sep="\t")
            lineno += len(doc)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("infile", nargs="?", default=sys.stdin)
    parser.add_argument("--max-tokens", "-t", type=int, metavar="T", default=250, help="Maximum tokens in total (default: %(default)s)")
    parser.add_argument("--max-sents", "-c", type=int, metavar="N", default=None, help="Maximum sentences of context (default: %(default)s)")
    parser.add_argument("--spm-model", "-m", default=None)
    parser.add_argument("--chunk", action="store_true")
    parser.add_argument("--docid-field", "-f", metavar="F", default=1, help="Field containing the doc ID (default: %(default)s)")
    parser.add_argument("--separator", "-s", default=" <eos>",
                        help="separator for sentences (default: %(default)s)")
    args = parser.parse_args()

    main(args)
