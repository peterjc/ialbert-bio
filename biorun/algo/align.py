import warnings, sys, os
import plac
from itertools import islice, count
import textwrap

from biorun.models import view
from biorun.const import *
from biorun import utils, storage

try:
    from Bio import SeqIO
    from Bio import Align
    from Bio.Seq import Seq
    from Bio.SeqRecord import SeqRecord
    from Bio.Alphabet import IUPAC
    from Bio import BiopythonExperimentalWarning
except ImportError as exc:
    print(f"*** Error: {exc}", file=sys.stderr)
    print(f"*** Please install biopython: conda install -y biopython==1.76", file=sys.stderr)
    sys.exit(-1)

try:
    import parasail

    HAS_PARASAIL = True
except ImportError as exc:
    print(f"*** Warning: {exc}", file=sys.stderr)
    print(f"*** Please install parasail: conda install -y parasail-python", file=sys.stderr)
    HAS_PARASAIL = False

with warnings.catch_warnings():
    warnings.simplefilter('ignore', BiopythonExperimentalWarning)
    from Bio.Align import substitution_matrices

    # The default logging function.
    logger = utils.logger


def unpack(aln):
    """
    Unpack the formatted alignment.
    """
    query, pattern, target = format(aln).splitlines()

    return query, pattern, target


def print_aln(aln, matrix, query, target, aligner, width=100):
    nw = 8
    tgt_name = f"{target.name[:nw]:8s}"
    pat_name = " " * nw
    rec_name = f"{query.name[:nw]:8s}"

    query, pattern, target = unpack(aln)

    print(f"# Lenght: {aln_len}")
    print(f"# Identity: {aln.icount}/{aln_len} ({ident_perc}%)")
    print(f"# Gaps: {gapn}/{aln_len} ({gapn_perc}%)")
    print(f"# Score: {aln.score}")
    print(f"#")
    print(f"# Matrix: {matrix} ")
    print(f"# Score: {aln.score}")
    print(f"# Gap open: {aligner.internal_open_gap_score}")
    print(f"# Gap extend: {aligner.internal_extend_gap_score}")
    print("#")

    for start in range(0, aln_len, width):
        end = start + width

        print(tgt_name, target[start:end])
        print(pat_name, pattern[start:end])
        print(rec_name, query[start:end])
        print("")


def biopython_align(query, target, nucl=True, gap_open=None, gap_extend=None, matrix=None, limit=1):
    """
    Perform alignment with BioPython.
    """

    # The pairwise aligner.
    aligner = Align.PairwiseAligner()

    # The default scoring matrices
    if nucl:
        gap_open = gap_open or -10
        gap_extend = gap_extend or -0.5
        matrix = matrix or "NUC.4.4"
    else:
        gap_open = gap_open or -16
        gap_extend = gap_extend or -4
        matrix = matrix or "BLOSUM62"

    # Read the substitution matrix
    try:
        if os.path.isfile(matrix):
            m = substitution_matrices.read(matrix)
        else:
            m = substitution_matrices.load(matrix)
    except Exception as exc:
        print(f"*** Unable to read scoring matrix: {exc}", file=sys.stderr)
        print(f"*** Builtin: {', '.join(substitution_matrices.load())}", file=sys.stderr)
        sys.exit(-1)

    # Gap open
    aligner.open_gap_score = gap_open

    # Gap extend
    aligner.extend_gap_score = gap_extend

    # Assign the matrix.
    aligner.substitution_matrix = m

    # Gaps at the end of the sequences.
    aligner.left_gap_score = 0
    aligner.right_gap_score = 0

    seq_q = str(query.seq).upper()
    seq_t = str(target.seq).upper()

    try:
        results = aligner.align(seq_t, seq_q)
    except Exception as exc:
        print(f"*** Error: {exc}", file=sys.stderr)
        sys.exit(-1)

    # How many alignments to report
    results = islice(results, limit)

    for aln in results:
        print_aln(aln, matrix=matrix, query=query, target=target, aligner=aligner)


class AlnResult():
    """
    A wrapper class to represent alignments produced from different sources.
    """
    counter = count(1)

    def __init__(self, query, target, trace,
                 gap_open=11, gap_extend=1, matrix='', mode='',
                 ichr='|', mchr='.', gchr=' ', schr=':', attrs={}):
        self.query = query
        self.target = target
        self.trace = trace
        self.len = len(trace)
        self.mode = mode
        self.gap_open = gap_open
        self.gap_extend = gap_extend
        self.matrix = matrix

        # Identity
        self.icount = self.trace.count(ichr)
        self.iperc = 100 * self.icount / self.len if self.len else 0

        # Similarity
        self.scount = self.icount + trace.count(schr)
        self.sperc = 100 * self.scount / self.len if self.len else 0

        # Mismatches
        self.mcount = trace.count(mchr)
        self.mperc = 100 * self.mcount / self.len if self.len else 0

        # Gaps
        self.gcount = trace.count(gchr)
        self.gperc = 100 * self.gcount / self.len if self.len else 0

        # Update with additional attributes.
        self.__dict__.update(attrs)

    def print_wrapped(self, width=80, **kwargs):
        """
        Wraps and prints alignments
        """

        # Enforce a fixed width on each name.
        get = lambda name: f'{kwargs.get(name, ""):12.12s}'

        # Fetch the query names from additional attributes.
        q_name = get("q_name")
        p_name = get("p_name")
        t_name = get("t_name")

        header = f'''
        ### Alignment:{next(self.counter)} {q_name} vs {t_name} ###

        Length:\t{self.len} ({self.mode}) 
        Query:\t{self.len_query} [{self.start_query}, {self.end_query}]
        Target:\t{self.len_ref} [{self.start_ref}, {self.end_ref}]
        Score:\t{self.score}
        Ident:\t{self.icount}/{self.len} ({self.iperc:.1f}%)
        Simil:\t{self.scount}/{self.len} ({self.sperc:.1f}%)
        Gaps:\t{self.gcount}/{self.len} ({self.gperc:.1f}%)
        Matrix:\t{self.matrix}(-{self.gap_open}, -{self.gap_extend}) 
        '''

        header = textwrap.dedent(header)
        print(header)
        for start in range(0, len(self.trace), width):
            end = start + width
            print(t_name, self.target[start:end])
            print(p_name, self.trace[start:end])
            print(q_name, self.query[start:end])
            print("")

