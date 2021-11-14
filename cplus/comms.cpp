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

bool send_report(int judge_fd, chain_node * node, double scores[3], bool * error_flag){

    *error_flag = false;
    uint8_t judge_call, *data;
    ssize_t returned;
    uint32_t label_size, data_size;
    int errsv, sent_data;

    /* sending scores to judge */
    if((returned = send(judge_fd, scores, SCORE_PACK_SIZE, 0)) != 24) goto ERROR;

    /* ignore sending pattern if judge doesn't want it */
    if((returned = recv(judge_fd, &judge_call, 1, 0)) != 1) goto ERROR;
    if(judge_call == '\0') return false;

    /* sending pattern label */
    label_size = strlen(node->label);
    if((returned = send(judge_fd, &label_size, sizeof(uint32_t), 0)) != sizeof(uint32_t)) goto ERROR;
    if((returned = send(judge_fd, node->label, label_size, 0)) != label_size) goto ERROR;

    /* sending pattern data */
    data = structure_to_binary(node->foundmap, &data_size);
    if((returned = send(judge_fd, &data_size, sizeof(uint32_t), 0)) != sizeof(uint32_t)) goto ERROR;

    /* make sure whole data is sent */
    if((returned = send(judge_fd, data, data_size, 0)) != data_size) {
        if (returned == -1) goto ERROR;
        sent_data = returned;
        while(sent_data != data_size){
            if(returned = send(judge_fd, &data[sent_data], data_size-sent_data, 0) == -1) goto ERROR;
            sent_data = sent_data + returned;
        }
    }

    return true;

    /* in case of error report */
    ERROR:
    errsv = errno;
    *error_flag = true;
    char report_error[128];
    sprintf(report_error, "[ERR] errno=%d, returned=%ld", errsv, returned);
    logit(report_error, COMMUNICATION_LOG);
    return false;
}

#ifdef COMMS_MAIN
int main(){
    
    int socket_test = connect_communication(2081);
    uint32_t a = 7;
    send(socket_test, &a, sizeof(uint32_t), 0);
    close(socket_test);

    // chain_node popy;

    // printf("(using dummy chain nodes to test communication)\n");
    // popy.label = "dummy";
    // FILE * f = fopen("popy_test.data", "rb");
    // fseek(f, 0L, SEEK_END);
    // long numbytes = ftell(f);
    // fseek(f, 0L, SEEK_SET);	
    // uint8_t * data = (uint8_t*)calloc(numbytes, sizeof(uint8_t));	
    // fread(data, sizeof(uint8_t), numbytes, f); fclose(f);
    // popy.foundmap = binary_to_structure(data);
    // free(data);

    // double scores[3] = {1.34, 99.56, 78.145};

    // int judge = connect_communication(2081);
    // send_report(judge, &popy, scores);
    // printf("[MAIN] DONE\n");

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