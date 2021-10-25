#include "comms.h"

int connect_communication(int port){

    /* creating socket */
    int sockfd = 0;
    if ((sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0){
        logit("Socket creation error", COMMUNICATION_LOG);
        return -1;
    }

    /* connecting to local host */
    struct sockaddr_in server;
    server.sin_addr.s_addr = inet_addr("127.0.0.1");
	server.sin_family = AF_INET;
	server.sin_port = htons(port);
    if (connect(sockfd , (struct sockaddr *)&server , sizeof(server)) < 0){
		logit("connect error", COMMUNICATION_LOG);
		return -1;
	}
	
    /* returning socket discriptor */
    return sockfd;
}

bool send_report(int judge_fd, chain_node * node, double scores[3]){

    uint8_t judge_call;

    /* sending scores to judge */
    send(judge_fd, scores, SCORE_PACK_SIZE, 0);

    /* ignore sending pattern if judge doesn't want it */
    recv(judge_fd, &judge_call, 1, 0);
    if(judge_call == '\0') return false;

    /* sending pattern label */
    uint32_t label_size = strlen(node->label), data_size;
    send(judge_fd, &label_size, sizeof(uint32_t), 0);
    send(judge_fd, node->label, label_size, 0);

    /* sending pattern data */
    uint8_t * data = structure_to_binary(node->foundmap, &data_size);
    send(judge_fd, &data_size, sizeof(uint32_t), 0);
    send(judge_fd, data, data_size, 0);

    return true;
}

#ifdef COMMS_MAIN
int main(){
    
    chain_node popy;

    printf("(using dummy chain nodes to test communication)\n");
    popy.label = "dummy";
    FILE * f = fopen("popy_test.data", "rb");
    fseek(f, 0L, SEEK_END);
    long numbytes = ftell(f);
    fseek(f, 0L, SEEK_SET);	
    uint8_t * data = (uint8_t*)calloc(numbytes, sizeof(uint8_t));	
    fread(data, sizeof(uint8_t), numbytes, f); fclose(f);
    popy.foundmap = binary_to_structure(data);
    free(data);

    double scores[3] = {1.34, 99.56, 78.145};

    int judge = connect_communication(2091);
    send_report(judge, &popy, scores);
    printf("[MAIN] DONE\n");

    // int sockfd = 0;

    // if ((sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0){
    //     printf("\n Socket creation error \n");
    //     return -1;
    // }

    // struct sockaddr_in server;

    // server.sin_addr.s_addr = inet_addr("127.0.0.1");
	// server.sin_family = AF_INET;
	// server.sin_port = htons( 2091 );

    // if (connect(sockfd , (struct sockaddr *)&server , sizeof(server)) < 0){
	// 	printf("connect error\n");
	// 	return -1;
	// }
	
	// printf("Connected\n");
	
	// //Send some data
	// char message[100] = "hi its me\n";
	// if( send(sockfd , message , strlen(message) , 0) < 0){
	// 	printf("Send failed\n");
	// 	return -1;
	// }
	// printf("Data Send\n");

    // char server_reply[2000];
    // int byte_read;
    // if( (byte_read = recv(sockfd, server_reply , 2000 , 0)) < 0){
	// 	printf("recv failed\n");
	// }
	// printf("Reply received -> size=%d\n", byte_read);
    // int a = get_integer((uint8_t *) server_reply);
	// printf("%d\n", a);

    // return 0;
}
#endif