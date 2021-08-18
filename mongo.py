import os, json
from io import BytesIO
from misc import ExtraPosition, bytes_to_int, int_to_bytes, log_it, make_location
from constants import AUTORECONNECT_TRY, BANKBASE_ADDRESS, BINARY_DATA, CLEAR, COLLECTION, DATABASE_ADDRESS, DATABASE_LOG, DATABASE_NAME, DEL, DROP, END, FIND_ONE, INSERT_MANY, INSERT_ONE, INT_SIZE, LABEL, MONGOD_RUN_SERVER_COMMAND_LINUX, MONGOD_SHUTDOWN_COMMAND, MONGO_ID, MONGO_PORT, MONGO_SECRET_ADDRESS, MONGO_USERNAME, POP, RAW_MONGOD_SERVER_COMMAND_LINUX, STR, UPDATE
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import AutoReconnect, ServerSelectionTimeoutError
from pymongo.results import DeleteResult


def mongo_secret_password():
    with open(MONGO_SECRET_ADDRESS, 'r') as secret:config = json.load(secret)
    return config['pwd']


def get_client(connect=None):
    return MongoClient(DATABASE_ADDRESS%(MONGO_USERNAME, mongo_secret_password()), connect=connect)


def get_bank_client(bank_port, connect=None):
    return MongoClient(BANKBASE_ADDRESS%(MONGO_USERNAME, mongo_secret_password(), bank_port), connect=connect)


def initial_akagi_database(name, dbpath, port=MONGO_PORT, serve=False):
    
    # run mongod server without --auth and make dbpath directory
    make_location(dbpath)
    stream = os.popen(RAW_MONGOD_SERVER_COMMAND_LINUX%(dbpath, name, '', port))
    output = stream.read()
    with open(DATABASE_LOG, 'a') as log:log.write('[MONGO][INITIAL] running server via python:\n' + output)
    if output.split('\n')[2].startswith('ERROR'):raise Exception(f'cant run mongo server check {DATABASE_LOG}')

    # read configuration for user akagi
    with open(MONGO_SECRET_ADDRESS,'r') as secret:config = json.load(secret)

    # create user using super client
    super_client = MongoClient(f'localhost:{port}')
    answer = super_client[DATABASE_NAME].command('createUser', config['user'], pwd=config['pwd'], roles=config['roles'])
    if not answer['ok']:raise Exception(f'cant create user -> {answer}')

    # shutting down super server
    os.system(MONGOD_SHUTDOWN_COMMAND%dbpath)

    # open again with --auth flag
    if serve:
        stream = os.popen(RAW_MONGOD_SERVER_COMMAND_LINUX%(dbpath, name, '--auth', port))
        output = stream.read()
        with open(DATABASE_LOG, 'a') as log:log.write('[MONGO][SERVE] running server via python:\n' + output)
        if output.split('\n')[2].startswith('ERROR'):raise Exception(f'cant run mongo server check {DATABASE_LOG}')


def serve_database_server(name, dbpath, port):
    stream = os.popen(RAW_MONGOD_SERVER_COMMAND_LINUX%(dbpath, name, '--auth', port))
    output = stream.read()
    with open(DATABASE_LOG, 'a') as log:log.write('[MONGO][INITIAL] running server via python:\n' + output)
    if output.split('\n')[2].startswith('ERROR'):raise Exception(f'cant run mongo server check {DATABASE_LOG}')


# [WARNING] only works for linux (because of --fork option)
# deprecated - for older versions of multi and it use predefined command
def run_mongod_server():
    stream = os.popen(MONGOD_RUN_SERVER_COMMAND_LINUX)
    output = stream.read()
    with open(DATABASE_LOG, 'a') as log:log.write('[MONGO][SERVER] running server via python:\n' + output)
    if output.split('\n')[2].startswith('ERROR'):raise Exception(f'cant run mongo server check {DATABASE_LOG}')


