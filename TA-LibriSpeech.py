# -*- coding: utf-8 -*-

import os,sys
import argparse
import sqlite3,math
from shutil import copyfile
from collections import OrderedDict
import re

class TA_LibriSpeech:

    parser_message = "Script developed to interact with the database" \
                     "to extract information easily:" \
    "Example use: python3 TA-LibriSpeech.py train ./folder_output_train --size 1200 --verbose" \
                     "sort CNG --maxSegDuration 35.0 --minSegDuration 3.0 --extract "
    db = "./TA-LibriSpeechCorpus.db"

    def __init__(self):
        self.evaluated_list = self.getEvaluated()
        self.train_dataset = []

    def getEvaluated(self):
        """
        Query the database to get the audio_filename (unique identifier) for 200 sentences
        that are evaluated by us
        :return: List of ['audio_filenames'] that are evaluated
        """
        chapters = [51758,123443,127083,163375]
        db_connection = sqlite3.connect(TA_LibriSpeech.db)
        books = []
        for chapter in chapters:
            cursor = db_connection.execute("SELECT audio_filename FROM alignments "
                    "WHERE chapter_id = " + str(chapter) + " LIMIT 50")

            query_results = cursor.fetchall()
            for result in query_results:

                books.append(result[0])
            cursor.close()

        return books

def write_data(outputFolder,data):
    args.output = outputFolder
    # Open folder
    if not os.path.exists(args.output):
        os.mkdir(args.output)

    # if --extract copyfile and write everything to output folder
    # else sys.stdout filepaths


    filepath_fh = open(args.output + "/filepaths.txt", "w", encoding="utf8")
    metadata_fh = open(args.output + "/metadata.meta", "w", encoding="utf8")
    transcription_fh = open(args.output + "/transcription.txt", "w", encoding="utf8")
    translation_fh = open(args.output + "/translation.txt", "w", encoding="utf8")

    for k, v in data.items():
        filepath_fh.write('{}/{}/{}/{}\n'.format('./audio_files',
                                                 str(v['book_id']), str(v['chapter_id']), k + ".wav"))
        # filepath_fh.write("./audio_files/"+str(v['book_id'])+"/"+str(v['chapter_id'])+"/"+k+".wav\n")
        if args.extract:
            # Copy files
            if args.verbose:
                print("Copying file\t" + k + ".wav to destination " + args.output + "/{}".format(k) + ".wav")

            copyfile('{}/{}/{}/{}'.format('./audio_files',
                                          str(v['book_id']), str(v['chapter_id']), k + ".wav"),
                     args.output + "/{}".format(k) + ".wav")

        # Write metadata
        metadata_fh.write("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t\n".format(k, str(v['book_id']), str(v['chapter_id']),
                                                                      str(v['sentNo']), v['transcription'],
                                                                      v['translation'],
                                                                      str(v['score']), str(v['segment_duration'])))
        transcription_fh.write("{}\n".format(v['transcription']))
        translation_fh.write("{}\n".format(v['translation']))

    filepath_fh.close()
    translation_fh.close()
    transcription_fh.close()

