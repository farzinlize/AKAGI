#ifndef _GLOBAL_DEFINES_H
#define _GLOBAL_DEFINES_H

/*              compilation modes                */
/* DEBUG: activate debuging prints and reports   */
/* OPTIMIZED: remove unnecessary parts           */
/* or simply nothing specifiec                   */


/* all available mains are included here       */
/* but building with make ignore these defines */
#ifndef MAKE_MAKE
#define WORKER_MAIN
#define ALG_MAIN
#define STRUCT_MAIN
#define COMMS_MAIN
#define MONGO_MAIN
#endif
/* ---------------- */

#define DATABASE_LOG "database.log"
#define REPORT_MESSAGE_BUFSIZE 64

/* scores */
#define SCORES_COUNT 3
#define SUMMIT_INDEX 0
#define SSMART_INDEX 1
#define JASPAR_INDEX 2


#endif