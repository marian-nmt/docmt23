# DocMT code and data

This repository contains code and data used for the experiments in the following paper:

> Escaping the sentence-level paradigm in machine translation
> Matt Post, Marcin Junczys-Dowmunt
> https://arxiv.org/abs/2304.12959v1

## Setup

Install the submodules, which are edits we made to existing repositories:

    git submodule init
    git submodule update

This will install our forks of five public repositories under `./ext`.
These are:

* `ext/ContraPro` (ContraPro: [original](https://github.com/ZurichNLP/ContraPro))
* `ext/ContraPro-EN-FR` (Large-contrastive-pronoun-testset-EN-FR: [original](https://github.com/rbawden/Large-contrastive-pronoun-testset-EN-FR))
* `ext/ContraWSD` (ContraWSD: [original](https://github.com/ZurichNLP/ContraWSD))
* `ext/GTWiC` (GTWiC: [original](https://github.com/lena-voita/good-translation-wrong-in-context))
* `ext/discourse-mt-test-sets` (discourse-mt-test-sets: [original](https://github.com/rbawden/discourse-mt-test-sets))

## Scripts

Under `bin/` are two scripts:

* `pack.py`: Takes a TSV stream of (sentence,docid) and assembles single-line documents with sentences joined by a delimiter (` <eos>` by default)
* `extract_sent.py`: Takes a single-line assembled document and extracts the requested sentence.

## ContraPro (English–German)

**Generating the files**

Using our modified ContraPro dataset, you first need to change to that directory and run the download script to download OpenSubs. Then run:

    # maximum 250 tokens, en-de
    ./ext/ContraPro/bin/json2text.py -m 250 --spm /path/to/spm/model --json-file ext/ContraPro/contrapro.json > contrapro.en-de.tsv

This will print the file to STDOUT: 36,031 lines of correct and contrastive lines. One of the fields has a value of "correct" or "contrastive"; for generative results, use only the former. You can output only these using the `--correct-only` flag.

For French, you also need to run its setup scripts to download and format the OpenSubtitles data. Then, use our modified tools in the ContraPro repo to generate data files in the same format. Note that you need to pass `-0` (since the EN-FR JSON file uses 0-indexing), along with some other options.

    # max 10 sents, en-fr
    cd ext/ContraPro-EN-FR/OpenSubs
    ../../ContraPro/bin/json2text.py --dir ./documents --json-file testset-en-fr.json -s en -t fr -m 250 -ms 10 --spm /path/to/spm/model -0 --correct-only > genpro.max250+10.en-fr.tsv

There are many other options:
```
  -h, --help            show this help message
                        and exit
  --source SOURCE, -s SOURCE
  --target TARGET, -t TARGET
  --dir DIR, -d DIR
  --max-sents MAX_SENTS, -ms MAX_SENTS
                        Maximum number of
                        context sentences
  --max-tokens MAX_TOKENS, -m MAX_TOKENS
                        Maximum length in
                        subword tokens
  --sents-before SENTS_BEFORE, -sb SENTS_BEFORE
                        Num sentences previous
                        context
  --tokens-before TOKENS_BEFORE, -tb TOKENS_BEFORE
                        Num tokens in previous
                        context
  --separator SEPARATOR
  --spm SPM
  --zero, -0            indices are already
                        zeroed (French)
  --offset OFFSET       Add this number to each
                        segment ID
  --correct-only        only output correct
                        lines
  --json-file JSON_FILE, -j JSON_FILE
```

**File format**

Each file is a TSV with the following fields:
- index (0-based) of the "payload" sentence
- distance of anaphora
- whether the sentence is a correct or contrastive variant
- the correct pronoun
- the complete source sentence with context
- the complete reference sentence with context

**Translating**

You just want the fourth field.

    cut -f 4 genpro.max250.en-de.tsv \
    | your-decoder [args] \
    > out-doc.genpro.max250.en-de.tsv

To translate just sentences without context, use `./bin/extract_sent.py`, which extracts a sentence from a line, with `<eos>` tags as the delimiter:

    # grab the source field, get the last sentence, translate
    export PATH=$PATH:$(pwd)/bin
    cut -f 4 genpro.max250.en-de.tsv \
    | extract_sent.py -i -1 \
    | your-decoder [args] \
    > out-sent.genpro.max250.en-de.tsv

**Evaluation**

Now, to evaluate the GenPro accuracy, use `evaluate_tsv.py`, found in our fork of ContraPro.

There are two main arguments to pay attention to: `-p`, which selects which pronouns to report accuracy over (a list, default "all", which reports on all of them), and `-d i j`, which selects the distances to use (inclusive). In the paper, we report accuracy on "all" with distance range 1..10:

    # evaluate all pronouns at distances 1..10
    paste genpro.max250.en-de.tsv out-doc.genpro.max250.en-de.tsv \
    | ./ext/ContraPro/bin/evaluate_tsv.py -d 1 10 -p all

    # accuracy of "sie" and "er", intrasentence:
    paste genpro.max250.en-de.tsv out-doc.genpro.max250.en-de.tsv \
    | ./ext/ContraPro/bin/evaluate_tsv.py -d 0 0 -p sie er

What this script does: it grabs the correct pronoun, and then splits the system output on `<eos>`, looking in the last sentence for the correct pronoun, using whole-token, case-insensitive matching.

## ContraWSD, GTWiC, discourse-mt-test-sets

More details coming soon (goal: 2023-06-02)

## Citation

If you make use of this code, please cite it as

> @misc{post2023escaping,
>      title={Escaping the sentence-level paradigm in machine translation},
>      author={Matt Post and Marcin Junczys-Dowmunt},
>      year={2023},
>      eprint={2304.12959},
>      archivePrefix={arXiv},
>      primaryClass={cs.CL}
>}
