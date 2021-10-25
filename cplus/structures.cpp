#include "structures.h"

tree_node * initial_tree(char * label){
    tree_node * tree = (tree_node *) malloc(sizeof(tree_node));
    tree->foundmap = NULL;
    tree->label = label;
    tree->q = 0;
    tree->children = (tree_node **) malloc(sizeof(tree_node *)*4);
    for(int child=0;child<4;child++)tree->children[child] = NULL;
    return tree;
}

/*
 * KEEP IN MIND
 * all foundmap instances contain at least one position
 */
FoundMap * initital_foundmap(int seq_id, int location, int size, FoundMap * nexty){
    FoundMap * initialmap = (FoundMap *) malloc(sizeof(FoundMap));
    initialmap->next = nexty;
    initialmap->seq_id = seq_id;

    // inital pos_v for first position entry
    pos_link * position_vector = (pos_link *) malloc(sizeof(pos_link));
    position_vector->next = NULL;
    position_vector->location = location;
    position_vector->size = size;
    initialmap->positions = position_vector;

    return initialmap;
}


int add_position(FoundMap * foundmap, int seq_id, int location, int size){

    /* sequence was present already */
    if(foundmap->seq_id == seq_id){
        pos_link * new_pos = (pos_link *) malloc(sizeof(pos_link));
        new_pos->location = location;
        new_pos->size = size;
        new_pos->next = foundmap->positions;

        foundmap->positions = new_pos;
        return 0;
    }

    /* inserting new sequence at tail */
    else if (foundmap->next == NULL){
        foundmap->next = initital_foundmap(seq_id, location, size, NULL);
        return 1;
    }

    /* inserting new sequence in order */
    else if(foundmap->next->seq_id > seq_id){
        foundmap->next = initital_foundmap(seq_id, location, size, foundmap->next);
        return 1;
    }

    /* linear search for seq_id match */
    return add_position(foundmap->next, seq_id, location, size);
}

void add_frame(tree_node * node, char * frame, int seq_id, int location, int size, int current_frame_index){

    #ifdef DEBUG
    printf("[FRAME] we are at %d index of our path (char->%c)\n", current_frame_index, frame[current_frame_index]);
    #endif

    /* end of the path */
    if(frame[current_frame_index] == '\0'){
        if(node->foundmap == NULL){
            node->foundmap = initital_foundmap(seq_id, location, size, NULL);
            node->q = 1;
        }else {
            node->q = node->q + add_position(node->foundmap, seq_id, location, size);
        }
        return;
    }

    /* select path */
    tree_node * next_path;
    switch (frame[current_frame_index]){
    case 'A':next_path = node->children[0];break;
    case 'T':next_path = node->children[1];break;
    case 'C':next_path = node->children[2];break;
    case 'G':next_path = node->children[3];break;
    }

    #ifdef DEBUG
    printf("[FRAME] we selected the next step at %d:address\n", next_path);
    #endif

    /* create path if not exist */
    if(next_path == NULL){

        #ifdef DEBUG
        printf("[FRAME] path dose not exist (creating on %c edge)\n", frame[current_frame_index]);
        #endif

        next_path = initial_tree(str_plus_char(node->label, frame[current_frame_index]));

        switch (frame[current_frame_index]){
            case 'A':node->children[0] = next_path;break;
            case 'T':node->children[1] = next_path;break;
            case 'C':node->children[2] = next_path;break;
            case 'G':node->children[3] = next_path;break;
        }
    }
    
    /* recursively go to path until reaching destination */
    add_frame(next_path, frame, seq_id, location, size, current_frame_index+1);
}


char * str_plus_char(char * s, char n){
    int str_size;
    if(s == NULL) str_size = 0;
    else          str_size = strlen(s);
    char * result = (char *) malloc(str_size+2);
    sprintf(result, "%s%c", s==NULL?"":s, n);
    return result;
}


