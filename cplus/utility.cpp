#include"utility.h"

int read_integer(FILE * data){
    // char * bytes = (char *) malloc(INTEGER_BYTES);
    unsigned char byte = 0;
    int result;
    for(int i=INTEGER_BYTES-1;i>=0;i--){
        byte = fgetc(data);
        result = result + byte << i*8;
    }
    return result;
}

char * read_str(FILE * data, int size){
    char * result = (char *) malloc(size+1);
    for(int i=0;i<size;i++){
        result[i] = fgetc(data);
    }
    result[size] = NULL;
    return result;
}

void logit(char * message, char * logfile){
    FILE * log = fopen(logfile, "a");
    fprintf(log, message);
    fclose(log);
}