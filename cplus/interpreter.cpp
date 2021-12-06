#include"interpreter.h"


void tree_check(){
    int that_location, that_size, that_seqid;
    char custom_frame[20], command, a_location[10], a_size[10], a_seqid[10];
    tree_node * tree = initial_tree(NULL), *node;

    printf("WELCOME to tree check, commands are listed below:\n"
           "a: add a custom frame to a tree\n"
           "f: scroll through a foundmap\n"
           "q: show stored q value at node\n"
           "e: for exit\n");
    
    command = getchar();printf("\n");

    while(command != 'e'){
        if      (command == 'a'){
            printf("[ENTER] frame: ");
            fgets(custom_frame, 20, stdin); custom_frame[strcspn(custom_frame, "\n")]=0;
            printf("[ENTER] seq_id: ");
            fgets(a_seqid, 10, stdin);that_seqid = atoi(a_seqid);
            printf("[ENTER] location: ");
            fgets(a_location, 10, stdin);that_location = atoi(a_location);
            printf("[ENTER] size: ");
            fgets(a_size, 10, stdin);that_size = atoi(a_size);

            add_frame(tree, custom_frame, that_seqid, that_location, that_size, 0);
        }else if(command == 'f'){
            printf("[ENTER] kmer: ");
            fgets(custom_frame, 20, stdin); custom_frame[strcspn(custom_frame, "\n")]=0;

            if((node = search_node(tree, custom_frame, 0)) != NULL) foundmap_scroll(node->foundmap);
            else printf("node doesn't exist\n");
        }else if(command == 'q'){
            printf("[ENTER] kmer: ");
            fgets(custom_frame, 20, stdin); custom_frame[strcspn(custom_frame, "\n")]=0;

            if((node = search_node(tree, custom_frame, 0)) != NULL) printf("q=%d\n", node->q);
            else printf("node doesn't exist\n");
        }else{
            printf("--doesn't recognize command--\n");
        }
        command = getchar();printf("\n");
    }
}


void foundmap_scroll(FoundMap * map){
    char command, a_number[10];
    int that_number;

    printf("WELCOME to foundmap interpreter-like visualization, list of commands are below:\n"
           "-> q: returns quorom or len(sequence_vector)\n"
           "-> 0: show sequence vector containing sequence ids\n"
           "-> 1: followed by an integer as sequence id will show position_vector at specific sequence\n"
           "-> e: for exit\n");
    command = getchar();printf("\n");

    while(command != 'e'){
        if      (command == 'q'){
            printf("q=%d\n", get_q(map));
        }else if(command == '0'){
            show_sequence_vector(map);
        }else if(command == '1'){
            printf("[ENTER] positions on what sequence? _\n");
            fgets(a_number, 10, stdin); that_number = atoi(a_number);
            show_position_vector_at(map, that_number);
        }else{
            printf("--doesn't recognize command--\n");
        }
        command = getchar();printf("\n");
    }

    printf("exit - bye\n");
}


void chaining_scroll(chain_node node, on_sequence onseq){
    int overlap, gap, q, that_number;
    char a_number[10], command;
    chain_link * results, *this_link;

    printf("[ENTER] chaining parameter: overlap?  ");
    fgets(a_number, 10, stdin); overlap = atoi(a_number);
    printf("[ENTER] chaining parameter: gap?  ");
    fgets(a_number, 10, stdin); gap = atoi(a_number);
    printf("[ENTER] chaining parameter: quorum?  ");
    fgets(a_number, 10, stdin); q = atoi(a_number);

    results = next_chain(node, onseq, onseq.sequence_count, overlap, gap, q);

    printf("--chaining done--\n"
           "press commands below for more information:\n"
           "l: for number of next-generation motifs\n"
           "g: go inside of foundmap structure of a hit\n"
           "e: for exit\n");

    command = getchar(); printf("\n");
    while(command != 'e'){
        if(command == 'l'){
            int length = 0;
            this_link = results;
            while(this_link->node != NULL){
                length++;
                if(this_link->next == NULL) break;
                this_link = this_link->next;
            }
            printf("number of result -> %d\n", length);
        }else if(command == 'g'){
            printf("[ENTER] how far?  ");
            fgets(a_number, 10, stdin); that_number = atoi(a_number);

            this_link = results;
            for(int far_away=0; far_away<that_number; far_away++) this_link = this_link->next;
            printf("--> scrolling a next-generation motif foundmap (label:%s, len=%ld)\n", this_link->node->label, strlen(this_link->node->label));
            foundmap_scroll(this_link->node->foundmap);
        }

        command = getchar(); printf("\n");
    }
    printf("--chain byte--\n");
}


