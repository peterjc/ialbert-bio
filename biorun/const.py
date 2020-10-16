# Constants reused in the program

# JSON field names
DEFINITION = "definition"
DBLINK = "dblink"
LOCUS = "locus"
SEQID = "id"
ORIGIN = "ORIGIN"
FEATURES = "FEATURES"


#
# Remaps types from GenBank to Sequence Ontology when converting to GFF files
#
SEQUENCE_ONTOLOGY = {
    "5'UTR": "five_prime_UTR",
    "mat_peptide": "mature_protein_region",
}

#
# The GFF attributes generated for a source type.
#
SOURCE_ATTRIBUTES = [
    "mol_type", "isolate", "db_xref", "organism", "country", "collection_date"
]

# GFF attributes filled for each feature other than "source"
GFF_ATTRIBUTES = [
    "gene", "protein_id", "function", "product", "note"
]