from io import BufferedReader, BufferedWriter, SEEK_CUR
from misc import ExtraPosition, bytes_to_int, int_to_bytes
import os
from constants import APPDATA_PATH, DATABASEFILE_TAG, DATABASE_LOG, DB_LOCATION, DB_PRT, DB_TAG, DEL, END, INT_SIZE, PRT, STR, TAG_LENGTH


def initial_foundmap(address, initial_list):
    tag = address[-TAG_LENGTH:]
    database_name = address[:-TAG_LENGTH] + DATABASEFILE_TAG

    # read database content
    if os.path.isfile(database_name):
        with open(database_name, 'rb') as base:
            table = read_table(base)
            content = base.read()
    else:
        table = []
        content = b''
    
    # check for coalition
    for row in table:
        if row[DB_TAG] == tag:
            with open(DATABASE_LOG, 'a+') as log:log.write('COALITION OCCURRED')
            return False # not placed

    # update table
    table.append((tag, len(content), False))

    with open(database_name, 'wb') as version:
        write_table(table, version)
        version.write(content)

        # list to byte
        version.write(STR)
        version.write(int_to_bytes(len(initial_list[0])))
        for seq_id in initial_list[0]:
            version.write(int_to_bytes(seq_id))
        version.write(DEL)

        for index in range(len(initial_list[0])):
            version.write(int_to_bytes(len(initial_list[1][index])))
            position: ExtraPosition
            for position in initial_list[1][index]:
                version.write(int_to_bytes(position.start_position))
                version.write(int_to_bytes(position.size))
            version.write(DEL)
        version.write(END)
    
    return True


def read_list(address)->list[list]:
    tag = address[-TAG_LENGTH:]
    database_name = address[:-TAG_LENGTH] + DATABASEFILE_TAG

    with open(database_name, 'rb') as base:
        table = read_table(base)

        read_location = -1
        for row in table:
            if row[DB_TAG] == tag:
                read_location = row[DB_LOCATION]
        
        # check for existence XD
        if read_location == -1:
            with open(DATABASE_LOG, 'a+') as log:log.write('tag not found - READ FAIL')
            return

        # goto data on file
        base.read(read_location)

        # byte to list
        assert base.read(1) == STR

        sequences = []
        for _ in range(bytes_to_int(base.read(INT_SIZE))):
            sequences += [bytes_to_int(base.read(INT_SIZE))]
        assert base.read(1) == DEL

        position_vector = []
        for _ in range(len(sequences)):
            positions = []
            for _ in range(bytes_to_int(base.read(INT_SIZE))):
                position = bytes_to_int(base.read(INT_SIZE))
                size = bytes_to_int(base.read(INT_SIZE))
                positions += [ExtraPosition(position, size)]
            position_vector += [positions[:]]
        
            assert base.read(1) == DEL
        assert base.read(1) == END
    
    return [sequences, position_vector]


def clear_list(address):
    tag = address[-TAG_LENGTH:]
    database_name = address[:-TAG_LENGTH] + DATABASEFILE_TAG

    # read database content
    with open(database_name, 'rb') as base:
        table = read_table(base)
        content = base.read()
    
    hit_row = None
    for index, row in enumerate(table):
        if row[DB_TAG] == tag:
            hit_row = row
            has_more = (index != len(table)-1)

    if hit_row == -1:
        with open(DATABASE_LOG, 'a+') as log:log.write('tag not found - CLEAR FAIL')
        return

    table = table[:index] + table[index+1:]

    with open(database_name, 'wb') as version:
        write_table(table, version)
        version.write(content[:hit_row[DB_LOCATION]])
        if has_more:version.write(content[table[index][DB_LOCATION]:])


def protect_list(address):
    tag = address[-TAG_LENGTH:]
    database_name = address[:-TAG_LENGTH] + DATABASEFILE_TAG

    # read database content and write PRT byte
    with open(database_name, 'rb+') as base:
        rows = bytes_to_int(base.read(INT_SIZE))
        for _ in range(rows):
            row_tag = str(base.read(TAG_LENGTH), encoding='ascii')
            if tag == row_tag:
                base.seek(INT_SIZE, 1)
                base.write(PRT)
                return True

    # not found!    
    with open(DATABASE_LOG, 'a+') as log:log.write('not found - [protect]')
    return False


# TODO: unfinished
def clear_disk(keep_protected=True):
    clear_size = 0
    databases = [f for f in os.listdir(APPDATA_PATH) if f.endswith(DATABASEFILE_TAG)]
    for database in databases:

        if keep_protected:
            with open(APPDATA_PATH + database, 'rb+') as base:
                table = read_table(base)
                content = base.read()
                
                after_table = []
                after_content = b''
                current_location = 0

                # read protected data
                for row_index in range(len(table)):
                    if table[row_index][DB_PRT]:
                        after_table.append((table[row_index][DB_TAG], current_location, True))
                        base.seek(table[row_index][DB_TAG], SEEK_CUR)

                        if row_index == len(table)-1:
                            after_content += base.read()
                        else:
                            data_length = table[row_index+1][DB_LOCATION] - table[row_index][DB_LOCATION]
                            data = base.read(data_length)
                            current_location += data_length
                            after_content += data

                # save protected data
                write_table(after_table, base)
                base.write(after_content)

        else:
            os.remove(os.path.join(APPDATA_PATH + database))
            


# ---------------------------------------------------- #

def read_table(buffer: BufferedReader):
    table = []
    rows = bytes_to_int(buffer.read(INT_SIZE))
    for _ in range(rows):
        tag = str(buffer.read(TAG_LENGTH), encoding='ascii')
        location = bytes_to_int(buffer.read(INT_SIZE))
        if buffer.read(1) == PRT:protected = True
        else                    :protected = False
        table.append((tag, location, protected))
    return table


def write_table(table, buffer: BufferedWriter):
    buffer.write(int_to_bytes(len(table)))
    for row in table:
        buffer.write(bytes(row[DB_TAG], encoding='ascii'))
        buffer.write(int_to_bytes(row[DB_LOCATION]))
        if row[DB_PRT]:buffer.write(PRT)
        else          :buffer.write(b'\x01')


def analyse_databases():pass


# ---------------------------------------------------- #

if __name__ == '__main__':
    pass

    
    