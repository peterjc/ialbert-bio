
#
# This file was generated automatically! Do not edit.
#

# Get the helper utitilies.
from generate import *

# Initialize directories.
init_dirs()


def test_1(capsys):
    run("set -uex")

def test_2(capsys):
    run("bio fasta genomes.gb --end  100 > genomes.fa")

def test_3(capsys):
    run("bio fasta genomes.gb --end  100  --alias alias.txt > genomes.alias.fa")

def test_4(capsys):
    run("bio fasta genomes.gb --end 10 --type CDS > cds.fa")

def test_5(capsys):
    run("bio fasta genomes.gb --type CDS --translate > translate.fa")

def test_6(capsys):
    run("bio fasta genomes.gb  --protein > protein.fa")

def test_7(capsys):
    run("bio fasta -s -3 > stop.fa")

def test_8(capsys):
    run("bio gff genomes.gb > genomes.gff")

def test_9(capsys):
    run("bio gff genomes.gb --type CDS > CDS.gff")

def test_10(capsys):
    run("bio gff -s 300 -e 10k > slice.gff")

