#ifndef _ALGORITHM
#define _ALGORITHM

#include<float.h>
#include"structures.h"
#include"utility.h"

chain_link next_chain(chain_node motif, on_sequence on_seq, int sequences_count, int overlap, int gap, int q);
double    pwm_score(dataset data, chain_node pattern);
double summit_score(dataset data, chain_node pattern);
double ssmart_score(dataset data, chain_node pattern);

#endif