import os,re,sys,dataset
from string import punctuation
import subprocess
from subprocess import threading
from subprocess import check_output
from nltk.tokenize import TreebankWordTokenizer
import json
from collections import OrderedDict
import collections
import math


class post_db_op:

    #Class Variables
    bad_formatted_files =[113,33,58,73,84,98,110,135,145,155,209,244,580,599,780,883,903,944,
                 1622,1629,1727,1941,1998,2166,2569,2688,2781,2845,3797,5658,5670,
                 6593,9798,9845,20912,21686,21700,29021,35499,1937,2876,2600,28054
                     ,159,210,974]

    database_path = 'sqlite:///../../DB/csv.db'
    normalizer_path = "../../lib/mosesdecoder-master/scripts/tokenizer/normalize-punctuation.perl"

    def __init__(self,id,normalize_punct=False):
        self.db = dataset.connect(post_db_op.database_path)
        self.book_id = id

        #To normalize the punctuation
        if normalize_punct == True:
            post_db_op.bad_formatted_files.append(self.book_id)



    def getTable(self,name):
        return self.db[name]

    def query(self,request):
        return self.db.query(request)

    def clean_db(self):

        if self.book_id not in post_db_op.bad_formatted_files:
            alignements = self.getTable('alignements')
            for row in alignements:
                if row['book_id'] == self.book_id:

                    rows = ['seg_cible','seg_source']
                    for process in rows:
                        str = row[process]
                        row_key = row['id']
                        normalized_string = re.sub(r" ([" + punctuation + "])", "\\1", str, re.IGNORECASE)
                        normalized_string = re.sub(r"([.,!?;:»«])(\w)", "\\1 \\2", normalized_string, re.IGNORECASE)
                        normalized_string = re.sub(r"(\w)\)", "\\1 )", normalized_string, re.IGNORECASE)

                        punctuations = "!\"#$%&'()*+,/:;<=>?@[\]^_`{|}~"
                        normalized_string = re.sub(r"([" + punctuations + "])([" + punctuations + "])", "\\1 \\2", normalized_string, re.IGNORECASE)


                        # normalized_string = re.sub(r"(\w)\"", "\\1'", normalized_string, re.IGNORECASE)
                        # normalized_string = re.sub(r"\.(\w)", ". \\1'", normalized_string, re.IGNORECASE)
                        # normalized_string = re.sub(r",(\w)", ", \\1", normalized_string, re.IGNORECASE)
                        # normalized_string = re.sub(r"\!(\w)", "! \\1", normalized_string, re.IGNORECASE)
                        # normalized_string = re.sub(r"\?(\w)", "? \\1", normalized_string, re.IGNORECASE)


                        #print(normalized_string)


                        # Update DB
                        if process == "seg_source":
                            data = dict(id=row_key, seg_source=normalized_string)
                            alignements.update(data, ['id'])
                        elif process == "seg_cible":
                            data = dict(id=row_key, seg_cible=normalized_string)
                            alignements.update(data, ['id'])

        else:
            # Normalize punctuations and post-cleaning with regex (even if it would've been better if it was done before)
            fh_log = open("fh_log.txt", "w", encoding="utf8")
            alignements = self.getTable("alignements")

            for row in alignements:
                if row['book_id'] == self.book_id:
                    fh_temp = open("./temp.txt", "w", encoding="utf8")

                    row_key = row['id']

                    fh_temp.write(row['seg_cible'].strip())
                    fh_temp.close()


                    cmd_normalize = "perl " + post_db_op.normalizer_path + " -l fr <./temp.txt> ./temp_norm.txt"
                    cmd = Command(cmd_normalize, fh_log)

                    cmd.run(timeout=9999)

                    with open("./temp_norm.txt", "r", encoding="utf8") as fh:
                        normalized_string = fh.read()
                    print(normalized_string)

                    normalized_string = re.sub(r"^ ", "", normalized_string, re.IGNORECASE)
                    normalized_string = re.sub(r"- ?\d+ ?-", "", normalized_string, re.IGNORECASE)
                    normalized_string = re.sub(r"- ", "", normalized_string, 1)
                    normalized_string = re.sub(r" ([" + punctuation + "])", "\\1", normalized_string, re.IGNORECASE)
                    normalized_string = re.sub(r"(\w)\"", "\\1'", normalized_string, re.IGNORECASE)
                    normalized_string = re.sub(r"\.(\w)", ". \\1'", normalized_string, re.IGNORECASE)
                    normalized_string = re.sub(r",(\w)", ", \\1", normalized_string, re.IGNORECASE)
                    normalized_string = re.sub(r"\!(\w)", "! \\1", normalized_string, re.IGNORECASE)
                    normalized_string = re.sub(r"\?(\w)", "? \\1", normalized_string, re.IGNORECASE)


                    print("\t" + normalized_string + "\n")
                    # print("Length\t"+ str(len(normalized_string)))
                    print(normalized_string)
                    print(row_key)

                    # Update DB
                    data = dict(id=row_key, seg_cible=normalized_string)
                    alignements.update(data, ['id'])

    def add_time_segments(self):
        alignements = self.getTable("alignements").find(book_id=self.book_id)
        #alignements = self.query("SELECT book_id,chapter_id,audio_filename,id FROM alignements GROUP BY book_id")
        alignements_sound = self.getTable("alignements_audio")

        for row in alignements:
            #print("Searching for row ")
            print(row)

            # Command for getting the duration: soxi -D out.wav
            abs_bath_audio = "/var/www/html/Alignements/audio_files/" \
                             + str(row['book_id']) + "/" + str(row['chapter_id']) + "/" + row['audio_filename'] + ".wav"

            #print(row['audio_filename'])
            checkExists = alignements_sound.find(audio_filename=row['audio_filename'])
            db_row = ""
            db_duration = 0.0
            tab_time = self.gettime(abs_bath_audio).split(":")


            if tab_time[-2] != '0.0':
                segment_duration = float(tab_time[-2])*60 + float(tab_time[-1])

            else:
                segment_duration = float(tab_time[-1])

            for row_db in checkExists:
                db_row = row_db['audio_filename']
                db_duration = row_db['duration']

            if db_row != "":
                #print(db_row,row['audio_filename'])
                assert db_row == row['audio_filename']



                #print(tab_time, row['id'])

                #print(db_duration,str(float(tab_time[-1])))

                assert db_duration == segment_duration

                print("Already in the DB passing!")
            else:

                data = dict(audio_filename=row['audio_filename'], duration=segment_duration,book_id=self.book_id)
                print(data)
                alignements_sound.insert(data)

    def checkTimeSegments(self):
        alignements = self.getTable("alignements").find(book_id=self.book_id)
        tab_errors = []
        for row in alignements:
            #print("Searching for row ")
            #print(row)

            # Command for getting the duration: soxi -D out.wav
            abs_bath_audio = "/var/www/html/Alignements/audio_files/" \
                             + str(row['book_id']) + "/" + str(row['chapter_id']) + "/" + row['audio_filename'] + ".wav"


            try:
                tab_time = self.gettime(abs_bath_audio).split(":")
            except subprocess.CalledProcessError:
                print("Error catched!: "+str(row['chapter_id']))
                tab_errors.append([self.book_id,row['chapter_id']])

        return tab_errors

    def computeTotalSeconds(self):

        table_align_audio = self.getTable("alignements_audio")

        totalSeconds = 0.0
        for row in table_align_audio:
            totalSeconds += row['duration']
        return totalSeconds

    def mark_sents_to_exclude(self):
        alignements = self.getTable("alignements")
        tb_exclusion = self.getTable("alignements_excluded")
        tb_audio = self.getTable("alignements_audio")
        tb_alignement = alignements.find(book_id = self.book_id)
        book_exclusions = {}
        for row in tb_alignement:
            tokenizer = TreebankWordTokenizer()
            #In order to mark look at the transcription and
            #seg_source, if len() is too different it's probably wrong
            tokens_tcpt = tokenizer.tokenize(row['transcription'])
            tokens_en = tokenizer.tokenize(row['seg_source'])
            tokens_fr = tokenizer.tokenize(row['seg_cible'])

            #print(tokens_fr)

            puncts = list(punctuation)+["«","»","’"]
            tokens_fr = list(filter(lambda x: x not in puncts,tokens_fr))

            row_tb_audio = tb_audio.find_one(audio_filename = row['audio_filename'])


            if row_tb_audio['duration'] == 0.0:
                book_exclusions[row['audio_filename']] = True
            elif len(tokens_tcpt) < len(tokens_en):
                if len(tokens_tcpt) < 4 and len(tokens_fr) > 5:
                    print(row['transcription'],row['seg_cible'])
                    #Verify the duration of the sound file
                    print(row['audio_filename'])
                    book_exclusions[row['audio_filename']] = True
                else:
                    book_exclusions[row['audio_filename']] = False
            else:
                book_exclusions[row['audio_filename']] = False


            if row['seg_cible'].strip() == "NA" or row['seg_source'] == "NA":
                #print(row['transcription'], row['seg_cible'])
                book_exclusions[row['audio_filename']] = True

            #If the target alignment token count is 5 times larger than tokens
            if len(tokens_tcpt) * 5 < len(tokens_fr):
                #print(row['transcription'],"\n",row['seg_cible'])
                book_exclusions[row['audio_filename']] = True

            #If the token count of transcription is 5 times larger than target alignment
            if len(tokens_tcpt) > len(tokens_fr) *5:
                book_exclusions[row['audio_filename']] = True

            #If the segment is less than 1 second
            if len(tokens_tcpt) == 1 and row_tb_audio['duration'] < 1.0:

                book_exclusions[row['audio_filename']] = True


        return book_exclusions

    def estimate_volume(self):
        corpus_dev = ["test-other", "test-clean", "dev-other", "dev-clean"]
        corpus_clean = ["train-clean-100", "train-clean-360"]
        corpus_other = ["train-other-500"]

        tb_alignements = self.getTable("alignements")
        tb_librispeech = self.getTable("librispeech")
        tb_audio = self.getTable("alignements_audio")
        tb_exclusion = self.getTable("alignements_excluded")

        """Theoric approximation of volume"""
        results = self.query("SELECT DISTINCT chapter_id FROM alignements")
        chapters = []
        for row in results:
            chapters.append(row['chapter_id'])

        time = {}

        time['minutes_dev'] = 0.0
        time['minutes_clean'] = 0.0
        time['minutes_other'] = 0.0

        for ch in chapters:

            results = tb_librispeech.find_one(id=ch)
            if results['corpus_name'] in corpus_dev:
                time['minutes_dev'] += results['minute']
            elif results['corpus_name'] in corpus_clean:
                time['minutes_clean'] += results['minute']
            elif results['corpus_name'] in corpus_other:
                time['minutes_other'] += results['minute']

        time['totalMinutes'] = time['minutes_other'] + time['minutes_clean'] + time['minutes_dev']

        "Count of time segments with exclusions"

        totalSeconds = 0.0
        for row in tb_alignements:
            identifier = row['audio_filename']

            result_exclusion = tb_exclusion.find_one(audio_filename=identifier)
            if result_exclusion['excluded'] == "False":
                result_duration = tb_audio.find_one(audio_filename=identifier)
                duration = result_duration['duration'] #In seconds
                totalSeconds += duration
            else:
                print(row['transcription'],row['seg_cible'])

        totalMins = totalSeconds/60
        return [time,totalMins]

    def json_to_googletranslate(self):
        tb_alignements = self.getTable("alignements")
        rows = tb_alignements.find(book_id=self.book_id)

        tokenizer = TreebankWordTokenizer()
        data = OrderedDict()
        for row in rows:
            transcpt = row['transcription']
            seg_source = row['seg_source']

            tok_transcpt = tokenizer.tokenize(transcpt)
            tok_seg_source = tokenizer.tokenize(seg_source)

            puncts = list(punctuation) + ["«", "»", "’","-","``","--"]
            tok_seg_source = list(filter(lambda x: x not in puncts, tok_seg_source))

            #print(len(tok_transcpt),len(tok_seg_source))
            if len(tok_transcpt) + round(len(tok_transcpt)*10/100) < len(tok_seg_source):
            #if len(tok_transcpt) != len(tok_seg_source):
                #print(len(tok_transcpt),len(tok_seg_source))
                #print(tok_transcpt,tok_seg_source)
                data[str(row['chapter_id'])+"_"+str(row['sentence_number'])] = transcpt.lower()
            else:
                data[str(row['chapter_id'])+"_"+str(row['sentence_number'])] = seg_source


        self.dumpJson("./gtranslate_books/"+str(self.book_id)+".json",data)

    def gtranslate_to_db(self):

        tb_gtranslate = self.getTable("alignements_gtranslate")

        with open("./gtranslate_books/"+str(self.book_id)+".fr.txt","r",encoding="utf8") as fh:
            translation = fh.readlines()




        with open("./gtranslate_books/"+str(self.book_id)+".json") as fh:
            jj = fh.read()


        data = json.JSONDecoder(object_pairs_hook=collections.OrderedDict).decode(jj)

        sys.stderr.write(str(self.book_id)+"\t"+str(len(data))+"\t"+str(len(translation))+"\n")
        assert len(data) == len(translation)
        x = 0
        for key,value in data.items():

            (chapter_id,sentence_no) = key.split("_")
            print(value,translation[x])

            db_data = dict(
                chapter_id = chapter_id,
                sentence_number = sentence_no,
                book_id = self.book_id,
                seg_source = value,
                translation = translation[x]
            )

            tb_gtranslate.insert(db_data)

            x += 1

    def clear_DB(self,table,book_id=-1):

        table = self.getTable(table)

        # If no parameter is given drops all the rows
        if book_id == -1:
            table.delete()
        else:
            table.delete(book_id=book_id)

    def prepare_data_forGIZA(self):
        """
        Extracts for all the DB text and assocs file tokenized and lowecased for GIZA
        :return: null
        """
        #.en file -> transcriptions, .fr file -> translation
        tb_alignments = self.getTable("alignements")

        with open('./GIZA/corpus.en', 'w') as a, open('./GIZA/corpus.fr', 'w') as b, open('./GIZA/corpus.assocs',"w") as c:

            for row in tb_alignments:
                (en,fr,id) = row['transcription'].strip(),row['seg_cible'].strip(),row['audio_filename']
                tokenizer = TreebankWordTokenizer()
                tokens_en = tokenizer.tokenize(en.lower())
                tokens_fr = tokenizer.tokenize(fr.lower())
                a.write(' '.join(tokens_en)+"\n")
                b.write(' '.join(tokens_fr)+"\n")
                c.write(id+"\n")


    @staticmethod
    def gettime(filename):
        return check_output(["soxi", "-d", filename]).split()[0].decode("utf-8")

    @staticmethod
    def dumpJson(path, data):
        with open(path, 'w') as outfile:
            json.dump(data, outfile)

    @staticmethod
    def loadJson(path):
        with open(path) as json_data:
            data = json.load(json_data)
            return data



