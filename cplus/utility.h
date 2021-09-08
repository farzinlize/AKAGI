#ifndef _FUZZY_UTILITY_H
#define _FUZZY_UTILITY_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define INTEGER_BYTES 4

int read_integer(FILE * data);
char * read_str(FILE * data, int size);
void logit(char * message, char * logfile);

#endif