#ifndef _STRUCTURE
#define _STRUCTURE

#include "utility.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_STACK_SIZE 10000

typedef struct pos_link{
    int location;
    int size;
    pos_link * next;
} pos_link;

typedef struct FoundMap{
    int seq_id;
    pos_link * positions;
    FoundMap * next;
} FoundMap;

typedef struct chain_node{
    char * label;
    FoundMap * foundmap;
} chain_node;

// observation tree entity
typedef struct tree_node{
    char * label;
    tree_node ** children;
    FoundMap * foundmap;
    int q;
} tree_node;

typedef struct on_sequence{
    char **** data;
    int sequence_count;
    int * sequence_lengths;
} on_sequence;

typedef struct list_of_chains
{
    chain_node * node;
    list_of_chains * next;
} list_of_chains;

typedef struct dataset
{
    char ** sequences;
    int * summits;
    float * p_values;
};

dataset load_compact_dataset(char * filename);
char * str_plus_char(char * st, char ch);
tree_node * initial_tree(char * label);
void add_frame(tree_node * node, char * frame, int seq_id, int location, int size, int current_frame_index);
on_sequence open_on_sequence(char * filename);

#endif