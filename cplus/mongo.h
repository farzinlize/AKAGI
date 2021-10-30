#ifndef _MONGO_H
#define _MONGO_H

#include <stdio.h>
#include <mongoc.h>
#include "jsmn.h"
#include "structures.h"
#include "utility.h"
#include "global.h"

#define APP_NAME "AKAGI-cplus"
#define DB_NAME "akagidb"
#define DB_USER "akagi"
#define QUEUE_COLLECTION "queue"
#define MONGO_PORT 2090
#define MONGO_SECRET "../mongo.secret"
#define MONGO_ADDRESS "mongodb://%s:%s@localhost:%d/?authSource=%s"
#define MAX_ORDER_SIZE 1000

#define MONGO_ID_KEY "_id"
#define MONGO_ID_KEY_LEN 3

#define MONGO_LABEL_KEY "l"
#define MONGO_LABEL_KEY_LEN 1

#define MONGO_DATA_KEY "data"
#define MONGO_DATA_KEY_LEN 4

mongoc_client_t * get_client_c(int port);
bool store_many_chains(chain_link items, mongoc_client_t * client);
bool pop_chain_node(mongoc_client_t * client, chain_node * popy, bool * empty);

#endif