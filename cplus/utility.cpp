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

double read_double(FILE * data){
    double read;
    fread(&read, sizeof(double), 1, data);
    return read;
}


char * read_string(FILE * data, int size){
    char * result = (char *) calloc(size+1, sizeof(char));
    fread(result, sizeof(char), size, data);
    return result;
}


/* just like read_string but using fgetc instead of fread */
char * read_str(FILE * data, int size){
    char * result = (char *) malloc(size+1);
    for(int i=0;i<size;i++){
        result[i] = fgetc(data);
    }
    result[size] = '\0';
    return result;
}

void logit(char * message, char * logfile){
    time_t date = time(NULL);
    FILE * log = fopen(logfile, "a");
    fprintf(log, "[%.19s]%s\n", ctime(&date), message);
    fclose(log);
}

void put_integer(uint8_t * here, int n){
    here[0] = (n >> 24) & 0xFF;
    here[1] = (n >> 16) & 0xFF;
    here[2] = (n >> 8 ) & 0xFF;
    here[3] =  n        & 0xFF;
}

int get_integer(uint8_t * here){
    return (here[3]) + (here[2] << 8) + (here[1] << 16) + (here[0] << 24);
}

double pwm_find(double * compact_pwm, int motif_size, char alphabet, int position, bool reverse){

    int a;
    switch (alphabet){
    case 'A':a = 0;break;
    case 'C':a = 1;break;
    case 'G':a = 2;break;
    case 'T':a = 3;break;
    }

    int position_on_array = a*motif_size*2 + (position*2 + reverse);
    return compact_pwm[position_on_array];
}

double max_double(double a, double b){
    if(a > b) return a;
    else      return b;
}

int max_integer(int a, int b){
    if(a > b) return a;
    else      return b;
}