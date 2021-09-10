#include<algorithm.h>

list_of_chains next_chain(chain_node motif, on_sequence on_seq, int sequences_count, int overlap, int gap, int q){
    
    /*   observation   */

    int i;
    tree_node * observation = initial_tree(NULL);
    FoundMap * current_map = motif.foundmap;
    while(current_map != NULL){                                 //sequences
        int current_seq_id = current_map->seq_id;
        pos_link * current_position = current_map->positions;
        while (current_position != NULL){                       //positions
            for (int sliding=-overlap;sliding<=gap;sliding++){  // sliding
                int next_position_location = current_position->location + current_position->size + sliding;
                if(next_position_location >= on_seq.sequence_lengths[current_seq_id])continue;
                int next_position_size = current_position->size;
                char * zero_motif = on_seq.data[current_seq_id][next_position_location][i++];
                while (zero_motif != NULL){                  // zero-motifs
                    add_frame(observation, zero_motif, current_seq_id, next_position_location, next_position_size, 0);
                    zero_motif = on_seq.data[current_seq_id][next_position_location][i++];
                }
            }current_position = current_position->next;
        }current_map = current_map->next;
    }

    /*   next-generation extreaction   */   
    
    // initial result array
    list_of_chains * head = (list_of_chains *) malloc(sizeof(list_of_chains));
    list_of_chains * chains = head;
    head->node = NULL;

    // initiate stack with tree root
    int sp = 0;
    tree_node * stack = (tree_node *) malloc(sizeof(tree_node)*MAX_STACK_SIZE);
    stack[sp++] = *observation;

    while (sp != 0){
        tree_node current_node = stack[--sp];

        // check for quorum
        if(current_node.q >= q){
            chain_node * new_chain = (chain_node *) malloc(sizeof(chain_node));
            new_chain->foundmap = current_node.foundmap;
            new_chain->label = current_node.label;

            // push to dynamic link-list to refere as result
            chains->node = new_chain;
            chains->next = (list_of_chains *) malloc(sizeof(list_of_chains));
            chains = chains->next;
        }

        // add tree children to stack
        for(int i=0;i<4;i++){
            if (current_node.children[i] != NULL){
                stack[sp++] = *current_node.children[i];
            }
        }
    }
    
    // clear dynamic garbage
    free(stack);

    return *head;
}


double pwm_score(){
    
}