void onseq_scroll(on_sequence onseq){
    char command, a_number[10], *z_motif;
    int seq_id, position, z_motif_idx;

    printf("----scrolling onsequence data and information----\n"
           "(sequence count -> %d)\n"
           "q: for query exact sequence id, position and motif idx\n"
           "l: retrive length of sequence\n"
           "N: find Null in z-motifs array (number of motifs at the same position)\n"
           "s: show z-motifs array\n"
           "e: for exit\n"
           , onseq.sequence_count);
    command = getchar();printf("\n");

    while(command != 'e'){
        if (command == 'q'){
            printf("[ENTER] sequence id?  ");
            fgets(a_number, 10, stdin); seq_id = atoi(a_number);
            printf("[ENTER] position?  ");
            fgets(a_number, 10, stdin); position = atoi(a_number);
            printf("[ENTER] motif index?  ");
            fgets(a_number, 10, stdin); z_motif_idx = atoi(a_number);

            z_motif = onseq.data[seq_id][position][z_motif_idx];
            printf("z-motif label: %s, length=%ld\n", z_motif, strlen(z_motif));
        }else if(command == 'l'){
            printf("[ENTER] sequence id?  ");
            fgets(a_number, 10, stdin); seq_id = atoi(a_number);
            
            printf("length of that sequence -> %d\n", onseq.sequence_lengths[seq_id]);
        }else if(command == 'N'){
            printf("[ENTER] sequence id?  ");
            fgets(a_number, 10, stdin); seq_id = atoi(a_number);
            printf("[ENTER] position?  ");
            fgets(a_number, 10, stdin); position = atoi(a_number);

            int i = 0;
            while ((z_motif = onseq.data[seq_id][position][i++]) != NULL);
            printf("number of z-motifs at (seq_id=%d, position=%d)\t\t:%d\n", seq_id, position, i);
        }else if(command == 's'){
            printf("[ENTER] sequence id?  ");
            fgets(a_number, 10, stdin); seq_id = atoi(a_number);
            printf("[ENTER] position?  ");
            fgets(a_number, 10, stdin); position = atoi(a_number);

            int i = 0;
            while ((z_motif = onseq.data[seq_id][position][i++]) != NULL) printf("(%s, len=%ld)\t\t", z_motif, strlen(z_motif));
            printf("\n--(end)-- number of z-motifs at (seq_id=%d, position=%d)\t\t:%d\n", seq_id, position, i); // -1
        }

        command = getchar();printf("\n");
    }

    printf("--(onseq bye)--\n");
}


#ifdef INTERPRETER_MAIN
// #define SCROLL_ONSEQ
int main(int argc, char * argv[]){

    struct termios info;
    tcgetattr(0, &info);          /* get current terminal attirbutes; 0 is the file descriptor for stdin */
    info.c_lflag &= ~ICANON;      /* disable canonical mode */
    info.c_cc[VMIN] = 1;          /* wait until at least one keystroke available */
    info.c_cc[VTIME] = 0;         /* no timeout */
    tcsetattr(0, TCSANOW, &info); /* set immediately */

    if(argc==1) {tree_check(); return 0;}

    #ifdef SCROLL_ONSEQ
        on_sequence onsequence = open_on_sequence(argv[1]);
        onseq_scroll(onsequence);
    #else
    if(argc < 3) {printf("argument count error - atleast specify (1:data-path) and (2:read-mode)\n");return 0;}
    chain_node motif;
    FILE * motif_data = fopen(argv[1], "rb");
    int label_size, bin_size;
    uint8_t * bin;
    if(!strcmp(argv[2], "node")){
        label_size = read_integer(motif_data);
        motif.label = read_string(motif_data, label_size);
        bin_size = read_integer(motif_data);
    }else if(!strcmp(argv[2], "map-sized")){
        motif.label = (char *) calloc(6, sizeof(char));
        sprintf(motif.label, "dummy");
        bin_size = read_integer(motif_data);

    }else if(!strcmp(argv[2], "map-free")){
        motif.label = (char *) calloc(6, sizeof(char));
        sprintf(motif.label, "dummy");
        
        fseek(motif_data, 0L, SEEK_END);
        bin_size = ftell(motif_data);
        fseek(motif_data, 0L, SEEK_SET);
    
    }else{
        printf("specify the file type (`node` if chainNode and `map-(sized or free)` for only binary foundmap)\n"
               "`map-sized` if size of data is written as header or `map-free` if the whole file is just one foundmap\n");
        return 0;
    }
    bin = (uint8_t*) calloc(bin_size, sizeof(uint8_t));
    fread(bin, sizeof(uint8_t), bin_size, motif_data);
    motif.foundmap = binary_to_structure(bin);

    printf("data loaded - investigating chain node (label:%s, bin_size:%d)\n", motif.label, bin_size);
    if(argc > 3){
        if(!strcmp(argv[3], "chain")) {
            on_sequence onseq = open_on_sequence(argv[4]);
            chaining_scroll(motif, onseq);
        }
        else {printf("unkown argument error, %s\n", argv[3]);return 0;}
        return 0;
    }
    foundmap_scroll(motif.foundmap);
    #endif
}
#endif