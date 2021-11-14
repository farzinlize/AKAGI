#ifndef _STRUCTURE
#define _STRUCTURE

#include "utility.h"
#include "global.h"
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

#define MAX_STACK_SIZE 10000
#define STR 0xff
#define DEL 0xdd
#define END 0xff

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
    bool foundmap_mode;
} chain_node;

/* observation tree entity */
typedef struct tree_node{
    char * label;
    tree_node ** children;

    /* observation data */
    int q;  // quorum
    FoundMap * foundmap;
} tree_node;

typedef struct on_sequence{
    char **** data;
    int sequence_count;
    int * sequence_lengths;
} on_sequence;

typedef struct chain_link
{
    chain_node * node;
    chain_link * next;
} chain_link;

typedef struct dataset
{
    int sequence_count;
    int * sequence_lengths;
    char ** sequences;

    /* bundle */
    int * summits;
    double * p_values;

    /* pwm */
    int motif_size;
    double * compact_pwm;
} dataset;

dataset load_compact_dataset(const char * filename);
char * str_plus_char(char * st, char ch);
tree_node * initial_tree(char * label);
FoundMap * initital_foundmap(int seq_id, int location, int size, FoundMap * nexty);
void add_frame(tree_node * node, char * frame, int seq_id, int location, int size, int current_frame_index);
int add_position(FoundMap * foundmap, int seq_id, int location, int size);
on_sequence open_on_sequence(const char * filename);
int intlen_positions(pos_link * positions);
void destroy_foundmap(FoundMap * map, bool array);
void destroy_node(chain_node * node, bool heap);
void delete_tree_node(tree_node * node, bool preserve_data);
int len_chain_link(chain_link head);
void clean_chain_link(chain_link * head);
chain_link * initial_empty_chain_link();
chain_link * insert_chain_link(chain_link * link, chain_node * node);

/* byte encode functions */
uint8_t * structure_to_binary(FoundMap * map, uint32_t * binary_size);
FoundMap * binary_to_structure(uint8_t * binary);

#endif