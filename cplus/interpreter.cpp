#include"interpreter.h"

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
        }
        command = getchar();printf("\n");
    }
}


#ifdef INTERPRETER_MAIN
int main(int argc, char * argv[]){

    struct termios info;
    tcgetattr(0, &info);          /* get current terminal attirbutes; 0 is the file descriptor for stdin */
    info.c_lflag &= ~ICANON;      /* disable canonical mode */
    info.c_cc[VMIN] = 1;          /* wait until at least one keystroke available */
    info.c_cc[VTIME] = 0;         /* no timeout */
    tcsetattr(0, TCSANOW, &info); /* set immediately */

    chain_node motif;
    FILE * motif_data = fopen(argv[1], "rb");
    int label_size, bin_size;
    uint8_t * bin;
    if(!strcmp(argv[2], "node")){
        label_size = read_integer(motif_data);
        motif.label = read_string(motif_data, label_size);
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
    foundmap_scroll(motif.foundmap);
}
#endif