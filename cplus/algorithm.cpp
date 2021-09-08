#include<algorithm.h>

list_of_chains next_chain(chain_node motif, on_sequence on_seq, int sequences_count, int overlap, int gap, int q){
    
    int i;

    /*   observation   */
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
    return extract_motifs(observation, q);
}