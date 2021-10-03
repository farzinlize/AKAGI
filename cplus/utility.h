#ifndef _FUZZY_UTILITY_H
#define _FUZZY_UTILITY_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define INTEGER_BYTES 4

int read_integer(FILE * data);
double read_double(FILE * data);
char * read_string(FILE * data, int size);
char * read_str(FILE * data, int size);
void logit(char * message, char * logfile);
void put_integer(unsigned char * here, int n);
int get_integer(unsigned char * here);
double pwm_find(double * compact_pwm, int motif_size, char alphabet, int position, bool reverse);

#endif