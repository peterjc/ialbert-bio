# Welcome to bioinformatics

> Software under development. Operational but not fully vetted.

`bio` - command-line utilities to make bioinformatics explorations more enjoyable.

Built on top of [BioPython][biopython], [Parasail][parasail] and other existing packages; `bio` streamlines bioinformatics tasks such as:
 
- downloading data from NCBI
- converting between data formats 
- extracting partial information from files: select by gene, by coordinate, by matching a pattern ...
- aligning sequences
- visualizing taxonomies
- ... and others ... 

Having access to all the utility described above makes the `bio` package well suited for exploratory analysis of genomes. 

If you are new to bioinformatics and would like to get traind in how to use `bio` see the [Biostar Handbook][handbook]
 
[biopython]: https://biopython.org/
[emboss]: http://emboss.sourceforge.net/
[parasail]: https://github.com/jeffdaily/parasail
[simplesam]: https://github.com/mdshw5/simplesam 
[handbook]: https://www.biostarhandbook.com/

## Source code

* https://github.com/ialbert/bio

## Why do we need this software?

If you've ever done bioinformatics you know how even seemingly straightforward tasks require multiple steps, arcane incantations, reading documentation and numerous other preparations that slow down your progress. 

Time and again I found myself not pursuing an idea because getting to the fun part was too tedious. The `bio` package is meant to solve that tedium. 


## A realistic example

Suppose you wanted to identify the differences between the `S` protein of the bat coronavirus deposited as `MN996532` and the `S` protein of the ancestral SARS-COV-2 virus designated by the NCBI via accession number `NC_045512`. 

If you are a trained bioinformatician, think about all the steps you would need to perform to accomplish this task, then think about the effort it would take you to teach someone else how to do the same. 

## The solution with `bio`

With the `bio` package the process takes simple, concise steps.

First we download and rename the data to have more manageable labels:

    bio NC_045512 --fetch --rename ncov
    bio MN996532  --fetch --rename ratg13

From now on `bio` can operate on  `NC_045512` using the name `ncov` and on `MN996532` using the name `ratg13` no matter where you are on your computer! It stores the data in an internal storage system that can be used from any folder. There is no clutter of files or paths to remember. For example, in any directory you now can type:

    bio ncov --fasta --end 100
    
and it will show you the first 100 bases of the genome     

    >ncov Severe acute respiratory syndrome coronavirus 2 isolate Wuhan-Hu-1, complete genome
    ATTAAAGGTTTATACCTTCCCAGGTAACAAACCAACCAACTTTCGATCTCTTGTAGATCT
    GTTCTCTAAACGAACTTTAAAATCTGTGTGGCTGTCACTC

You could also convert the data stored under `ncov` name to other formats. Let's convert the `CDS` features annotated for gene `S` to `GFF`:

```{bash, comment=NA}
    bio ncov --gff --gene S --type CDS
```

Now, back to our problem of aligning proteins. Let's align the first 90 basepairs of DNA sequences for the `S` protein for each organism, `bio` even gives you a shortcut, instead of typing `--gene S --type CDS` you can write it as `ncov:S` :

```{bash, comment=NA}
    bio ncov:S ratg13:S --end 90 --align
```
    
If instead we wanted to align the 90bp DNA sequences for `S` protein after their translation into proteins we could do it like so:

```{bash, comment=NA}
    bio ncov:S ratg13:S --translate --end 80 --align
```
    
We can note right away that all differences in the first 80bp of DNA are synonymous substitutions, the protein translations are the same.

## What did `bio` do for us?
 
1. fetched the data from NCBI
1. created a more efficient local representation the data
1. stored this representation so that next time you need it is available much faster
1. generated alignments 

## But wait there is more 

How about translating the reverse of the last 10 nucleotides of every feature labeled as `CDS`. `bio` can do that like so:

    bio ncov --fasta --type CDS --start -10 --reverse --translate
    
ah yes, just what I needed:    
   
    >YP_009724389.1 [-9:21291], reverse, translated DNA
    NQQ
    
    >YP_009725295.1 [-9:13218], reverse, translated DNA
    NVA
    
    >YP_009724390.1 [-9:3822], reverse, translated DNA
    NTH
    ...
    
And so on. `bio` has a wealth of utility that makes bioinformatics more accessible.

## Comparisons to EMBOSS

The software with the most similar goals to `bio` is the [emboss suite][emboss], a revolutionary software package developed decades ahead of its time. Unfortunately, perhaps because of being developed so early on, the amazing feats of software engineering within `emboss` are deployed with a nearly incomprehensible documentation that attempts, in vain, to describe an incredibly obtuse command interface. 

We love the concept of `emboss` but even after many years we don't understand how to use it. We constantly have to consult the manual for details. Moreover commands that use `emboss` suites tend to end up as a series of hard to read arcane commands that are surprisingly difficult to comprehend even for experienced scientists. 

Criticism aside, imitation is the greatest form of flattery, `bio` is an homage to `emboss` with the hope that one day, we can replace the functionality from `emboss` with code brings joy rather than frustrations. 
