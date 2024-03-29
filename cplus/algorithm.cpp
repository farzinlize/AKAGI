#include "algorithm.h"

chain_link * next_chain(chain_node motif, on_sequence on_seq, int sequences_count, int overlap, int gap, int q){
    
    #ifdef DEBUG_CHAINING
    int number_of_observation = 0;
    #endif

    /* observation for chaining */
    tree_node * observation = initial_tree(NULL);
    FoundMap * current_map = motif.foundmap;

    /* sequences (scroll) */
    while(current_map != NULL){
        int current_seq_id = current_map->seq_id;
        pos_link * current_position = current_map->positions;

        /* positions (scroll) */
        while (current_position != NULL){

            /* sliding (overlap-gap) */
            for (int sliding=-overlap;sliding<=gap;sliding++){
                int end_position = current_position->location + current_position->size;
                int next_position_location = end_position + sliding;

                /* ignore sliding value that passes through the sequence or the whole motif itself */
                if(next_position_location >= on_seq.sequence_lengths[current_seq_id] || next_position_location <= current_position->location)continue;
                
                /* zero-motifs as condidate */
                int i = 0; char * zero_motif;
                while ((zero_motif = on_seq.data[current_seq_id][next_position_location][i++]) != NULL){
                    int candidate_size = strlen(zero_motif);

                    /* ignore candidates which doesn't extend the motif length */
                    /* TODO IMPORTANT WARNING CHECK HERE THIS LINE after or condition */
                    if(next_position_location + candidate_size <= end_position || next_position_location + candidate_size >= on_seq.sequence_lengths[current_seq_id])continue;

                    add_frame(observation, zero_motif, current_seq_id, current_position->location, current_position->size + candidate_size + sliding, 0);

                    #ifdef DEBUG_CHAINING
                    number_of_observation++;
                    #endif
                }
            }current_position = current_position->next;
        }current_map = current_map->next;
    }

    #ifdef DEBUG_CHAINING
    printf("[CHAINING] number of observation -> %d\n", number_of_observation);
    #endif

    /* next-generation extreaction */   
    chain_link * head = initial_empty_chain_link();
    chain_link * tail = head;

    /* initiate stack with tree root */
    int sp = 0;
    tree_node ** stack = (tree_node **) malloc(sizeof(tree_node *)*MAX_STACK_SIZE);
    stack[sp++] = observation;

    while (sp != 0){
        tree_node * current_node_ref = stack[--sp];
        tree_node current_node = *current_node_ref;
        bool preserve = false;

        /* add tree children to stack (DFS) */
        for(int i=0;i<4;i++){
            if (current_node.children[i] != NULL){
                stack[sp++] = current_node.children[i];
            }
        }

        /* check for quorum */
        if(current_node.q >= q){
            chain_node * new_chain = (chain_node *) malloc(sizeof(chain_node));
            new_chain->foundmap = current_node.foundmap;
            new_chain->label = concat_malloc(motif.label, current_node.label);
            new_chain->foundmap_mode = FOUNDMAP_NOARRAY;
            preserve = true;

            /* push to dynamic link-list to refere as result */
            tail = insert_chain_link(tail, new_chain);
        }

        /* delete node after use */
        delete_tree_node(current_node_ref, preserve);
    }
    
    /* clear dynamic garbage */
    free(stack);

    return head;
}


double pwm_score(dataset data, chain_node pattern){

    /* define variables */
    int start, end, count = 0;
    int * s_len = data.sequence_lengths;
    int pwm_size = data.motif_size;
    char ** sequences = data.sequences;
    double *pwm = data.compact_pwm, a = 0;

    /* search through instances */
    FoundMap * map = pattern.foundmap;
    for (int seq_id; map != NULL; map = map->next){
        seq_id = map->seq_id;
        pos_link * instance = map->positions;
        for(int start, end; instance != NULL; instance = instance->next){
            start = instance->location;
            end   = instance->location + instance->size;

            /* prevent going through sequence length for extended motifs */
            /* motifs may extend sequences in an edit-distance based alignment */
            if(end > s_len[seq_id]) end = s_len[seq_id];

            /* calculating score of instance */
            double max_score = -DBL_MAX; int range = instance->size + pwm_size;

            #ifdef DEBUG_PWM
            printf("[INSTANCE] size-> %d, location-> %d (seq_id=%d)\n", instance->size, instance->location, seq_id);
            #endif

            for(int i=1; i<range; i++){
                int seq_idx = max_integer(start, start + i - pwm_size);
                int ref_idx = max_integer(0, pwm_size - i);

                double a_score = 0, r_score = 0;
                while (seq_idx < end && ref_idx < pwm_size){
                    a_score = a_score + pwm_find(pwm, pwm_size, sequences[seq_id][seq_idx], ref_idx, false);
                    r_score = r_score + pwm_find(pwm, pwm_size, sequences[seq_id][seq_idx], ref_idx, true);
                    ref_idx++; seq_idx++;

                    #ifdef DEBUG_PWM
                    printf("(seq_idx=%d, character=%c, ref_idx=%d)\t", seq_idx, sequences[seq_id][seq_idx], ref_idx);
                    #endif
                }

                #ifdef DEBUG_PWM
                if(a_score > max_score) {
                    max_score = a_score;
                    printf("#(a:%f)#", a_score);
                }
                if(r_score > max_score) {
                    max_score = r_score;
                    printf("#(r:%f)#", r_score);
                }
                printf("#(max-score-until-now->%f)#\n", max_score);
                #else
                if(a_score > max_score) max_score = a_score;
                if(r_score > max_score) max_score = r_score;
                #endif
            }

            #ifdef DEBUG_PWM
            printf("[DEBUG][PWM] instance max_score -> %f\n", max_score);
            #endif

            a = a + max_score; count++;
        }
    }

    #ifdef DEBUG_PWM
    printf("[DEBUG][PWM] a=%f, count=%d\n", a, count);
    #endif

    /* returing the average as pattern score */
    return a / count;
}


