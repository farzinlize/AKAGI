from FoundMap import FoundMap, ReadOnlyMap
from misc import ExtraPosition, bytes_to_int, int_to_bytes
from constants import BINARY_DATA, DATABASE_ADDRESS, DATABASE_LOG, DATABASE_NAME, DEL, END, INT_SIZE, MONGO_ID, STR
from io import BytesIO
from pymongo.mongo_client import MongoClient
from bson.objectid import ObjectId


def get_client():return MongoClient(DATABASE_ADDRESS)
    

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


def read_list(address:bytes, collection_name, client:MongoClient=None):

    if not client:client = get_client()
    
    collection = client[DATABASE_NAME][collection_name]
    item = collection.find_one({MONGO_ID:ObjectId(address)})

    if not item:
        with open(DATABASE_LOG, 'a+') as log:log.write(f'[MONGO][READ] not found! address: {address}')
        return None
    
    reader = BytesIO(item[BINARY_DATA])

    return binary_to_list(reader)


def clear_list(address:bytes, collection_name, client:MongoClient=None):

    if not client:client = get_client()

    collection = client[DATABASE_NAME][collection_name]
    deleted = collection.delete_one({MONGO_ID:ObjectId(address)}).deleted_count

    if not deleted:
        with open(DATABASE_LOG, 'a+') as log:log.write(f'[MONGO][CLEAR] not found! address: {address}')


def protect_list(address:bytes, collection_name, client:MongoClient=None):
    
    if not client:client = get_client()


def initial_readonlymaps(foundmaps:list[FoundMap], collection_name, client:MongoClient=None)->list[ReadOnlyMap]:
    
    if not client:client = get_client()
    
    order = []      # list of dictionaries for mongod process 
    objects = []    # return result objects of ReadOnlyMap
    collection = client[DATABASE_NAME][collection_name]
    
    for foundmap in foundmaps:
        readonlymap = ReadOnlyMap(collection_name, ObjectId())
        order.append({MONGO_ID:readonlymap.address, BINARY_DATA:list_to_binary(foundmap.get_list())})
        objects.append(readonlymap)

    collection.insert_many(order, ordered=False)
    return objects

