import string
import sys, os, io, operator, functools
from Bio import SeqIO
from Bio.SeqRecord import SeqRecord
from Bio.SeqFeature import Reference, CompoundLocation, FeatureLocation
from collections import OrderedDict, defaultdict
from itertools import *
from biorun import utils

NUCS = set("ATGC" + 'atgc')
PEPS = set("ACDEFGHIKLMNPQRSTVWY")
RNAS = set("AUGC" + 'augc')

NUCLEOTIDE, PEPTIDE = "nucleotide", "peptide"

SOURCE = "source"

SEQUENCE_ONTOLOGY = {
    "5'UTR": "five_prime_UTR",
    "3'UTR": "three_prime_UTR",
    "mat_peptide": "mature_protein_region",
}


counter = count(1)

UNIQUE = defaultdict(int)



def is_nuc(c):
    return c in NUCS


def is_prot(c):
    return c in PEPS


def all_pep(text, limit=1000):
    subs = text[:limit]
    return all(map(is_prot, subs))


def all_nuc(text, limit=1000):
    subs = text[:limit]
    return all(map(is_nuc, subs))


def is_sequence(text):
    if all_nuc(text):
        return NUCLEOTIDE
    elif all_pep(text):
        return PEPTIDE
    else:
        return None


class Peeker:
    def __init__(self, stream):
        self.stream = stream
        self.buffer = io.StringIO()

    def peek(self):
        content = next(self.stream)
        self.buffer = io.StringIO(content)
        return content

    def read(self, size=None):
        if size is None:
            return self.buffer.read() + self.stream.read(size=size)
        content = self.buffer.read(size)
        if len(content) < size:
            content += self.stream.read(size - len(content))
        return content

    def readline(self):
        line = self.buffer.readline()
        if not line.endswith('\n'):
            line += self.stream.readline()
        return line

    def __iter__(self):
        data = self.buffer.read()
        if data:
            yield data
        else:
            for line in self.stream:
                yield line

def get_streams(elems):
    """
    Returns streams including stdin.
    """
    if not sys.stdin.isatty():
        yield sys.stdin

    for fname in elems:
        if os.path.isfile(fname):
            yield open(fname)
        else:
            utils.error(f"file not found: {fname}")

def get_peakable_streams(elems, dynamic=False):
    """
    Returns peekable streams. Can also generate dynamic streams from text.
    """
    label = chain(string.ascii_lowercase)

    if not sys.stdin.isatty():
        yield Peeker(sys.stdin)

    for fname in elems:
        if os.path.isfile(fname):
            yield Peeker(open(fname))
        elif dynamic and is_sequence(fname):
            stream = io.StringIO(f">{next(label)}\n{fname}")
            yield Peeker(stream)
        else:
            utils.error(f"file not found: {fname}")

def parse_stream(stream):
    """
    Guesses the type of input and parses the stream into a BioPython SeqRecord.
    """
    first = stream.peek()
    format = "fasta" if first.startswith(">") else 'genbank'
    recs = SeqIO.parse(stream, format)
    return recs

def flatten(nested):
    return functools.reduce(operator.iconcat, nested, [])


def json_ready(value):
    """
    Recursively serializes values to types that can be turned into JSON.
    """

    # The type of of the incoming value.
    curr_type = type(value)

    # Reference types will be dictionaries.
    if curr_type == Reference:
        return dict(title=value.title, authors=value.authors, journal=value.journal, pubmed_id=value.pubmed_id)

    # Serialize each element of the list.
    if curr_type == list:
        return [json_ready(x) for x in value]

    # Serialize the values of an Ordered dictionary.
    if curr_type == OrderedDict:
        return dict((k, json_ready(v)) for (k, v) in value.items())

    return value

def next_count(ftype):
    UNIQUE[ftype] += 1
    return f'{ftype}-{UNIQUE[ftype]}'

def first(data, key, default=""):
    # First element of a list value that is stored in a dictionary by a key.
    return data.get(key, [default])[0]


def guess_name(ftype, annot):
    """
    Attempts to generate an unique id name for a BioPython feature
    """
    uid = desc = ''

    if ftype == 'gene':
        name = first(annot, "gene")
        desc = first(annot, "locus_tag")
    elif ftype == 'CDS':
        name = first(annot, "protein_id")
        desc = first(annot, "product")
    elif ftype == 'mRNA':
        name = first(annot, "transcript_id")
        desc = ftype
    elif ftype == "exon":
        name = first(annot, "gene")
        uid = next_count(ftype)
    else:
        name = next_count(ftype)
        desc = first(annot, "product")

    desc = f"{ftype} {desc}"
    name = name or next_count(f"unknown-{ftype}")
    uid = uid or name
    return uid, name, desc


def record_generator(rec):

    rec.type = SOURCE
    rec.strand = None
    rec.start, rec.end = 1, len(rec.seq)
    rec.locs = []
    yield rec

    for feat in rec.features:

        if feat.type == SOURCE:
            continue

        seq = feat.extract(rec.seq)

        # Qualifiers are transformed into annotations.
        pairs = [(k, json_ready(v)) for (k, v) in feat.qualifiers.items()]

        annot = dict(pairs)

        uid, name, desc = guess_name(ftype=feat.type, annot=annot)

        sub = SeqRecord(id=uid, name=name, description=desc, seq=seq)

        sub.type = feat.type

        sub.strand = feat.strand

        sub.start, sub.end = int(feat.location.start) + 1, int(feat.location.end)

        # Store the locations.
        sub.locs = [(loc.start+1, loc.end, loc.strand) for loc in
                          feat.location.parts] if feat is not None else []

        yield sub




    for feat in rec.features:
        print (type(feat))

def main():

    fnames = sys.argv[1:]

    stream = get_peakable_streams(fnames, dynamic=True)
    reader = map(parse_stream, stream)
    recs = flatten(reader)

    recs = map(record_generator, recs)
    recs = flatten(recs)

    for rec in recs:
        print (rec.name, rec.type)

if __name__ == '__main__':
    main()