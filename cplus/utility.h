#ifndef _FUZZY_UTILITY_H
#define _FUZZY_UTILITY_H

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>

#define INTEGER_BYTES 4

int read_integer(FILE * data);
double read_double(FILE * data);
char * read_string(FILE * data, int size);
char * read_str(FILE * data, int size);
void logit(char * message, char * logfile);
void put_integer(uint8_t * here, int n);
int get_integer(uint8_t * here);
double pwm_find(double * compact_pwm, int motif_size, char alphabet, int position, bool reverse);
int max_integer(int a, int b);
double max_double(double a, double b);

#endif