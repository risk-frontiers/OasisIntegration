import csv
import struct
import sqlite3

"""
Implementation of ktool item/coverage bin conversion tool including
complex item data serialized with msgpack.
"""

SUPPORTED_GUL_STREAMS = {"item": (1, 1), "coverage": (1, 2), "loss": (2, 1)}


def gulcalc_sqlite_fp_to_bin(db_fp, output, num_sample, stream_id=(1, 1)):
    """This transforms a sqlite result table (rf format) into oasis loss binary stream

    :param db_fp: path to the sqlite database
    :param output: output stream where results will be written to
    :param num_sample: number of samples in result
    :param stream_id: item, coverage or loss stream id
    :return: OASIS compliant item or coverage binary stream
    """
    con = sqlite3.connect(db_fp)
    gulcalc_sqlite_to_bin(con, output, num_sample, stream_id)
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


def gulcalc_sqlite_to_bin(con, output, num_sample, stream_id=(1,1)):
    """This transforms a sqlite result table (rf format) into oasis loss binary stream

    :param con: open sqlite database connection
    :param output: output stream where results will be written to
    :param num_sample: number of samples in result
    :param stream_id: item, coverage or loss stream id
    :return: OASIS compliant item or coverage binary stream
    """
    cur = con.cursor()
    cur.execute("SELECT event_id, reg_id, sample_id, groundup "
                ", case when sample_id = -2 then 0 else sample_id end sub_order "
                "from u_lossoasis_r254 "
                "order by event_id, reg_id, sub_order;")

    if stream_id not in list(SUPPORTED_GUL_STREAMS.values()) or not num_sample > 0:
        return
    stream_id = (stream_id[0] << 24) | stream_id[1]
    output.write(struct.pack('i', stream_id))
    output.write(struct.pack('i', num_sample))

    last_key = (0, 0)
    for row in cursor_iterator(cur):
        current_key = (int(row[0]), int(row[1]))
        if not last_key == current_key:
            if not last_key == (0, 0):
                output.write(struct.pack('Q', 0))  # sidx/loss 0/0 as separator
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
