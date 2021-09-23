#include"utility.h"

int read_integer(FILE * data){
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
    result[size] = '\0';
    return result;
}

void logit(char * message, char * logfile){
    FILE * log = fopen(logfile, "a");
    fprintf(log, "%s", message);
    fclose(log);
}

void put_integer(unsigned char * here, int n){
    here[0] = (n >> 24) & 0xFF;
    here[1] = (n >> 16) & 0xFF;
    here[2] = (n >> 8 ) & 0xFF;
    here[3] =  n        & 0xFF;
}

int get_integer(unsigned char * here){
    return (here[3]) + (here[2] << 8) + (here[1] << 16) + (here[0] << 24);
}