def binary_to_list(reader:BytesIO):

    sequences = []
    positions_vector = []

    # check header byte signature
    assert reader.read(1) == STR

    # reading sequence vector
    for _ in range(bytes_to_int(reader.read(INT_SIZE))):
        sequences += [bytes_to_int(reader.read(INT_SIZE))]
                    
    assert reader.read(1) == DEL

    # reading 2D-position vector
    for _ in range(len(sequences)):
        positions = []
        for _ in range(bytes_to_int(reader.read(INT_SIZE))):
            position = bytes_to_int(reader.read(INT_SIZE))
            size = bytes_to_int(reader.read(INT_SIZE))
            positions += [ExtraPosition(position, size)]
        positions_vector += [positions[:]]

        assert reader.read(1) == DEL
                
    assert reader.read(1) == END

    return [sequences, positions_vector]


def list_to_binary(found_list):

    writer = BytesIO()
    sequences = found_list[0]
    positions_vector = found_list[1]

    # header byte signature
    writer.write(STR)

    # writing sequence vector
    writer.write(int_to_bytes(len(sequences)))
    for seq_id in sequences:
        writer.write(int_to_bytes(seq_id))
                
    writer.write(DEL)

    # writing 2D-position vector
    for index in range(len(sequences)):
        writer.write(int_to_bytes(len(positions_vector[index])))
        position: ExtraPosition
        for position in positions_vector[index]:
            writer.write(int_to_bytes(position.start_position))
            writer.write(int_to_bytes(position.size))
                
        writer.write(DEL)

    writer.write(END)

    return writer.getvalue()


def safe_operation(collection:Collection, command, order=None, order_filter=None, try_tokens=AUTORECONNECT_TRY):
    try:
        if   command == INSERT_MANY :collection.insert_many(order, ordered=False)
        elif command == POP         :return collection.find_one_and_delete({})
        elif command == FIND_ONE    :return collection.find_one(order)
        elif command == COLLECTION  :return [item for item in collection.find()]
        elif command == CLEAR       :return collection.delete_one(order)
        elif command == DROP        :collection.drop()
        elif command == INSERT_ONE  :collection.insert_one(order)
        elif command == UPDATE      :collection.find_one_and_update(filter=order_filter, update=order, upsert=True)
    except AutoReconnect as reconnect_error:
        log_it(DATABASE_LOG, f'[MONGO][SAFE] AutoReconnect problem - try again? ({try_tokens}) - {reconnect_error}')
        if try_tokens:return safe_operation(collection, command, order, order_filter, try_tokens-1)
        else:log_it(DATABASE_LOG, f'[MONGO][SAFE] no more trying return error');return reconnect_error
    except ServerSelectionTimeoutError as server_down:
        log_it(DATABASE_LOG, f'[MONGO] server down\n{server_down}');return server_down
    except Exception as any_error:
        log_it(DATABASE_LOG, f'[MONGO] database error\n{any_error, type(any_error)}');return any_error


def read_list(address:bytes, collection_name, client:MongoClient=None):

    if not client:client = get_client();should_close = True
    else                               :should_close = False
    
    collection = client[DATABASE_NAME][collection_name]
    item_or_error = safe_operation(collection, FIND_ONE, {MONGO_ID:address})
    if should_close:client.close()

    if not item_or_error:
        with open(DATABASE_LOG, 'a') as log:log.write(f'[MONGO][READ] not found! address: {address}\n')
        return None
    elif not isinstance(item_or_error, dict):
        with open(DATABASE_LOG, 'a') as log:log.write(f'[MONGO][READ] error: {item_or_error}\n')
        return item_or_error

    return binary_to_list(BytesIO(item_or_error[BINARY_DATA]))


def clear_list(address:bytes, collection_name, client:MongoClient=None):

    if not client:client = get_client();should_close = True
    else                               :should_close = False

    collection = client[DATABASE_NAME][collection_name]
    result = safe_operation(collection, CLEAR, {MONGO_ID:address})
    if should_close:client.close()

    if not isinstance(result, DeleteResult):
        with open(DATABASE_LOG, 'a') as log:log.write(f'[MONGO][CLEAR] error: {result}\n')
    elif not result.deleted_count:
        with open(DATABASE_LOG, 'a') as log:log.write(f'[MONGO][CLEAR] not found! address: {address}\n')


if __name__ == '__main__':
    run_mongod_server()
    client = get_client()