**What it does**

Uses SAMTools_' pileup command to produce a pileup dataset from a provided BAM dataset. It generates two types of pileup datasets depending on the specified options. If *Call consensus according to MAQ model?* option is set to **No**, the tool produces simple pileup. If the option is set to **Yes**, a ten column pileup dataset with consensus is generated. Both types of datasets are briefly summarized below.

.. _SAMTools: http://samtools.sourceforge.net/samtools.shtml

------

**Types of pileup datasets**

The description of pileup format below is largely based on information that can be found on SAMTools Pileup_ documentation page. The 6- and 10-column variants are described below.

.. _Pileup: http://samtools.sourceforge.net/pileup.shtml

**Six column pileup**::

    1    2  3  4        5        6
 ---------------------------------
 chrM  412  A  2       .,       II
 chrM  413  G  4     ..t,     IIIH
 chrM  414  C  4     ...a     III2
 chrM  415  C  4     TTTt     III7

where::

  Column Definition
 ------- ----------------------------
       1 Chromosome
       2 Position (1-based)
       3 Reference base at that position
       4 Coverage (# reads aligning over that position)
       5 Bases within reads where (see Galaxy wiki for more info)
       6 Quality values (phred33 scale, see Galaxy wiki for more)

**Ten column pileup**

The `ten-column` (consensus_) pileup incorporates additional consensus information generated with *-c* option of *samtools pileup* command::


    1    2  3  4   5   6   7   8       9       10
 ------------------------------------------------
 chrM  412  A  A  75   0  25  2       .,       II
 chrM  413  G  G  72   0  25  4     ..t,     IIIH
 chrM  414  C  C  75   0  25  4     ...a     III2
 chrM  415  C  T  75  75  25  4     TTTt     III7

where::

  Column Definition
 ------- --------------------------------------------------------
       1 Chromosome
       2 Position (1-based)
       3 Reference base at that position
       4 Consensus bases
       5 Consensus quality
       6 SNP quality
       7 Maximum mapping quality
       8 Coverage (# reads aligning over that position)
       9 Bases within reads where (see Galaxy wiki for more info)
      10 Quality values (phred33 scale, see Galaxy wiki for more)


.. _consensus: http://samtools.sourceforge.net/cns0.shtml

------

**Citation**

For the underlying tool, please cite `Li H, Handsaker B, Wysoker A, Fennell T, Ruan J, Homer N, Marth G, Abecasis G, Durbin R; 1000 Genome Project Data Processing Subgroup. The Sequence Alignment/Map format and SAMtools. Bioinformatics. 2009 Aug 15;25(16):2078-9. &lt;http://www.ncbi.nlm.nih.gov/pubmed/19505943&gt;`_
