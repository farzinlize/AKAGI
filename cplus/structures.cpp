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


FoundMap * initital_foundmap(int seq_id, int location, int size){
    FoundMap * initialmap = (FoundMap *) malloc(sizeof(FoundMap));
    initialmap->next = NULL;
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
    if(foundmap->seq_id == seq_id){
        pos_link * new_pos = (pos_link *) malloc(sizeof(pos_link));
        new_pos->location = location;
        new_pos->size = size;
        new_pos->next = foundmap->positions;

        foundmap->positions = new_pos;
        return 0;
    }
    else if (foundmap->next == NULL){
        foundmap->next = initital_foundmap(seq_id, location, size);
        return 1;
    }
    else if(foundmap->next->seq_id > seq_id){
        FoundMap * nexty = foundmap->next;
        foundmap->next = initital_foundmap(seq_id, location, size);
        foundmap->next->next = nexty;
        return 1;
    }

    // linear search for seq_id match
    return add_position(foundmap->next, seq_id, location, size);
}

void add_frame(tree_node * node, char * frame, int seq_id, int location, int size, int current_frame_index){

    // end of the path
    if(frame[current_frame_index] == NULL){
        if(node->foundmap == NULL){
            node->foundmap = initital_foundmap(seq_id, location, size);
            node->q = 1;
        }else {
            node->q = node->q + add_position(node->foundmap, seq_id, location, size);
        }
    }

    // select path
    tree_node * next_path;
    switch (frame[current_frame_index]){
    case 'A':next_path = node->children[0];break;
    case 'T':next_path = node->children[1];break;
    case 'C':next_path = node->children[2];break;
    case 'G':next_path = node->children[3];break;
    }

    // create if not exist
    if(next_path == NULL){
        next_path = initial_tree(str_plus_char(node->label, frame[current_frame_index]));

        switch (frame[current_frame_index]){
            case 'A':node->children[0] = next_path;break;
            case 'T':node->children[1] = next_path;break;
            case 'C':node->children[2] = next_path;break;
            case 'G':node->children[3] = next_path;break;
        }
    }
    
    // recursively go to path until reaching destination
    add_frame(next_path, frame, seq_id, location, size, current_frame_index+1);
}


char * str_plus_char(char * s, char n){
    char * result = (char *) malloc(strlen(s)+1);
    sprintf(result, "%s%c", s, n);
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


dataset load_compact_dataset(char * filename){
    int count;
    dataset * result = (dataset *) malloc(sizeof(dataset));
    FILE * compact = fopen(filename, "r");
    fscanf(compact, "%u\n", &count);

    result->p_values = (float *) malloc(sizeof(double)*count);
    result->summits = (int *) malloc(sizeof(int)*count);
    result->sequences = (char **) malloc(sizeof(char *)*count);

    for(int i=0;i<count;i++)
        fscanf(compact, "%s\n%u\n%f\n", &(result->sequences[i]), &(result->summits[i]), &(result->p_values[i]));

    return *result;
}