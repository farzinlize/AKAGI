#include "worker.h"

/* global variables used by interrupt handler */
bool MOTHER_ACTIVE = true;
int  exit_code = EXIT_SUCCESS;
mongoc_client_t * bank;
int bank_port;

void mother_interrupt(int signum){
    int signal = getchar();
    switch(signal){
    case SIGNAL_TERMINATE:
    case EOF:
        #ifdef ACK_MOTHER
        putchar(SIGNAL_BYE);
        #endif
        MOTHER_ACTIVE = false;break;
    case SIGNAL_RESUME:
        #ifdef ACK_MOTHER
        putchar(SIGNAL_ACK);
        #endif
        sleep(5);break;
    case SIGNAL_CHANGE_BANK:
        bank_port = read_integer(stdin);
        #ifdef ACK_MOTHER
        putchar(SIGNAL_ACK);
        #endif
        mongoc_client_destroy(bank);
        bank = get_client_c(bank_port);break;
    default:
        #ifdef ACK_MOTHER
        putchar(SIGNAL_NACK);
        #endif
        MOTHER_ACTIVE = false;
        exit_code = EXIT_ERROR;
    }
    /* sending unecessary acknowledges to mother */
    #ifdef ACK_MOTHER
    fflush(stdout);
    #endif
}

int error_handler(FILE * stream, int error, chain_node * popy){

    FILE * dump;
    uint8_t * map_data;
    uint32_t label_len, mapbinsize;

    /* logging error based on type */
    switch (error){
    case EMPTY:
        fprintf(stream, "database empty (port:%d)\n", bank_port);
        break;
    case ESTORE:
    case EPOP:
        fprintf(stream, "database failure (port:%d)\n", bank_port);
        break;
    case EJUDGE:
        fprintf(stream, "judge error check comms.log\n");
        break;
    } fflush(stream);

    /* dumping failed job data for later */
    if(error==ESTORE || error==EJUDGE){
        dump = fopen(DUMPER_FILE, "ab");
        label_len = strlen(popy->label);
        fwrite(&label_len, sizeof(int), 1, dump);
        fwrite(popy->label, sizeof(char), label_len, dump);
        map_data = structure_to_binary(popy->foundmap, &mapbinsize);
        fwrite(&mapbinsize, sizeof(int), 1, dump);
        fwrite(map_data, sizeof(uint8_t), mapbinsize, dump);
        fclose(dump);
    }

    /* wait for mother to respond*/
    pause();
    return 0;
}