if __name__ == '__main__':

    database = TA_LibriSpeech()


    parser = argparse.ArgumentParser(description=TA_LibriSpeech.parser_message,
                            formatter_class=argparse.RawDescriptionHelpFormatter)


    #Required arguments
    parser.add_argument('action', help='1)train 2)dev 3)test')
    parser.add_argument('output', help='Destination to output folder')


    parser.add_argument('--size', help="Size of the corpus to be extracted: (minutes)"
                                     "Default: 100 hours = 6000 minutes  ", default=6000)

    ## Arguments for dev/test

    parser.add_argument("--listTrain", help="Path to the filepaths.txt that contains the filepaths used in training dataset"
                                            "in order to exclude them in dev and test sets")
    parser.add_argument("--useEvaluated", help="For test/dev datasets, this clause gives privilege to "
                                               "200 sentences that are manually evaluated", default = True)
    #Optional arguments
    parser.add_argument('--sort', help='Sorts the corpus using scores before extracting'
                        'None: Do not sort'
                        'hunAlign: Using hunAlign scores'
                        'CNG: Using CL-CNG & CL-CTS scores ', default='None',
                        choices=('None', 'hunAlign', 'CNG', 'LM'))

    parser.add_argument('-v', '--verbose', help='verbose mode',
                        action='store_true', default= True)



    parser.add_argument("--maxSegDuration",help="Maximum length of an audio file (segment) in seconds"
                                                "Default: 30 seconds", default=30.0, type=float)
    parser.add_argument("--minSegDuration",help="Minimum length of an audio file", default = 0.0, type=float)
    parser.add_argument("--extract", help="Copies the sound files to output folder instead of"
                                          "copying only the audio filenames along with transcription and translation files",
                        action="store_true", default = False)

    args = parser.parse_args()
    sorttype = args.sort
    if args.sort == "None":
        args.sort = "ORDER BY book_id"
    elif args.sort == "hunAlign":
        args.sort = "ORDER BY alignment_score DESC"
    elif args.sort == "CNG":
        args.sort = "ORDER BY cng_score DESC"
    elif args.sort == "LM":
        args.sort = "ORDER BY lm_score"

    dev_test = False
    if args.listTrain != "" and (args.action == "dev" or args.action == "test"):
        dev_test =True
        with open(args.listTrain,"r",encoding="utf8") as fh:
            train_files = fh.readlines()

        for train_file in train_files:
            searchObject = re.search(r"(\d+-\d+-\d+)",train_file.strip(),re.I)
            identifier = searchObject.group(1)
            database.train_dataset.append(identifier)

    db_connection = sqlite3.connect(TA_LibriSpeech.db)

    maxLimit = args.size
    if maxLimit != "max":
        maxLimit = float(maxLimit) * 60  # Seconds
    else:
        maxLimit = math.inf

    if dev_test and args.useEvaluated:

        time_counter = 0.0
        data = OrderedDict()
        for id in database.evaluated_list:

            query = "SELECT * FROM alignments WHERE audio_filename = \"" + id + "\""

            cursor = db_connection.execute(query)
            row = cursor.fetchone()
            cursor.close()

            #Get the human evaluation score (AVG) and append
            query = "SELECT AVG(alignment_eval) FROM alignments_evaluations WHERE chapter_id = 123443 AND sent_id = 0"
            row_evaluation = db_connection.execute(query).fetchone()
            if row_evaluation[0] >= 3.0:


                if time_counter <= maxLimit:
                    print(row_evaluation)
                    sys.exit("STOP ")
                    # Query for segment duration
                    (audio_filename,
                     book_id, chapter_id,
                     sentno, transcrpt, transl, exclusion) = row[1], row[2], row[3], row[4], row[5], row[7], row[11]

                    cursor = db_connection.execute(
                        "SELECT * FROM alignments_audio WHERE audio_filename = \"" + audio_filename + "\"")
                    audio_row = cursor.fetchone()
                    segment_duration = audio_row[-1]
                    cursor.close()


                    if segment_duration >= args.minSegDuration \
                            and segment_duration <= args.maxSegDuration:

                        time_counter += segment_duration
                        if args.verbose:
                            print(row)
                        # Alignment scores
                        score = row_evaluation[0]

                        bookItem = {}
                        bookItem['book_id'] = book_id
                        bookItem['chapter_id'] = chapter_id
                        bookItem['segment_duration'] = segment_duration
                        bookItem['score'] = score
                        bookItem['sentNo'] = sentno
                        bookItem['transcription'] = transcrpt
                        bookItem['translation'] = transl
                        data[audio_filename] = bookItem

        #Do not continue with the rest of the pipeline if its dev/test
        write_data(args.output,data)
        sys.exit("")

    # Query for DB
    query = " SELECT * FROM alignments " \
            "JOIN (alignments_excluded JOIN alignments_scores " \
            "USING(audio_filename)) USING (audio_filename) WHERE excluded != \"True\"  " + args.sort

    cursor = db_connection.execute(query)


    if args.verbose:
        print("Starting query")
    query_results = cursor.fetchall()

    time_counter = 0.0
    data = OrderedDict()
    for row in query_results:

        if time_counter <= maxLimit:
            (audio_filename,
             book_id,chapter_id,
             sentno,transcrpt,transl,exclusion) = row[1],row[2],row[3],row[4],row[5],row[7],row[11]
            # print(audio_filename,book_id,chapter_id,sentno,transcrpt,transl,exclusion)

            #Keep manually evaluted audio files to test & dev
            if args.action == "train" and audio_filename in database.evaluated_list:
                continue

            #Alignment scores

            scores = {}
            scores['CNG'] = row[-2]
            scores['hunAlign'] = row[8]
            scores['None'] = row[-2]
            scores['LM'] = row[-1]
            score = scores[sorttype]
            #Query for segment duration
            cursor = db_connection.execute("SELECT * FROM alignments_audio WHERE audio_filename = \"" + audio_filename+"\"")
            audio_row = cursor.fetchone()
            segment_duration = audio_row[-1]
            cursor.close()

            if segment_duration >= args.minSegDuration\
                    and segment_duration <= args.maxSegDuration:
                time_counter += segment_duration
                if args.verbose:
                    print(row)
                bookItem = {}
                bookItem['book_id'] = book_id
                bookItem['chapter_id'] = chapter_id
                bookItem['segment_duration'] = segment_duration
                bookItem['score'] = score
                bookItem['sentNo'] = sentno
                bookItem['transcription'] = transcrpt
                bookItem['translation'] = transl
                data[audio_filename] = bookItem

    cursor.close()
    write_data(args.output,data)


    """
    SELECT * FROM alignments JOIN (alignments_excluded JOIN alignments_scores USING(audio_filename) ) USING ( audio_filename ) WHERE excluded != "True"  ORDER BY alignment_score DESC 
    """