double summit_score(dataset data, chain_node pattern){
    int count = 0;
    double a = 0;
    int * summits = data.summits;

    FoundMap * map = pattern.foundmap;
    for (int seq_id; map != NULL; map = map->next){
        seq_id = map->seq_id;
        pos_link * instance = map->positions;
        for(int start, end; instance != NULL; instance = instance->next){
            start = instance->location;
            end   = instance->location + instance->size;

            int mid = (end + start) / 2;
            a = a + abs(summits[seq_id] - mid);
            count++;
        }
    }
    return a / count;
}


double ssmart_score(dataset data, chain_node pattern){

    /* define variables (fsvs->foundmap_sequence_vector_size) */
    int seq_id = 0, fsvs = 0;
    int seq_count = data.sequence_count;
    double p_sum = 0, n_sum = 0, n_score;
    double * p_values = data.p_values;

    FoundMap * map = pattern.foundmap;
    while(seq_id < seq_count){
        if(map != NULL && map->seq_id == seq_id){
            p_sum = p_sum + p_values[seq_id];
            map = map->next; fsvs++;
        }
        else n_sum = n_sum + p_values[seq_id];
        seq_id++;
    }

    if(n_sum != 0) n_score = (n_sum/(seq_count-fsvs));
    else           n_score = 0;

    return (p_sum/fsvs) - n_score;
}


#ifdef ALG_MAIN
int main(int argc, char * argv[]){

    printf("you need to address motif data file (argc=%d) \n", argc);

    /* ready test case */
    chain_node motif;
    FILE * motif_data = fopen(argv[1], "rb");
    int label_size = read_integer(motif_data);
    motif.label = read_string(motif_data, label_size);
    int bin_size = read_integer(motif_data);
    uint8_t * bin = (uint8_t*) calloc(bin_size, sizeof(uint8_t));
    fread(bin, sizeof(uint8_t), bin_size, motif_data);
    motif.foundmap = binary_to_structure(bin);
    dataset compact = load_compact_dataset("test.ct");
    on_sequence onseq = open_on_sequence("test.onseq");
    printf("[ALG] all data loaded - investigating chain node (label:%s, bin_size:%d)\n", motif.label, bin_size);

    #ifdef TEST_ONSEQ
    char * test_motif = onseq.data[0][0][0];
    printf("first motif in onseq (0.0.0) -> %s, size=%ld\n", test_motif, strlen(test_motif));
    int a = 1;
    while(test_motif != NULL){
        test_motif = onseq.data[0][0][a++];
    }
    printf("number of motifs at (0.0) -> %d\n", a);
    #endif

    /* scores */
    double scores[3];
    scores[0] = pwm_score(compact, motif);
    scores[1] = ssmart_score(compact, motif);
    scores[2] = summit_score(compact, motif);
    printf("[SCORES]\n--pwm:%f\n--ssmart:%f\n--summit:%f\n", scores[0], scores[1], scores[2]);

    clock_t now, record;

    /* chaining */
    now = clock();
    chain_link * result = next_chain(motif, onseq, onseq.sequence_count, 4, 4, 195);
    record = clock() - now;
    printf("[CHAIN] number of clocks -> %ld (clock per second = %ld)\n", record, CLOCKS_PER_SEC);
    chain_link *current = result;
    int next_size = 0, nexty_idx = 0;
    char filename[200];
    while(current != NULL){
        if(current->node == NULL) {
            printf("[?] NULL node in chain_link\n");
            break;
        }
        next_size++;
        chain_node * nexty = current->node;
        
        uint32_t bin_size;
        uint8_t * data_bin = structure_to_binary(nexty->foundmap, &bin_size);
        sprintf(filename, "nexty[%d].data", nexty_idx);
        FILE * f = fopen(filename, "wb");
        fwrite(data_bin, sizeof(uint8_t), bin_size, f);

        printf("bin_size->%d, label->%s\n", bin_size, nexty->label);
        current = current->next;
        nexty_idx++;
    }printf("[CHAIN] number of next chains = %d\n", next_size);

    return 0;
}
#endif