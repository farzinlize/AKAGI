#include "mongo.h"

char * secret_pass(){

    FILE * secretfile;
    char *js, *pass;
    long numbytes;
 
    /* check if secret is available */
    if(access(MONGO_SECRET, F_OK) != 0){
        logit("mongo secret file dose not exist", DATABASE_LOG);
        return NULL;
    }

    /* read content of secret file */
    secretfile = fopen(MONGO_SECRET, "r");
    fseek(secretfile, 0L, SEEK_END);
    numbytes = ftell(secretfile);
    fseek(secretfile, 0L, SEEK_SET);	
    js = (char*)calloc(numbytes, sizeof(char));	
    fread(js, sizeof(char), numbytes, secretfile);
    fclose(secretfile);
 
    /* parse json */
    jsmn_parser parser;
    jsmntok_t tokens[12];
    jsmn_init(&parser);
    jsmn_parse(&parser, js, strlen(js), tokens, 12);

    /* extract password (expected to be in index number 4) */
    jsmntok_t pass_token = tokens[4];
    int size = pass_token.end - pass_token.start;
    pass = (char *) calloc(size, sizeof(char));
    for(int i=pass_token.start,j=0;i<pass_token.end;i++,j++)
        pass[j] = js[i];
    
    free(js);
    return pass;
}


mongoc_client_t * get_client_c(int port){

    char uri_string[70];
    char * password = secret_pass(); if(password==NULL) return NULL;
    sprintf(uri_string, MONGO_ADDRESS, DB_USER, password, port, DB_NAME);

    mongoc_uri_t * uri = mongoc_uri_new (uri_string);
    mongoc_client_t *client = mongoc_client_new_from_uri (uri);
    mongoc_client_set_appname (client, APP_NAME);

    mongoc_uri_destroy(uri);
    free(password);
    return client;
}