on_sequence open_on_sequence(char * filename){
    FILE * onsequence_data = fopen(filename, "rb");
    int number_of_sequences = read_integer(onsequence_data);
    char **** all_sequences = (char ****) malloc(sizeof(char ***)*number_of_sequences);
    int * sequence_lengths = (int *) malloc(sizeof(int)*number_of_sequences);
    for(int i=0;i<number_of_sequences;i++){
        sequence_lengths[i] = read_integer(onsequence_data);
        all_sequences[i] = (char ***) malloc(sizeof(char **)*sequence_lengths[i]);
        for(int position=0;position<sequence_lengths[i];position++){
            int str_counts = read_integer(onsequence_data);
            all_sequences[i][position] = (char **) malloc((sizeof(char *)*str_counts)+1);
            for(int each=0;each<str_counts;each++){
                int str_size = read_integer(onsequence_data);
                all_sequences[i][position][each] = read_str(onsequence_data, str_size);
            }
            all_sequences[i][position][str_counts] = NULL;
        }
    }
    fclose(onsequence_data);
    on_sequence * result = (on_sequence *) malloc(sizeof(on_sequence));
    result->data = all_sequences;
    result->sequence_count = number_of_sequences;
    result->sequence_lengths = sequence_lengths;
    return *result;
}


dataset load_compact_dataset(const char * filename){

    FILE * compact = fopen(filename, "rb");
    dataset result;

    result.sequence_count = read_integer(compact);

    /* initializing arrays about sequences */
    result.sequence_lengths = (int *)    malloc(sizeof(int)    * result.sequence_count);
    result.sequences        = (char **)  malloc(sizeof(char *) * result.sequence_count);
    result.summits          = (int *)    malloc(sizeof(int)    * result.sequence_count);
    result.p_values         = (double *) malloc(sizeof(double) * result.sequence_count);

    /* reading sequences and info */
    for(int i=0;i<result.sequence_count;i++){
        result.sequence_lengths[i] = read_integer(compact);
        result.sequences[i]        = read_string(compact, result.sequence_lengths[i]);
        result.summits[i]          = read_integer(compact);
        result.p_values[i]         = read_double(compact);
    }

    /* reading pwm */
    result.motif_size  = read_integer(compact);
    result.compact_pwm = (double *) malloc(sizeof(double) * result.motif_size * 4 * 2);
    fread(result.compact_pwm  , sizeof(double), result.motif_size * 4 * 2, compact);

    fclose(compact);
    return result;
}


int intlen_positions(pos_link * positions){

    #ifndef OPTIMIZED
    if(positions == NULL) return 0;
    #endif

    int answer = 2;
    pos_link * current = positions->next;
    while(current != NULL) {
        current = current->next;
        answer = answer + 2;
    }
    
    return answer;
}


uint8_t * structure_to_binary(FoundMap * map, uint32_t * binary_size){

    /*
     * First calculate number of bytes needed to encode the map
     * for each sequence and its position list two additional integer and one byte are considered:
     * (one int for position length, another int for sequence ID and one byte for ending delimeter)
     */
    int bytesize = (intlen_positions(map->positions) + 2) * INTEGER_BYTES + 1;
    int sequence_count = 1;
    FoundMap * current = map->next;

    while (current != NULL){
        bytesize = bytesize + (intlen_positions(current->positions) + 2) * INTEGER_BYTES + 1;
        sequence_count++;
        current = current->next;
    }

    /* 
     * consider STR, END and DEL bytes plus sequence vector size
     * (DEL between sequence vector and positions 2D-vector)
     */
    uint8_t * binary = (uint8_t *) malloc(bytesize + 3 + INTEGER_BYTES);
    if(binary_size != NULL) *binary_size = bytesize + 3 + INTEGER_BYTES;

    int si = 0;
    int pi = (sequence_count+1) * INTEGER_BYTES + 1;
    binary[si++] = STR;
    put_integer(&binary[si], sequence_count);si=si+INTEGER_BYTES;
    binary[pi++] = DEL;

    FoundMap here = *map;
    do{
        /* sequence vector */
        put_integer(&binary[si], here.seq_id);si=si+INTEGER_BYTES;

        /* 2D position vector */
        pos_link current_position = *here.positions;
        put_integer(&binary[pi], intlen_positions(&current_position)/2);pi=pi+INTEGER_BYTES;
        do{
            put_integer(&binary[pi], current_position.location);pi=pi+INTEGER_BYTES;
            put_integer(&binary[pi], current_position.size);    pi=pi+INTEGER_BYTES;

            if(current_position.next == NULL) break;
            else current_position = *current_position.next;
        } while (true);
        binary[pi++] = DEL;

        if(here.next == NULL) break;
        else here = *here.next;
    } while (true);
    
    binary[pi] = END;
    return binary;
}


