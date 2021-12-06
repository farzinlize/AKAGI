#ifndef INTERPRETER_H
#define INTERPRETER_H

#include <termios.h>
#include"structures.h"
#include"algorithm.h"

void foundmap_scroll(FoundMap * map);
void tree_check();
void chaining_scroll(chain_node node, on_sequence onseq);
void onseq_scroll(on_sequence onseq);


#endif