class Command(object):
    def __init__(self, cmd, log):
        self.cmd = cmd
        self.process = None
        self.logFile = log

    def run(self, timeout):
        def target():
            print('Thread started')
            self.process = subprocess.Popen(self.cmd, shell=True, stderr=self.logFile)
            self.process.communicate()
            print('Thread finished')

        thread = threading.Thread(target=target)
        thread.start()

        thread.join(timeout)
        if thread.is_alive():
            print('Terminating process')
            self.process.terminate()
            thread.join()
        print(self.process.returncode)

def average(x):
    assert len(x) > 0
    return float(sum(x)) / len(x)

def pearson_def(x, y):
    assert len(x) == len(y)
    n = len(x)
    assert n > 0
    avg_x = average(x)
    avg_y = average(y)
    diffprod = 0
    xdiff2 = 0
    ydiff2 = 0
    for idx in range(n):
        xdiff = x[idx] - avg_x
        ydiff = y[idx] - avg_y
        diffprod += xdiff * ydiff
        xdiff2 += xdiff * xdiff
        ydiff2 += ydiff * ydiff

    return diffprod / math.sqrt(xdiff2 * ydiff2)

if __name__ == '__main__':

    #"Calculation Pearson correlation between hunAlign scores and our evaluations"

    bookObj = post_db_op(11)

    ###Chapters to evaluate: 51758,123443,127083,163375
    chapter = 51758
    chapters = [51758,123443,127083,163375]

    hunAlign_scores = []
    cng_scores = []
    lm_scores = []
    lm_cng_scores = []
    for chapter in chapters:
        chapter_results = bookObj.query("SELECT sentence_number,alignment_score,audio_filename FROM alignements WHERE chapter_id = "+str(chapter)+" LIMIT 50")

        for row in chapter_results:
            hunAlign_scores.append(float(row['alignment_score']))
            row_scores = bookObj.getTable("alignements_scores").find_one(audio_filename=
                                                                        row['audio_filename'])
            cng_scores.append(row_scores['score_cng'])
            lm_scores.append(row_scores['score_lm'])
            lm_cng_scores.append(row_scores['score_lm_cng'])


    assert len(hunAlign_scores) == len(cng_scores) == len(lm_scores)



    print(len(cng_scores),len(lm_scores),len(hunAlign_scores))
    #Score besacier


    besacier_scores = []
    for chapter in chapters:
        eval_folder = "./Evals/" + str(chapter)
        with open(eval_folder + "/Besacier-Alignment.txt", "r", encoding="utf8") as fh:
            besacier_evals = fh.readlines()
        for line in besacier_evals:
            besacier_scores.append(int(line.strip()))



    assert len(besacier_scores) == len(hunAlign_scores)
    print(len(besacier_scores),len(lm_cng_scores))

    print(pearson_def(besacier_scores, lm_cng_scores))

    sys.exit(":)")


    """
    #Visualise what's missing in one of the tables of db
    bookObj = post_db_op(11)
    results = bookObj.query("SELECT book_id,chapter_id,sentence_number FROM alignements_gtranslate GROUP BY book_id")

    for row in results:
        (book,ch,sent) = row['book_id'],row['chapter_id'], row['sentence_number']
        results_alignement = bookObj.getTable('alignements').find(book_id=book,chapter_id=ch,sentence_number=sent)
        for g_row in results_alignement:
            if g_row['sentence_number'] == sent and g_row['chapter_id'] == ch and g_row['book_id'] == book:
                print("ok")
            else:
                sys.exit("?")


    sys.exit("STOP HERE")
    """

    ids = [11,12,17,20,23,33,35,36,46,58,60,62,64,68,72,73,76,82,83,84,98,103,105,108,110,113,120,121,123,130,135,139,141,145,153,155,158,159,161,175,209,210,215,216,228,244,308,345,360,370,479,500,507,514,537,541,559,580,599,600,700,730,731,732,734,735,766,767,768,769,780,786,815,816,830,848,883,903,940,944,946,963,965,967,974,981,1004,1023,1028,1041,1056,1079,1081,1142,1164,1184,1257,1259,1260,1268]
    ids2 = [1322,1342,1353,1355,1399,1400,1423,1482,1497,1565,1608,1622,1629,1635,1685,1688,1727,1858,1862,1892,1906,1930,1937,1938,1941,1998,2017,2021,2083,2142,2166,2197,2275,2300,2383,2488,2505,2511,2524,2554,2569,2600,2609,2667,2681,2686,2688,2710,2741,2781,2833,2845,2850,2852,2864,2876,2944,2981,3091,3154,3268,3300,3526,3600,3721,3748,3795,3797,3800,4002,4028,4276,4280,4363,4537,4583,4705,4737,4761,4965,5131,5157,5225,5658,5669,5670,5682,5921,5946,6053,6124,6593,6626,6688,6737,6763,7025,8128,8166,8167]
    ids3 = [9189,9296,9455,9618,9662,9798,9845,9869,10056,10615,10940,11136,12587,13409,13505,14021,14725,17405,18857,19942,20239,20795,20912,21686,21700,22002,22088,22472,22759,24022,24055,24777,26640,27365,27435,28054,29021,29433,29734,30017,33504,33701,33800,34580,34901,35499,37915,38219]


    #135 removed from ids ! DONT FORGET TO ADD

    # book = post_db_op(46)
    # book.clear_DB("alignements_audio")
    # sys.exit("stop")

    corpus = ids + ids2 + ids3

    #ids = [12587,20795,21700,28054] #to fix


    errors = []
    exclude_list = {}
    corpus = [11]
    with open("./Evals/SUM.txt") as fh:
        scores = fh.readlines()
    with open("./Evals/corpus_correspondances.txt") as fh:
        correspondances = fh.readlines()
    db = dataset.connect('sqlite:///../../Interface/TA-LibriSpeechCorpus.db')

    book = post_db_op(corpus[0])
    for x in range(len(scores)):
        data = dict(
            audio_filename = correspondances[x].strip(),
            score_lm_cng = scores[x].strip()
        )
        print(data)
        book.getTable("alignements_scores").update(data,['audio_filename'])

    for id in corpus:
        # print("\t\tWorking on book: "+ str(id))
        book = post_db_op(id)
        #book.prepare_data_forGIZA()

        # book.add_time_segments()
        #
        # results = book.query("SELECT COUNT(DISTINCT chapter_id) FROM alignements WHERE book_id = "+str(book.book_id))
        # for row in results:
        #     for k,v in row.items():
        #         if v >= 14:
        #             errors.append(book.book_id)


        # tb_exclusion = book.getTable("alignements_excluded")
        #
        # dict_book = book.mark_sents_to_exclude()
        # print(dict_book)
        # for k,v in dict_book.items():
        #     data = dict(
        #         book_id = id,
        #         audio_filename = k,
        #         excluded = str(v)
        #     )
        #     tb_exclusion.insert(data)
        #
        # exclude_list[id] = dict_book
        # print(exclude_list)
        # #
        # error = book.checkTimeSegments()
        # print(error,book.book_id)
        # if error != []:
        #     errors.append(error)

        # book.add_time_segments()
        # book.clean_db()
        # print(book.json_to_googletranslate())
        # book.gtranslate_to_db()
        #book.clean_db()
        #print(punctuation)

        # print(book.gtranslate_to_db())

    print(errors)
    #book = post_db_op(11)
    #book.json_to_googletranslate()

    #print(book.estimate_volume())



    "Getting all of the sentences to calculate scores"
    """
    bookObject = post_db_op(11) #Object construction
    table_alignments = bookObject.getTable("alignements")

    #Iterate through the whole alignments table
    fh_en = open("./Evals/corpus.en.txt","w",encoding="utf8")
    fh_fr = open("./Evals/corpus.fr.txt","w",encoding="utf8")
    fh_ensure = open("./Evals/corpus_correspondances.txt","w",encoding="utf8")
    #In order to be sure -> extract the audio filename of each file to
    #another file
    for row in table_alignments:
        #We need to extract the transcription and seg_cible
        (en,fr,filename) = row['transcription'],row['seg_cible'],row['audio_filename']
        fh_en.write(en.strip()+"\n")
        fh_fr.write(fr.strip()+"\n")
        fh_ensure.write(filename.strip()+"\n")
    """

