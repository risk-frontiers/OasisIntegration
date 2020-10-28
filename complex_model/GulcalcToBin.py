import struct
import sqlite3
import os
import logging
import complex_model.DefaultSettings as DS
import time

"""
Implementation of ktool item/coverage/loss bin stream conversion tool including
complex item data serialized with msgpack.
"""

_DEBUG = DS.RF_DEBUG_MODE
if "RF_DEBUG_MODE" in os.environ:
    if isinstance(os.environ["RF_DEBUG_MODE"], str) and os.environ["RF_DEBUG_MODE"].lower() == "true":
        _DEBUG = True
logging.basicConfig(level=logging.DEBUG if _DEBUG else logging.INFO,
                    filename=DS.WORKER_LOG_FILE,
                    format='[%(asctime)s: %(levelname)s/%(filename)s] %(message)s')

SUPPORTED_GUL_STREAMS = {"item": (1, 1), "coverage": (1, 2), "loss": (2, 1)}
DEFAULT_GUL_STREAM = SUPPORTED_GUL_STREAMS["loss"]


def gulcalc_sqlite_fp_to_bin(working_dir, db_fp, output, num_sample, stream_id=DEFAULT_GUL_STREAM,
                             oasis_event_batch=None):
    """This transforms a sqlite result table (rf format) into oasis loss binary stream

    :param working_dir: working directory
    :param db_fp: path to the sqlite database
    :param output: output stream where results will be written to
    :param num_sample: number of samples in result
    :param stream_id: item, coverage or loss stream id
    :param oasis_event_batch: event batch id attached to this process
    :return: OASIS compliant item or coverage binary stream
    """
    start = time.time()
    logging.info("STARTED: Transforming sqlite losses into gulcalc item/loss binary stream for oasis_event_batch "
                 + str(oasis_event_batch))
    gulcalc_create_header(output, num_sample, stream_id)

    con = sqlite3.connect(db_fp)
    cur = con.cursor()
    cur.execute("SELECT count(*) FROM event_batches")
    num_partial = cur.fetchone()[0]
    cur.execute("SELECT batch_id FROM event_batches ORDER BY batch_id")
    add_first_separator = False
    rc = 0
    for batch_id in cur.fetchall():
        logging.info("RUNNING: Streaming partial loss " + str(1 + int(batch_id[0])) + "/" + str(num_partial)
                     + " for oasis_event_batch " + str(oasis_event_batch))
        batch_res_fp = os.path.join(working_dir, "oasis_loss_{0}.db".format(batch_id[0]))
        batch_res_con = sqlite3.connect(batch_res_fp)
        rc = rc + gulcalc_sqlite_to_bin(batch_res_con, output, add_first_separator)
        add_first_separator = True
    con.close()

    hours, rem = divmod(time.time() - start, 3600)
    minutes, seconds = divmod(rem, 60)
    exec_time = "{:0>2}:{:0>2}:{:05.2f}".format(int(hours), int(minutes), seconds)
    logging.info("COMPLETED: Successfully generated losses as gulcalc binary stream for event batch "
                 + str(oasis_event_batch) + ": " + str(rc) + " rows were streamed in " + exec_time)


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


def gulcalc_create_header(output, num_sample, stream_id=DEFAULT_GUL_STREAM):
    if stream_id not in list(SUPPORTED_GUL_STREAMS.values()) or not num_sample > 0:
        return
    stream_id = (stream_id[0] << 24) | stream_id[1]
    output.write(struct.pack('i', stream_id))
    output.write(struct.pack('i', num_sample))


def gulcalc_sqlite_to_bin(con, output, add_first_separator):
    """This transforms a sqlite result table (rf format) into oasis loss binary stream

    :param con: sqlite connection to result batch
    :param output: output stream where results will be written to
    :param add_first_separator: boolean flag to add separator 0/0 for second, third, ... batches
    :return: OASIS compliant item or coverage binary stream
    """
    cur = con.cursor()
    cur.execute("SELECT event_id, loc_id, sample_id, loss FROM oasis_loss ORDER BY event_id")

    last_key = (0, 0)
    rc = 0
    for row in cursor_iterator(cur):
        current_key = (int(row[0]), int(row[1]))
        if not last_key == current_key:
            if not last_key == (0, 0) or add_first_separator:
                output.write(struct.pack('Q', 0))  # sidx/loss 0/0 as separator
            output.write(struct.pack('II', current_key[0], current_key[1]))
            last_key = (int(row[0]), int(row[1]))
        output.write(struct.pack('if', int(row[2]), float(row[3])))
        rc = rc + 1
    return rc


if __name__ == "__main__":
    import sys
    if len(sys.argv) <= 1:
        print("missing working directory")
    else:
        working_directory = sys.argv[1]
        debug_output = sys.stdout.buffer
        samples = 1
        if len(sys.argv) > 2:
            debug_output = open(sys.argv[2], 'w+b')
        if len(sys.argv) > 3:
            samples = int(sys.argv[2])
        stream = (2, 1)
        if len(sys.argv) > 4:
            stream = int(sys.argv[3])

        db_path = os.path.join(working_directory, 'riskfrontiersdbAUS_v2_6.db')
        gulcalc_sqlite_fp_to_bin(working_directory, db_path, debug_output, samples, stream)