#ifdef WORKER_MAIN
int main(int argc, char* argv[]){
    
    /* defining variables */
    clock_t now, record;
    char message_buffer[REPORT_MESSAGE_BUFSIZE];
    bool check, empty_error;
    uint jobs_done_by_me = 0, chaining_done_by_me = 0, message_index;

    /* initiating report file with process id */
    char report_file[NAME_BUFFER_SIZE], errors_file[NAME_BUFFER_SIZE];
    sprintf(report_file, REPORT_FILE_NAME, getpid());
    sprintf(errors_file, ERRORS_FILE_NAME, getpid());
    FILE * report = fopen(report_file, "w");
    FILE * errors = fopen(errors_file, "w");

    #ifdef DEBUG_WORKER
    fprintf(report, "[DEBUG] worker is here\n");fflush(report);
    #endif

    /* declare signal handler to hear mother messages */
    signal(SIGINT, mother_interrupt);

    /* initial mongo driver */
    mongoc_init();

    /* parse arguments and load data */
    if(argc != NUMBER_OF_ARGS){fprintf(report, "EXIT ON ERROR - not a correct number of arguments\n");return EXIT_ERROR;}
    bank_port = atoi(argv[BANK_PORT_INDEX]);
    int judge_port = atoi(argv[JUDGE_PORT_INDEX]);
    on_sequence onsequence = open_on_sequence(argv[ONSEQUENCE_INDEX]);
    dataset compact_data = load_compact_dataset(argv[COMPACT_INDEX]);
    int overlap = atoi(argv[OVERLAP_INDEX]);
    int gap = atoi(argv[GAP_INDEX]);
    int q = atoi(argv[Q_INDEX]);

    #ifdef DEBUG_WORKER
    fprintf(report, "[DEBUG] parsing arguments are done (bank port %d | judge port %d)\n", bank_port, judge_port);fflush(report);
    #endif

    /* connecting to other processes */
    bank = get_client_c(bank_port);

    #ifdef DEBUG_WORKER
    fprintf(report, "[DEBUG] bank access is established\n");fflush(report);
    #endif

    int judge = connect_communication(judge_port);
    if(judge == -1){fprintf(report, "EXIT ON ERROR - judge communication failed (port:%d)", judge_port); return EXIT_ERROR;}

    #ifdef DEBUG_WORKER
    fprintf(report, "[DEBUG] connection to other processes are established\n");fflush(report);
    #endif

    while(MOTHER_ACTIVE){

        /* starting message line for report */
        message_index = 0;

        /* obtaining a job */
        chain_node motif;
        check = pop_chain_node(bank, &motif, &empty_error);
        if(!check){error_handler(errors, empty_error?EMPTY:EPOP, NULL);continue;}
        jobs_done_by_me++;

        #ifdef DEBUG_WORKER
        fprintf(report, "[DEBUG] popy motif -> %s\n", motif.label);fflush(report);
        #endif

        /* evaluating the motif (drop on judge decide) */
        double scores[3];
        now = clock();       // [CAPTURE]
        scores[SUMMIT_INDEX] = summit_score(compact_data, motif);
        scores[SSMART_INDEX] = ssmart_score(compact_data, motif);
        scores[JASPAR_INDEX] = pwm_score   (compact_data, motif);
        record = clock() - now;
        message_index += sprintf(&message_buffer[message_index], "[EVA:%ld]", record);
        
        #ifdef DEBUG_WORKER
        fprintf(report, "[DEBUG] socors -> %f, %f, %f\n", scores[0], scores[1], scores[2]);fflush(report);
        #endif

        /* talk with judge and ignore low ranks patterns */
        now = clock();       // [CAPTURE]
        check = send_report(judge, &motif, scores, &empty_error);
        if(empty_error) {error_handler(errors, EJUDGE, &motif); continue;}
        record = clock() - now;
        
        #ifdef DEBUG_WORKER
        fprintf(report, "[DEBUG] judge call -> %s\n", check?"GO":"IGNORE");fflush(report);
        #endif

        if(!check) continue;
        message_index += sprintf(&message_buffer[message_index], "[JUG:%ld]", record);
        
        /* chaining */
        now = clock();       // [CAPTURE]
        chain_link * next_generation = 
            next_chain(motif, onsequence, compact_data.sequence_count, overlap, gap, q);
        record = clock() - now;
        message_index += sprintf(&message_buffer[message_index], "[CHN:%ld]", record);
        
        #ifdef DEBUG_WORKER
        fprintf(report, "[DEBUG] chaining done in %ld clock (number of next-gen -> %d)\n", record, len_chain_link(*next_generation));
        fflush(report);

        chain_node * testy = next_generation->node;
        if(testy != NULL){
            uint32_t testy_size; uint8_t * testy_bin = structure_to_binary(testy->foundmap, &testy_size);
            fprintf(report, "[DEBUG] test chaining result -> first item data size = %d\n", testy_size);
            fflush(report);
        }
        #endif

        /* storing next generation */
        now = clock();       // [CAPTURE]
        check = store_many_chains(*next_generation, bank);
        record = clock() - now;
        if(!check){error_handler(errors, ESTORE, &motif);continue;}
        message_index += sprintf(&message_buffer[message_index], "[DBS:%ld]", record);

        #ifdef DEBUG_WORKER
        fprintf(report, "[DEBUG] next-generation is stored in %ld clock\n", record);fflush(report);
        #endif

        /* clean trash */
        clean_chain_link(next_generation);
        destroy_node(&motif, false);

        #ifdef DEBUG_WORKER
        fprintf(report, "[DEBUG] memory cleaning is done\n");fflush(report);
        #endif

        /* report to user in file */
        chaining_done_by_me++;
        message_buffer[message_index] = '\x00';
        fprintf(report, "%s\n", message_buffer);fflush(report);
    }
    
    /* clean ending */
    mongoc_client_destroy(bank);
    mongoc_cleanup();

    return 0;
}
#endif