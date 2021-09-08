#include<stdio.h>
#include<string.h>
#include<stdlib.h>
#include<unistd.h>

#include"structures.h"

//  global defines (constants)

#define REPORT_FILE_NAME "process_%d.report"
#define NAME_BUFFER_SIZE 22
#define EXIT_ERROR -1

#define BANK_PORT_INDEX 1
#define ONSEQUENCE_INDEX 2

#define IMPORTANT_LOG '00_important_00.log'

int empty_handler(){
    return 0;
}

int error_handler(int error){
    return 0;
}

int main(int argc, char* argv[]){

    printf("IN\n");
    // initiating report file with process id
    char report_file[NAME_BUFFER_SIZE];
    sprintf(report_file, REPORT_FILE_NAME, getpid());
    FILE * report = fopen(report_file, "w");

    // parse arguments
    if(argc != 3){fprintf(report, "EXIT ON ERROR - not a correct number of arguments");return EXIT_ERROR;}

    int bank_port = atoi(argv[BANK_PORT_INDEX]);
    on_sequence onsequence = open_on_sequence(argv[ONSEQUENCE_INDEX]);

    #ifdef TEST
    printf("sequences count -> len(struct) -> %u\n", onsequence.sequence_count);
    for(int i=0;i<200;i++)
        printf("seq_id:%d-len(%d)", i, onsequence.sequence_lengths[i]);
    // random check
    int seq_id = 6, location = 27; 
    char ** list = onsequence.data[seq_id][location];
    char * current_str = list[0];
    int count = 0;
    while (current_str != NULL){
        printf("(%s)", current_str);
        current_str = list[++count];
    }
    printf("\ncount = %d", count);
    #endif

    printf("HOW MUCH IS DONE HAS DONE ANYWAY");
    return 0;
}