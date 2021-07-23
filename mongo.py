from misc import ExtraPosition, bytes_to_int, int_to_bytes
from constants import BINARY_DATA, CLEAR, DATABASE_ADDRESS, DATABASE_LOG, DATABASE_NAME, DEL, END, FIND_ONE, INSERT_MANY, INT_SIZE, MONGO_ID, MONGO_SECRET_ADDRESS, MONGO_USERNAME, STR
from io import BytesIO
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import ServerSelectionTimeoutError
from pymongo.results import DeleteResult


def mongo_secret_password():
    with open(MONGO_SECRET_ADDRESS, 'r') as secret:
        pwd = secret.read().split(',')[1]
        return pwd[pwd.find('"')+1:pwd.rfind('"')]


def get_client(connect=None):
    return MongoClient(DATABASE_ADDRESS%(MONGO_USERNAME, mongo_secret_password()), connect=connect)
    

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


def safe_operation(collection:Collection, command, order):
    try:
        if   command == INSERT_MANY :collection.insert_many(order, ordered=False)
        elif command == FIND_ONE    :return collection.find_one(order)
        elif command == CLEAR       :return collection.delete_one(order)
    except ServerSelectionTimeoutError as server_down:
        with open(DATABASE_LOG, 'a') as log:log.write(f'[MONGO] server down\n{server_down}\n')
        return server_down
    except Exception as any_error:
        with open(DATABASE_LOG, 'a') as log:log.write(f'[MONGO] database error\n{any_error, type(any_error)}\n')
        return any_error


def read_list(address:bytes, collection_name, client:MongoClient=None):

    if not client:client = get_client()
    
    collection = client[DATABASE_NAME][collection_name]
    item_or_error = safe_operation(collection, FIND_ONE, {MONGO_ID:address})

    if not item_or_error:
        with open(DATABASE_LOG, 'a') as log:log.write(f'[MONGO][READ] not found! address: {address}\n')
        return None
    elif not isinstance(item_or_error, dict):
        with open(DATABASE_LOG, 'a') as log:log.write(f'[MONGO][READ] error: {item_or_error}\n')
        return item_or_error

    return binary_to_list(BytesIO(item_or_error[BINARY_DATA]))


def clear_list(address:bytes, collection_name, client:MongoClient=None):

    if not client:client = get_client()

    collection = client[DATABASE_NAME][collection_name]
    result = safe_operation(collection, CLEAR, {MONGO_ID:address})

    if not isinstance(result, DeleteResult):
        with open(DATABASE_LOG, 'a') as log:log.write(f'[MONGO][CLEAR] error: {result}\n')
    elif not result.deleted_count:
        with open(DATABASE_LOG, 'a') as log:log.write(f'[MONGO][CLEAR] not found! address: {address}\n')


# def protect_list(address:bytes, collection_name, client:MongoClient=None):
    
#     if not client:client = get_client()
#     raise NotImplementedError


if __name__ == '__main__':
    client = get_client()