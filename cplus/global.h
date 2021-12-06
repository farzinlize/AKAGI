#ifndef _GLOBAL_DEFINES_H
#define _GLOBAL_DEFINES_H

/*              compilation modes                  */
/* OPTIMIZED: remove unnecessary parts             */
/* DEBUG_WORKER: only activate main worker reports */
/* DEBUG_STRUCTURE: structures module debug mode   */
/* DEBUG_MONGO: database module debug mode         */
/* DEBUG_PWM: pwm score debug                      */
/* DEBUG_CHAINING: next_chain function debug parts */
/* or simply nothing specifiec                     */


/* all available mains are included here            */
/* but building with make will ignore these defines */
#ifndef MAKE_MAKE
#define WORKER_MAIN
#define ALG_MAIN
#define STRUCT_MAIN
#define COMMS_MAIN
#define MONGO_MAIN
#define UTILITY_MAIN
#define INTERPRETER_MAIN
#endif
/* ------------------------------------------------ */

#define AKAGI_PATH_FILE "akagi.pwd"
#define DATABASE_LOG    "database.log"
#define DUMPER_FILE     "dumped.motifs"
#define REPORT_MESSAGE_BUFSIZE 64
#define FOUNDMAP_NOARRAY false
#define FOUNDMAP_ARRAY   true

/* scores */
#define SCORES_COUNT 3
#define SSMART_INDEX 0
#define SUMMIT_INDEX 1
#define JASPAR_INDEX 2


#endif