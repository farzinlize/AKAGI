#ifndef _COMMUNICATION_H
#define _COMMUNICATION_H

#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <arpa/inet.h>	
#include "utility.h"
#include "global.h"
#include "structures.h"

#define COMMUNICATION_LOG "comms.log"

/* equals to 3 double (8 byte) */
#define SCORE_PACK_SIZE 24

int connect_communication(int port);
bool send_report(int judge_fd, chain_node * node, double scores[3]);

#endif