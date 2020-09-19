# bio: introduction

> Note: the package is not yet released, some functionality is not yet operational.

**Making bioinformatics fun again.**

Utilities to streamline bioinformatics education.

The `bio` software package attempts to streamline several bioinformatics tasks,
to allow users to focus on the concepts that matter.

The primary use of the package is in education and exploratory analysis of viral and bacterial genomes.

## Rationale

Typical bioinformatics solutions end up  being unnecessarily complicated. Seemingly simple tasks require elaborate sets
of preparations that limit progress

For example suppose you wanted to find the alignment and the differences between protein `S` of the bat corona virus `MN996532` and protein `S` of the ancestral SARS-COV-2 virus (accession numbers as designated by NCBI accession number `NC_045512`). Think about all the steps you would need to undertake to perform that task.
 
With `bio` you can write:

    bio align MN996532:S NC_045512:S

And that's it. It will automatically fetch the data, align in DNA space, produce a global DNA alignment. But wait there is more. Perhaps you needed local alignments, no problem:

    bio align MN996532:S NC_045512:S --local

or align the translated sequences as proteins:

    bio align MN996532:S NC_045512:S --translation

perhaps you wanted to align only a range of the sequences:

    bio align MN996532:S NC_045512:S --range 100-200

and so on.

Moreover after the first run the data for `MN996532` and `NC_045512` are saved in the local cache. Thus you would not need to connect to internet to run subsequent commands.

## Documentation

The `bio` package offers functionality beyond the example shown above.

The documentation is maintained at

    https://bio.github.io

Or in the github repository as markdown files:

    https://github.com/ialbert/bio/tree/master/doc



