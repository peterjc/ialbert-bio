#
# This script is used to generate Python tests.
#
# The output generated by each test can be seen at:
#
# https://github.com/ialbert/bio/tree/master/test/data
#

# Stop on errors.
set -uex

# Fetch the accession, rename the data and change the sequence id.
bio fetch NC_045512 MN996532 --quiet > genomes.gb

# Convert genbank files to FASTA
bio convert genomes.gb  --fasta > genomes.fa

# Slice the genomes
bio convert genomes.gb --end  10 > slice.fa

# Generate features only.
bio convert genomes.gb --end 10 --features > features.fa

# Generate features only.
bio convert genomes.gb --end 10 --type CDS > cds.fa

# Translate the features.
bio convert genomes.gb --type CDS --translate > translate.fa

# Extract the proteins.
bio convert genomes.gb  --protein > protein.fa

# Convert genbank files to GFF
bio convert genomes.gb  --gff > genomes.gff
