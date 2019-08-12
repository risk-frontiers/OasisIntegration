import csv
import struct
import sqlite3

"""
Implementation of ktool item/coverage bin conversion tool including
complex item data serialized with msgpack.
"""


def gulcalc_csv_to_bin(source, output, num_sample, stream_type=1):
    """This transforms a gulcalc csv file stream into binary stream
    ****DEPRECATED****

    :param source: input stream
    :param output: output stream
    :param num_sample: number of samples
    :param stream_type: 1 for item option, 2 for coverage option
    :return: OASIS compliant item or coverage binary stream
    """
    if stream_type not in (1, 2) or not num_sample > 0:
        return
    header = (1, 0, stream_type)
    s = struct.Struct('>BbH')
    output.write(s.pack(*header))
    sample = (num_sample,)
    s = struct.Struct('I')
    output.write(s.pack(*sample))

    loc_col = "item_id"
    if stream_type == 2:
        loc_col = "coverage_id"
    last_key = (0, 0)
    for row in csv.DictReader(iter(source.readline, '')):
        current_key = (int(row["event_id"]), int(row[loc_col]))
        if not last_key == current_key:
            if not last_key == (0, 0):
                s = struct.Struct('Q')  # separator
                output.write(s.pack(*(0,)))
            s = struct.Struct('II')
            output.write(s.pack(*current_key))
            last_key = (int(row["event_id"]), int(row[loc_col]))
        losses = (int(row["sidx"]), float(row["loss"]))
        s = struct.Struct('if')
        output.write(s.pack(*losses))


def gulcalc_sqlite_fp_to_bin(db_fp, output, num_sample, stream_type=1):
    """This transforms a sqlite result table (rf format) into oasis loss binary stream

    :param db_fp: path to the sqlite database
    :param output: output stream where results will be written to
    :param num_sample: number of samples in result
    :param stream_type: item or coverage stream type
    :return: OASIS compliant item or coverage binary stream
    """
    con = sqlite3.connect(db_fp)
    gulcalc_sqlite_to_bin(con, output, num_sample, stream_type)
    con.close()


def cursor_iterator(cursor, batchsize=100000):
    """An iterator that uses fetchmany to keep memory usage down

    :param cursor: a sqlite db cursor
    :param batchsize: size of the batch to be fetched
    :return: a generator constructed from fetchmany
    """
    while True:
        results = cursor.fetchmany(batchsize)
        if not results:
            break
        for result in results:
            yield result


def gulcalc_sqlite_to_bin(con, output, num_sample, stream_type=1):
    """This transforms a sqlite result table (rf format) into oasis loss binary stream

    :param con: open sqlite database connection
    :param output: output stream where results will be written to
    :param num_sample: number of samples in result
    :param stream_type: item or coverage stream type
    :return: OASIS compliant item or coverage binary stream
    """
    cur = con.cursor()
    cur.execute("SELECT event_id, reg_id, sample_id, groundup "
                ", case when sample_id = -2 then 0 else sample_id end sub_order "
                "from u_lossoasis_r254 "
                "order by event_id, reg_id, sub_order;")

    if stream_type not in (1, 2) or not num_sample > 0:
        return
    stream_id = (1 << 24) | stream_type
    output.write(struct.pack('i', stream_id))
    output.write(struct.pack('i', num_sample))

    last_key = (0, 0)
    for row in cursor_iterator(cur):
        current_key = (int(row[0]), int(row[1]))
        if not last_key == current_key:
            if not last_key == (0, 0):
                output.write(struct.pack('Q', 0))  # separator
            output.write(struct.pack('II', current_key[0], current_key[1]))
            last_key = (int(row[0]), int(row[1]))
        output.write(struct.pack('if', int(row[2]), float(row[3])))


if __name__ == "__main__":
    import sys
    if len(sys.argv) <= 1:
        print("missing sqlite database argument")
    else:
        PY3K = sys.version_info >= (3, 0)
        if PY3K:
            output_stdout = sys.stdout.buffer
        else:
            # Python 2 on Windows opens sys.stdin in text mode, and
            # binary data that read from it becomes corrupted on \r\n
            if sys.platform == "win32":
                # set sys.stdin to binary mode
                import msvcrt
                import os
                msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
            output_stdout = sys.stdout
        samples = 1
        if len(sys.argv) > 2:
            samples = int(sys.argv[2])
        stream = 2
        if len(sys.argv) > 3:
            stream = int(sys.argv[3])
        gulcalc_sqlite_fp_to_bin(sys.argv[1], output_stdout, samples, stream)