def get_matrix(seq, matrix):
    if not matrix:
        haspep = any(x for x in seq[:100] if x not in "ATGC")
        matrix = parasail.blosum62 if haspep else parasail.nuc44
    else:
        raise Exception("No matrix found")
    return matrix


def parasail_align(qseq, tseq, param):
    q = str(qseq.seq)
    t = str(tseq.seq)

    # Guess matrix type
    matrix = get_matrix(t, param.matrix)

    # Pick the algorithm for the alignment method.
    if param.mode in (GLOBAL_ALIGN, SEMIGLOBAL_ALIGN):
        func = parasail.sg_trace_scan
    elif param.mode == STRICT_ALIGN:
        func = parasail.nw_trace_scan
    else:
        func = parasail.sw_trace_scan

    res = func(q, t, param.gap_open, param.gap_extend, matrix=matrix)

    # Alignment must be traceback aware.
    t = res.traceback

    # Shortcuts to each field of the traceback.
    query, target, trace = t.query, t.ref, t.comp

    # Collect additional attributes
    attrs = dict()
    words = "score matches len_ref len_query cigar".split()
    for word in words:
        attrs[word] = getattr(res, word, '')

    # Populate the start coordinates
    coords = "start_ref end_ref start_query end_query".split()
    for coord in coords:
        attrs[coord] = getattr(res, coord, 0) + 1

    # Semiglobal mode needs to compute alignment start/end differently.
    if param.mode == SEMIGLOBAL_ALIGN and t.comp:
        # Find the indices of the nonzero elements.
        idx = list(idx for (idx, chr) in enumerate(t.comp) if not chr.isspace())
        start, end = min(idx), max(idx) + 1
        query = query[start:end]
        target = target[start: end]
        trace = trace[start:end]
        attrs['start_ref'], attrs['end_ref'] = start + 1, end
    else:
        # Populate from cigar string.
        attrs['start_query'] = res.cigar.beg_query + 1
        attrs['start_ref'] = res.cigar.beg_ref + 1

    # Decode the CIGAR string
    attrs['cigar'] = res.cigar.decode.decode("ascii")

    # String name for the matrix
    mname = str(matrix.name.decode("ascii"))

    aln = AlnResult(query=query, target=target, gap_open=param.gap_open, gap_extend=param.gap_extend,
                    trace=trace, attrs=attrs, matrix=mname, mode=param.mode)

    # For semiglobal alignment need to manually find the start/end from the pattern.
    aln.print_wrapped(q_name=qseq.id, t_name=tseq.id)


@plac.opt('start', "start coordinate ", type=int)
@plac.opt('end', "end coordinate")
@plac.opt('matrix', "scoring matrix", abbrev='M')
@plac.opt('gap_open', "scoring matrix", abbrev='o')
@plac.opt('gap_extend', "scoring matrix", abbrev='x')
@plac.opt('mode', "alignment mode (local, global, semiglobal, strictglobal")
@plac.flg('verbose', "verbose mode, progress messages printed")
def run(start=1, end='', mode=LOCAL_ALIGN, gap_open=11, gap_extend=1, verbose=False, query='', target=''):
    "Prints the effect of an annotation"

    # Set the verbosity of the process.
    utils.set_verbosity(logger, level=int(verbose))

    if not (query and target):
        utils.error(f"Please specify both a QUERY and a TARGET")


    param1 = utils.Param(start=start, end=end, gap_open=gap_open, gap_extend=gap_extend, mode=mode)
    param2 = utils.Param(start=start, end=end, gap_open=gap_open, gap_extend=gap_extend, mode=mode)

    # Fill in potential filtering instructions.
    query = param1.parse(query)
    target = param2.parse(target)


    # Get the data.
    qdata = storage.get_json(query)
    tdata = storage.get_json(target)

    if qdata:
        qrecs = view.get_fasta(data=qdata, param=param1)
    else:
        qrecs = [SeqRecord(Seq(query), id="QUERY")]

    if tdata:
        trecs = view.get_fasta(data=tdata, param=param2)
    else:
        trecs = [SeqRecord(Seq(target), id="TARGET")]

    # biopython_align(query=query, target=target, matrix=matrix)

    for qseq in qrecs:
        for tseq in trecs:
            parasail_align(qseq=qseq, tseq=tseq, param=param1)



def main():
    plac.call(run)


if __name__ == '__main__':
    main()