FoundMap * binary_to_structure(uint8_t * binary){

    #ifndef OPTIMIZED
    int si = 0;
    assert(binary[si++] == STR);
    #else
    int si = 1;
    #endif

    int sequence_count = get_integer(&binary[si]);si=si+INTEGER_BYTES;

    #ifndef OPTIMIZED
    int pi = (sequence_count+1) * INTEGER_BYTES + 1;
    assert(binary[pi++] == DEL);
    #else
    int pi = (sequence_count+1) * INTEGER_BYTES + 2;
    #endif

    FoundMap * all_maps = (FoundMap *) calloc(sequence_count, sizeof(FoundMap));
    for(int sequence = 0;sequence < sequence_count;sequence++){

        /* sequence vector */
        all_maps[sequence].seq_id = get_integer(&binary[si]);si=si+INTEGER_BYTES;

        /* linking */ 
        if(sequence != sequence_count-1)
             all_maps[sequence].next = &all_maps[sequence+1];
        else all_maps[sequence].next = NULL;

        /* position vector */
        int len_positions = get_integer(&binary[pi]);pi=pi+INTEGER_BYTES;

        #ifdef TEST
        printf("[BIN] seq_id=%d, len_positions=%d\n", all_maps[sequence].seq_id, len_positions);
        #endif

        pos_link * all_positions = (pos_link *) calloc(len_positions, sizeof(pos_link));
        all_maps[sequence].positions = all_positions;
        for(int position=0;position<len_positions;position++){
            all_positions[position].location = get_integer(&binary[pi]);pi=pi+INTEGER_BYTES;
            all_positions[position].size     = get_integer(&binary[pi]);pi=pi+INTEGER_BYTES;

            /* linking */
            if(position != len_positions-1)
                 all_positions[position].next = &all_positions[position+1];
            else all_positions[position].next = NULL;

            #ifdef TEST
            printf("[BIN][OBS] location=%d, size=%d, next_addr=%u\n", 
                all_positions[position].location, 
                all_positions[position].size, 
                all_positions[position].next);
            #endif
        }

        #ifndef OPTIMIZED
        assert(binary[pi++]==DEL);
        #else
        pi++;
        #endif
    }

    #ifndef OPTIMIZED
    assert(binary[pi]==END);
    #endif

    return all_maps;
}


void destroy_foundmap(FoundMap * map){
    FoundMap *current = map, *next_map;
    while(current!=NULL){

        /* clearing position list */
        pos_link *list = current->positions, *next;
        while(list!=NULL){
            next = list->next;
            free(list);
            list = next;
        }

        next_map = current->next;
        free(current);
        current = next_map;
    }
}


void destroy_node(chain_node * node){
    destroy_foundmap(node->foundmap);
    free(node->label);
    free(node);
}


#ifdef STRUCT_MAIN
int main(int argc, char * argv[]){

    tree_node * root = initial_tree(NULL);
    printf("here we have a root\n");

    char * frame = argv[1];
    printf("we have a frame -> %s (size=%ld)\n", frame, strlen(frame));

    char * new_frame = str_plus_char(frame, 'G');
    printf("also we have a new frame plus G -> %s (size=%ld)\n", new_frame, strlen(new_frame));

    char * nully = NULL;
    char * after_nully = str_plus_char(nully, 'A');
    printf("we add A character to our nully now we have after_nully -> %s (size=%ld)\n", after_nully, strlen(after_nully));

    add_frame(root, frame, 0, 5, 6, 0);
    printf("we added a frame to our tree");

    return 0;
}
#endif