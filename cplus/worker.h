/* built-in C libraries */
#include<stdio.h>
#include<string.h>
#include<stdlib.h>
#include<unistd.h>
#include<signal.h>
#include<time.h>

/* project libraries */
#include"structures.h"
#include"mongo.h"
#include"comms.h"
#include"algorithm.h"
#include"utility.h"

/* global contants */
#include"global.h"

#define REPORT_FILE_NAME "process_%d.report"
#define ERRORS_FILE_NAME "process_%d.errors"
#define NAME_BUFFER_SIZE 22

/* fixed position arguments for process */
#define BANK_PORT_INDEX  1
#define JUDGE_PORT_INDEX 2
#define ONSEQUENCE_INDEX 3
#define COMPACT_INDEX    4
#define OVERLAP_INDEX    5
#define GAP_INDEX        6
#define Q_INDEX          7

/* errors */
#define EMPTY   0
#define EPOP    1
#define ESTORE  2

/* mother signals */
#define SIGNAL_RESUME      'R'
#define SIGNAL_CHANGE_BANK 'C'
#define SIGNAL_TERMINATE   'T'

/* unnecessary message passing for mother */
#ifndef OPTIMIZED
#define SIGNAL_ACK  'A'
#define SIGNAL_BYE  'B'
#define SIGNAL_NACK 'N'
#endif

#define EXIT_SUCCESS 0
#define EXIT_ERROR -1
