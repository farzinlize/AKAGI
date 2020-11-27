# Graph Kmer-hood based Motif finding

A kmer-hood graph is a study design graph for motif finding applications. This project is implemented in python using several objects described at class section of this report. Main purpose of this project is to determine how indels (inserts and deletion) in a DNA sequence affect motif discovery.

## Binding Sites Discovery

A specific part of DNA sequence that a special protein can bind is called a *binding site*. The protein can start, terminate or regulate a biological process inside a cell after binding to its special binding site. Discovering such binding site will helps biologist to know a cell functionality by reading its genome. Although, Finding these binding sites using experimental approaches is highly expensive in resource and time. However, computational algorithm have shown promising results that accelerate discovering process.

## Motif Search Problem

A motif is a sub-string of a genomic sequence, like DNA, that is related to a specific binding site. There are many computational approaches to model and discover these motifs but a common approach is to discover the most repeated sub-string (over-represented) over a set of sub-sequences that are most likely to have a specific binding site. For example sequences with 1000 base pair length will be extracted upstream of a specific gene from different cells for finding its special binding site.

**Motifs are slightly different from each other**
At each binding site, there could be slightly mutations that will have no effect on biological process related to the site. As it is unclear how these mutations works, researchers designed different models to cover possible mutations and among those, **(l,d)-motif** is a very popular model that have been evolving these past years.

### (l, d)-motif and distance definition

Assuming *l* and *d* as integer values and a set of sequences, any string with length of l that has at least one instance in each sequence with at most d differences from it, is called a (l, d)-motif. Although this problem definition is almost untouched in many articles but the term *difference* has been being argued. Many articles only considered base pair mutation so they could use hamming distance for finding different motif instances. However, it is shown that indels are also playing an important role in diversity. Under the title of **E**dit-distance based **M**otif **S**earch (EMS), some articles tried to consider indels but all of them were limiting motif length as they were based on (l, d)-motif model. This limitation is resulting *forced differences* for each considered indel and here is where a kmer-hood graph comes in.

# G-Kmer-hood (class)

A G-Kmer-hood is an undirected graph where each node is related to a specific string and edges are defined as if two string are one edit-distance apart, they will be connected trough an edge. The graph has different level which any node belongs to a specific level will have same length strings. An instance of G-Kmer-hood has two value k-min and k-max as its dimensions and they are lower bound and upper bound of graph levels respectively.
The algorithm below describing how a gkhood instance will have built in this project using k-min, k-max and working alphabet as inputs:

 - generate all included nodes using trie tree (described later)
 - for each node:
	 - a redundant list of one-distance neighbours of the node is generated
	 - nodes related to generated neighbors are found by trie (if its within graph dimension) and will be added into the node's neighbours sorted list using a binary search 

After successfully generating a G-Kmer-hood, a breath first search with limited depth could be executed for extracting d-neighbourhood of any specific node. This neighbourhood is not limited on specific length and includes **every possible** strings that are at most d distance apart within graph dimensions.

## TrieFind (class)

A customized trie structure is bind to each kmer-hood graph for accessing nodes using their **k**-mer with **k** step. Because of being a complete tree, it is responsible for generating all possible nodes within graph dimension. This class also is being used for saving kmers as a list. In other words, a G-Kmer-hood is a list of all possible kmers within specific range of lengths, therefore, a tree holding its information must be complete.
In this project different set of function were used for **a)** saving a list of kmers or **b)** creating and finding nodes in G-Kmer-hood. In both modes each node belongs to a specific level and have a label that indicates a path from root to itself. Children of this node have the same label plus a letter which indicates path branches. There are also **c)** chaining and **d)** report section for further goals.

### (a) Set Trie

Starting with only one instance as root, kmers could be added using `add_frame` function on root that will generate path or use previously presented one. Tree nodes in this mode may have a list that stores kmer instances location that occurred in input sequences. Nodes without this list are considered unseen.
**Motif Extraction**: after visiting every possible frame and their neighbourhoods, calling `extract_motif` function on root will search all tree nodes and collect motifs that are present in at least **q** number of sequences. 

> As mentioned in motif search problem section, applications uses sequences that have a great chance of having a specific binding site. Therefore it is possible that a target binding site wouldn't be in some sequences. Researchers use an integer variable **q** (less than but near to number of sequences) and report a kmer as motif that is occurred in at least q number of sequences (instead of all sequences) 

### (b) Bound Trie

Each G-Kmer-hood has a trie binding to it that generates all of its nodes at first and will be used for searching with `find` function. An empty trie will generate complete set of children for each letter in graph alphabet and repeat this process for each child until it reaches upper bound limit of its graph. Meanwhile, tree nodes within graph dimension will generate its corresponding node in graph and recursively aggregates them in a list. The final list is the `child_birth` return value. 

## Graph Data-set

It is easily understood that those process above are time consuming but could be used several time for any instance of motif finding problem. Therefore, saving graph information is beneficial. This process is done using `FileHandler` object and a tree-like file that includes locations related to each d-neighbourhood of all nodes in data-set. This information includes two integer values indicating file index and first d-neighbourhood line number. A d-neighbourhood is a distance-sorted set of tuples in each line with one string value (kmer) and its distance 

### Heap array coding/decoding

It is desired to find kmer's d-neighbourhood in files just like finding it in memory (using objects). An encoding technique is used to indexing kmers in a continuous array with no gap that also supports tree-like search. The core idea behind this technique is to sort all children of a node located at `i` in `|alphabet|×i` area. In this project `heap_encode` and `heap_decode` functions are implemented for only DNA alphabet (or any 4 letter alphabet). 
**What about missing kmers in graph itself?** A graph with specific dimensions includes kmers with specific range of kmers. The technique discussed above will put every kmers with same size after each other, therefore, omitting smaller kmers doesn't make any gap.

Using the technique above, we will have a unique continuous integer code for our kmers in graph

## Chaining motifs

Early expriments of motif finding with small length shows significant 


> Written with [StackEdit](https://stackedit.io/).