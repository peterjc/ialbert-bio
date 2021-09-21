import re
import sys
import json
try:
    from Bio import Entrez
except ImportError as exc:
    print(f"# Error: {exc}", file=sys.stderr)
    print(f"# This program requires biopython", file=sys.stderr)
    print(f"# Install: conda install -y biopython>=1.79", file=sys.stderr)
    sys.exit(-1)

try:
    from ffq.ffq import ffq_doi, ffq_gse, ffq_run, ffq_study
except ImportError as exc:
    print(f"# Error: {exc}", file=sys.stderr)

from biorun.libs import placlib as plac
from tqdm import tqdm
from biorun import utils
from urllib.error import HTTPError
import requests

Entrez.email = 'foo@foo.com'


#
# Genbank and Refseq accession numbers
#
# https://www.ncbi.nlm.nih.gov/genbank/acc_prefix/
# https://www.ncbi.nlm.nih.gov/books/NBK21091/table/ch18.T.refseq_accession_numbers_and_mole/?report=objectonly/
#

# https://rest.ensembl.org/sequence/id/ENST00000288602?content-type=text/x-fasta;type=cdna


def parse_ensmbl(text):
    patt = r'(?P<letters>[a-zA-Z]+)(?P<digits>\d+)(\.(?P<version>\d+))?'
    patt = re.compile(patt)
    m = patt.search(text)
    code = m.group("letters") if m else ''
    digits = m.group("digits") if m else ''
    version = m.group("version") if m else ''
    return code, digits, version

def parse_ncbi(text):
    patt = r'(?P<letters>[a-zA-Z]+)(?P<under>_?)(?P<digits>\d+)(\.(?P<version>\d+))?'
    patt = re.compile(patt)
    m = patt.search(text)
    code = m.group("letters") if m else ''
    digits = m.group("digits") if m else ''
    refseq = m.group("under") if m else ''
    version = m.group("version") if m else ''
    return code, digits, refseq, version

def is_srr(text):
    patt = re.compile("(S|E)RR\d+")
    return bool(patt.search(text))

def is_bioproject(text):
    patt = re.compile("PRJN\d+")
    return bool(patt.search(text))

def is_ensembl(text):
    code, digits, version = parse_ensmbl(text)
    cond = code in ( "ENST", "ENSG", "ENSP", "ENSE")
    cond = cond and len(digits)>8 and digits.startswith('0')
    return cond

def is_ncbi_nucleotide(text):
    """
    Returns true of text matches NCBI nucleotides.
    """
    code, digits, refseq, version = parse_ncbi(text)
    if refseq:
        cond = code in ["AC", "NC", "NG", "NT", "NW", "NZ", "NM", "XM", "XR"]
    else:
        num1, num2 = len(code), len(digits)
        cond = (num1 == 1 and num2 == 5) or (num1 == 2 and num2 == 6) or (num1 == 3 and num2 == 8)

    return cond

def is_ncbi_protein(text):
    """
    Returns true of text matches NCBI protein sequences
    """
    code, digits, refseq, version = parse_ncbi(text)
    if refseq:
        cond = code in ["AP", "NP", "YP", "XP", "WP"]
    else:
        num1, num2 = len(code), len(digits)
        cond = (num1 == 3 and num2 == 5) or (num1 == 3 and num2 == 7)
    return cond


def fetch_ncbi(ids, db, rettype='gbwithparts', retmode='text'):

    try:
        stream = Entrez.efetch(db=db, id=ids, rettype=rettype, retmode=retmode)
        stream = tqdm(stream, unit='B', unit_divisor=1024, desc='# downloaded', unit_scale=True, delay=5, leave=False)
    except HTTPError as exc:
        utils.error(f"Accession or database may be incorrect: {exc}")

    for line in stream:
        print(line, end='')
        stream.update(len(line))
    stream.close()


def fetch_ensembl(ids, ftype='genomic'):


    ftype = 'genomic' if not ftype else ftype

    server = "https://rest.ensembl.org"

    for acc in ids:

        ext = f"/sequence/id/{acc}?type={ftype}"

        r = requests.get(server + ext, headers={"Content-Type": "text/x-fasta"})

        if not r.ok:
            r.raise_for_status()
            sys.exit()

        print(r.text)

@plac.pos("acc", "accession numbers")
@plac.opt("db", "database", choices=["nuccore", "protein"])
@plac.opt("format_", "return format", choices=["gbwithparts", "fasta", "gb"])
@plac.opt("type_", "get CDS/CDNA (Ensembl only)")
def run(db="nuccore", format_="gbwithparts", type_='',  *acc):
    ids = []
    for num in acc:
        ids.extend(num.split(","))

    if not sys.stdin.isatty():
        lines = utils.read_lines(sys.stdin, sep=None)
        ids.extend(lines)

    # Dealing with SRR numbers
    srr = list(map(is_srr, ids))
    if all(srr):
        res = map(ffq_run, ids)
        res = list(res)
        text = json.dumps(res, indent=4)
        print(text)
        return

    # Dealing with Ensembl
    ensmbl = list(map(is_ensembl, ids))
    if all(ensmbl):
        fetch_ensembl(ids=ids, ftype=type_)
        return

    # Detects nucleotides
    nucs = list(map(is_ncbi_nucleotide, ids))

    # Detects proteins
    prots =list(map(is_ncbi_protein, ids))

    if not all(prots) or not all(nucs):
        utils.error(f"input mixes protein and nucleotide entries: {ids}")

    # Fetech the ids
    ids = ",".join(ids)
    fetch_ncbi(db=db, rettype=format_, ids=ids)


if __name__ == '__main__':
    # id = "AY851612",

    run()