/* saving next generation */
bool store_many_chains(chain_link items, mongoc_client_t * client){

    mongoc_collection_t * collection = mongoc_client_get_collection(client, DB_NAME, QUEUE_COLLECTION);
    chain_link current = items;

    int order_size = 0; bool reorder = false, exit_code = true, check;
    bson_t ** order = (bson_t **) calloc(MAX_ORDER_SIZE, sizeof(bson_t *));
    // bson_t * documents = (bson_t *) calloc(MAX_ORDER_SIZE, sizeof(bson_t));

    /* unordered option for inserting many documents */
    bson_error_t error;
    bson_t opts = BSON_INITIALIZER;
    BSON_APPEND_BOOL (&opts, "ordered", false);

    #ifdef DEBUG_MONGO
    bson_t reply = BSON_INITIALIZER;
    printf("[STORE] starting processing input objects into bson\n");
    #endif

    while (current.node != NULL){

        /* send order in case of too many documents */
        if(order_size == MAX_ORDER_SIZE){

            #ifdef DEBUG_MONGO
            printf("[STORE] order array filled - send out data to server\n");
            #endif

            if(!mongoc_collection_insert_many(collection, order, order_size, &opts, NULL, &error)){
                logit(error.message, DATABASE_LOG); 
                exit_code = false; break;
            }
            order_size = 0; reorder = true;
        }

        /* making BSON object to order */
        bson_t * current_order = bson_new();
        if(reorder) bson_destroy(order[order_size]);
        order[order_size++] = current_order;

        #ifdef DEBUG_MONGO
        printf("[STORE] ---- initialzing bson number %d (reorder->%s)\n", order_size, reorder?"yes":"no");
        #endif

        /* generating mongo ID */
        bson_oid_t new_id; bson_oid_init(&new_id, NULL);
        check = bson_append_binary(current_order, MONGO_ID_KEY, MONGO_ID_KEY_LEN, BSON_SUBTYPE_BINARY, new_id.bytes, 12);

        #ifdef DEBUG_MONGO
        char id_string[25]; bson_oid_to_string(&new_id, id_string);
        printf("[STORE] ---- appending check: %s | appending _id (id=%s)\n", check?"success":"failed", id_string);
        #endif

        /* appending node data (label and binary structure) */
        uint32_t binary_size; uint8_t * data = structure_to_binary(current.node->foundmap, &binary_size);
        check &= bson_append_binary(current_order, MONGO_DATA_KEY, MONGO_DATA_KEY_LEN, BSON_SUBTYPE_BINARY, data, binary_size);

        #ifdef DEBUG_MONGO
        printf("[STORE] ---- appending check: %s | structure to binary size -> %u\n", check?"success":"failed", binary_size);
        #endif

        check &= bson_append_utf8(current_order, MONGO_LABEL_KEY, MONGO_LABEL_KEY_LEN, current.node->label, -1);

        #ifdef DEBUG_MONGO
        printf("[STORE] ---- appending check: %s | appending label -> %s\n", check?"success":"failed", current.node->label);
        printf("[STORE] bson number %d is done\n", order_size);
        #endif

        if(current.next == NULL) break;
        else current = *current.next;
    }
    
    #ifdef DEBUG_MONGO
    printf("[STORE] no more orders (last order_size -> %d and reorder -> %s)\n", order_size, reorder?"yes":"no");
    if(order_size > 0 && exit_code && !mongoc_collection_insert_many(collection, order, order_size, &opts, &reply, &error)){
    #else
    if(order_size > 0 && exit_code && !mongoc_collection_insert_many(collection, order, order_size, &opts, NULL, &error)){
    #endif
        logit(error.message, DATABASE_LOG);
        exit_code = false;

        #ifdef DEBUG_MONGO
        size_t l; char * json = bson_as_json(&reply, &l);
        FILE * f =fopen("DEBUG_reply.json", "w");
        fwrite(json, sizeof(char), l, f); fclose(f);
        #endif
    }

    #ifdef DEBUG_MONGO
    printf("[STORE][FREE] starting to free occupied data (exit_code=%s)\n", exit_code?"success":"ERROR");
    bson_destroy(&reply); 
    #endif

    /* free memory */
    bson_destroy(&opts); 
    mongoc_collection_destroy(collection);
    if(reorder) order_size = MAX_ORDER_SIZE;
    for(int i=0;i<order_size;i++) bson_destroy(order[i]);
    free(order);

    #ifdef DEBUG_MONGO
    printf("[STORE] goodbye\n");
    #endif

    return exit_code;
}


/* pop a job from queue */
bool pop_chain_node(mongoc_client_t * client, chain_node * popy, bool * empty){

    /* binary to structure foundmap */
    popy->foundmap_mode = FOUNDMAP_ARRAY;

    mongoc_collection_t * collection = mongoc_client_get_collection(client, DB_NAME, QUEUE_COLLECTION);
    bson_error_t error; bson_t dummy_query = BSON_INITIALIZER, reply;
    
    if(!mongoc_collection_find_and_modify(collection, &dummy_query, NULL, NULL, NULL, true, false, false, &reply, &error)){
        logit(error.message, DATABASE_LOG);
        return false;
    }

    /* parse replied bson to chain node */
    bson_iter_t iterator, value;
    bool check = bson_iter_init_find(&value, &reply, "value") && bson_iter_recurse(&value, &iterator);
    if(!check){*empty = true;return false;}
    else       *empty = false;

    #ifdef TEST
    size_t l;
    char * json = bson_as_json(&reply, &l);
    FILE * f =fopen("bson.test", "w");
    fwrite(json, sizeof(char), l, f); fclose(f);
    printf("[REPLY] key->%s type->%d\n", bson_iter_key(&value), bson_iter_type(&value));
    #endif

    while(bson_iter_next(&iterator)){

        #ifdef TEST
        printf("[ITER] key->%s type->%d\n", bson_iter_key(&iterator), bson_iter_type(&iterator));
        #endif

        /* binary data field for foundmap */
        if(!strcmp(MONGO_DATA_KEY, bson_iter_key(&iterator))) {
            unsigned int data_size; uint8_t * data;
            bson_iter_binary(&iterator, NULL, &data_size, &data);

            #ifdef TEST
            printf("[DATA] size=%d (size of uint8_t is %d)\n", data_size, sizeof(uint8_t));
            FILE * f = fopen("test_bin.data", "wb");
            fwrite(data, sizeof(uint8_t), data_size, f); fclose(f);
            #endif

            popy->foundmap = binary_to_structure(data);
        }
        
        /* label filed */
        else if(!strcmp(MONGO_LABEL_KEY, bson_iter_key(&iterator))){
            unsigned int label_size;
            const char * label = bson_iter_utf8(&iterator, &label_size);
            popy->label = (char *) calloc(label_size+1, sizeof(char));
            strcpy(popy->label, label);
        }
    }

    /* free space */
    bson_destroy(&reply);
    mongoc_collection_destroy(collection);
    return true;
}



#ifdef MONGO_MAIN

/* mongo test modes */
// #define TEST_1
// #define NO_RESTORE
// #define NO_POPY
// #define POP_AFTER
#define TEST_2

int main(){
    printf("[CPLUS/MONGO][TEST][V3]\n");

    /* initial library */
    mongoc_init();

    /* get client ready */
    mongoc_client_t * client = get_client_c(MONGO_PORT);

    #ifdef TEST_1
    /* ###############################################
     * test#1 
     * pop, observe, restore
     * ############################################### */

    chain_node popy; bool check; bool empty;
    #ifndef NO_POPY
    /* POP */
    check = pop_chain_node(client, &popy, &empty);
    printf("pop->%s\n", check?"pass":"ERROR");

    /* observe */
    printf("popy label: %s (foundmap will be temporarily stored in popy_test.data)\n", popy.label);
    // FoundMap * current = popy.foundmap;
    // while(current!=NULL){
    //     printf("[FOUNDMAP] seq_id=%d, positions count = %d\n", current->seq_id, intlen_positions(current->positions));
    //     current = current->next;
    // }
    uint32_t data_size;
    uint8_t * data = structure_to_binary(popy.foundmap, &data_size);
    printf("data transform to foundmap successfully -> data size = %d\n", data_size);
    FILE * f = fopen("popy_test.data", "wb");
    fwrite(data, sizeof(uint8_t), data_size, f); fclose(f);
    #else
    printf("(using dummy chain nodes to test storing procedure)\n");
    popy.label = "dummy";
    FILE * f = fopen("popy_test.data", "rb");
    fseek(f, 0L, SEEK_END);
    long numbytes = ftell(f);
    fseek(f, 0L, SEEK_SET);	
    uint8_t * data = (uint8_t*)calloc(numbytes, sizeof(uint8_t));	
    fread(data, sizeof(uint8_t), numbytes, f); fclose(f);
    popy.foundmap = binary_to_structure(data);
    free(data);
    #endif

    #ifndef NO_RESTORE
    /* restore */
    chain_link store_1;
    store_1.node = &popy;
    store_1.next = NULL;

    check = store_many_chains(store_1, client);
    printf("store->%s\n", check?"pass":"ERROR");
    #endif

    #ifdef POP_AFTER
    chain_node after_popy;
    check = pop_chain_node(client, &after_popy, &empty);
    printf("after-pop->%s\n", check?"pass":"ERROR");
    uint32_t data_size;
    uint8_t * after_data = structure_to_binary(after_popy.foundmap, &data_size);
    printf("after popy label -> %s, bin size = %u\n", after_popy.label, data_size);
    #endif

    #endif // TEST_1

    #ifdef TEST_2
    chain_link * empty_one = initial_empty_chain_link();
    bool check = store_many_chains(*empty_one, client);
    printf("check -> %s\n", check?"OK":"ERROR");
    #endif // TEST_2

    /* cleanup library */
    mongoc_client_destroy(client);
    mongoc_cleanup();
    return 0;
}
#endif