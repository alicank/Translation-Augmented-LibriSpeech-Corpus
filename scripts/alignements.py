#!/usr/bin/python
# -*- coding: utf-8 -*-



import json
import sys
import os
import shutil
from shutil import copyfile
import re
from string import punctuation
from subprocess import STDOUT, check_output
import pickle
from collections import OrderedDict
import subprocess, threading
from time import sleep
from itertools import zip_longest
from bisect import bisect_left
import base64

if sys.path[0] == '/home/getalp/kocabiya/Scripts':
    server = True
else:
    server = False

if not server:
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import sent_tokenize
    from nltk.tokenize import word_tokenize
    import nltk.data
    from nltk.stem import SnowballStemmer
    from nltk.stem.snowball import FrenchStemmer
    from nltk.tokenize import TreebankWordTokenizer
    import treetaggerwrapper
    import dataset
    import difflib
    from nodejs.bindings import node_run
    from bs4 import BeautifulSoup
    from statistics import mean
    import diff_match_patch


class Alignements:
    def __init__(self, book_id, original_title, translated_title, fileName):
        self.db_librispeech = self.getDB_librispeech("../DB/librispeech")
        self.dataset = dataset.connect('sqlite:///../DB/csv.db')
        self.book_id = book_id
        self.original_title = original_title
        self.translated_title = translated_title
        self.corpus_dev = ["test-other", "test-clean", "dev-other", "dev-clean"]
        if fileName is None:
            self.fileName = "/corpus_data/empty.txt"
        else:
            self.fileName = fileName
        self.chapters = self.getChapters()
        self.alignedChapters = []
        self.procFolder = "../Alignements/data/" + str(self.book_id)
        self.lsFile = self.procFolder + "/ls_" + str(self.book_id) + ".txt"
        self.lcFile = self.procFolder + "/lc_" + str(self.book_id) + "." + getExtension(self.fileName)
        self.lfAlignerPath = "../Alignements/data/aligner/scripts/LF_aligner_3.11_with_modules.pl"
        self.alignedMinutes = self.getTimeAlignedChapters()
        self.alignmentQuality = self.getAlignmentQuality()  # Append alignment scores to chapters[]
        # For chapter extraction
        self.STOPWORD_en = ""
        self.STOPWORD_fr = ""
        self.regExOpts = re.I
        self.exceptions =  [142304,101622,22698,131332]
        """
        Exceptions: 1257350 -> diff chapter/transcription too high
        125750 -> add / delete too much (book id 2383)
        """

    def getChapters(self):
        chapters = []
        for liste in self.db_librispeech:
            if liste['book_id'] == self.book_id:
                chapters.append([liste['id'], liste['minute'],
                                 liste['reader_id'], liste['corpus_name'],
                                 liste['chapter']])
        return chapters

    def getDB_dataset(self, table):
        db = dataset.connect('sqlite:///../DB/csv.db')

        table_to_return = db[table]
        return table_to_return

    #TODO: hunAlign segmentation dump: raw file saved but file not aligned causes
    # causes problem with self.alignedChapters
    def getTimeAlignedChapters(self):
        minCount = 0.0
        # VERY SIMPLIFIED VERSION !
        for chapter in self.chapters:
            if os.path.isfile(self.procFolder + "/fr/" + str(chapter[0]) + "/raw.txt") and \
                    os.path.isfile(self.procFolder + "/en/" + str(chapter[0]) + "/raw.txt"):
                minCount += chapter[1]
                self.alignedChapters.append(True)
            else:
                self.alignedChapters.append(False)
        return minCount

    def getAlignmentQuality(self):
        """
		Requires the alignChapters() to be done with .meta files in order to work
		:return:
		"""
        for i in range(len(self.chapters)):

            if os.path.exists(self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + ".meta"):
                fh_meta = open(self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + ".meta")
                lines = fh_meta.readlines()
                case = lines[-1].strip()
                if case.startswith("Died"):
                    self.chapters[i].append(0.0)
                elif case.startswith("Sizes"):
                    self.chapters[i].append(0.0)
                else:
                    quality = case.split(" ")
                    self.chapters[i].append(quality[1])
                    fh_meta.close()
            else:
                self.chapters[i].append(0.0)

        l = []

        for chapter in self.chapters:
            l.append(float(chapter[5]))
        return (sum(l) / len(self.chapters))

    def getDB_librispeech(self, path):
        with open(path + ".json") as json_data:
            data = json.load(json_data)
            json_data.close()
            return data

    def createProcessingFolder(self):
        folder = "../Alignements/data/"
        # Books folder
        if not os.path.exists(folder + str(self.book_id)):
            os.makedirs(folder + str(self.book_id))
        # Data folder
        if not os.path.exists(folder + str(self.book_id) + "/data"):
            os.makedirs(folder + str(self.book_id) + "/data")

        # Alignment folder
        if not os.path.exists(folder + str(self.book_id) + "/Alignments"):
            os.makedirs(folder + str(self.book_id) + "/Alignments")

        # Chapter folders for data (transcription & flac files)
        fh_meta = open(folder + str(self.book_id) + "/data/chapters.meta", "w", encoding="utf8")
        # fr&en chapter files that will contain extracted chapters
        languages = ['en', 'fr']
        for lang in languages:
            if not os.path.exists(folder + str(self.book_id) + "/" + lang):
                os.makedirs(folder + str(self.book_id) + "/" + lang)

        for chapter in self.chapters:

            extension = re.search(r"\.(.+?)$", self.fileName)

            if not os.path.exists(folder + str(self.book_id) + "/data/" + str(chapter[0])):
                os.makedirs(folder + str(self.book_id) + "/data/" + str(chapter[0]))
            # Creating chapter folders to en_fr texts
            for lang in languages:
                if not os.path.exists(folder + str(self.book_id) + "/" + lang + "/" + str(chapter[0])):
                    os.makedirs(folder + str(self.book_id) + "/" + lang + "/" + str(chapter[0]))
            # Transcription and Sound Files from LibriVox
            corpus_folder = "../corpus_librispeech/" + str(chapter[3]) + "/" + str(chapter[2]) \
                            + "/" + str(chapter[0]) + "/"
            for file in os.listdir(corpus_folder):
                copyfile(corpus_folder + file, folder + str(self.book_id) + "/data/" + str(chapter[0]) + "/" + file)
            # Metadata File
            fh_meta.write(str(chapter[0]) + "\t" + str(chapter[-1]) + "\n")
        fh_meta.close()
        # LC file to process
        copyfile(".." + self.fileName, folder + str(self.book_id) + "/lc_" + str(self.book_id)
                 + "." + extension.group(1))

        # LS file to process
        copyfile("../corpus_data_en/" + str(self.book_id) + ".txt",
                 folder + str(self.book_id) + "/ls_" + str(self.book_id)
                 + ".txt")

        # meta file to chapters
        for lang in languages:
            copyfile(folder + str(self.book_id) + "/data/chapters.meta",
                     folder + str(self.book_id) + "/" + lang + "/chapters.meta")

    def convertFormat(self):

        if getExtension(self.fileName) != 'txt' and getExtension(self.fileName) != '':
            # Traitement pour le PDF soit par PerlNLPToolkit | Calibre | pdfMiner
            # Utilisation de Calibre est + robuste
            cmd = "ebook-convert " + self.lcFile + " " + self.procFolder \
                  + "/lc_" + str(self.book_id) + ".txt"

            os.system(cmd)
            htmlzFile = str(self.book_id) + ".htmlz"

            cmd2 = "ebook-convert " + self.lcFile + " " + self.procFolder \
                   + "/lc_" + htmlzFile
            os.system(cmd2)

            os.system("unzip " + self.procFolder + "/lc_" + htmlzFile
                      + " -d " + self.procFolder)

    def extractChapters(self, regExp_en, regExp_fr):
        languages = ['en', 'fr']
        fh = open(self.lsFile, "r")
        ls_text = fh.read()
        ls_chapters = re.findall(regExp_en, ls_text)
        print(ls_chapters)
        # Makedir
        for lang in languages:
            if not os.path.exists(self.procFolder + "/" + lang + "/chapitres"):
                os.makedirs(self.procFolder + "/" + lang + "/chapitres")

        inbetweenExtractor(ls_chapters, self, "en", STOP=self.STOPWORD_en)
        fh.close()
        fh_cible = open(self.lcFile[:-len(getExtension(self.fileName))] + "txt", "r", encoding="utf8")
        lc_text = fh_cible.read()
        lc_chapters = re.findall(regExp_fr, lc_text)
        print(lc_chapters)

        inbetweenExtractor(lc_chapters, self, "fr", STOP=self.STOPWORD_fr)

    def createPipeline(self):
        x = 0
        # Create pipeline for all chapters
        languages = ["english", "french"]
        for lang in languages:  # for each language

            for i in range(len(self.chapters)):  # for each chapter
                if self.alignedChapters[i]:  # if the chapter is extracted


                    if lang == "french":
                        copyfile(self.procFolder + "/" + lang[:2] + "/" + str(self.chapters[i][0]) + "/raw.txt",
                                 self.procFolder + "/" + lang[:2] + "/" + str(self.chapters[i][0]) + "/raw.sed")

                        # Preprocessing to delete links, page numbers and "-" at the end of the file

                        # copyfile("./regex.sh",self.procFolder+"/"+lang[:2]+"/"+str(self.chapters[i][0])+"/regex.sh")
                        os.system("perl -wpi -e 's/[--]\n/-/g' " + self.procFolder + "/" + lang[:2] + "/" + str(
                            self.chapters[i][0]) + "/raw.sed")
                        os.system("perl -pi -e 's/[--] ?\d+ ?[--]//g' "
                                  + self.procFolder + "/" + lang[:2] + "/" + str(self.chapters[i][0]) + "/raw.sed")
                        os.system("perl -pi -e 's/\d+\n//g' "
                                  + self.procFolder + "/" + lang[:2] + "/" + str(self.chapters[i][0]) + "/raw.sed")
                        os.system("perl -pi -e 's/(https?:\/\/)?[0-9a-zA-Z]+\.[-_0-9a-zA-Z]+\.[0-9a-zA-Z]+//g' "
                                  + self.procFolder + "/" + lang[:2] + "/" + str(self.chapters[i][0]) + "/raw.sed")

                    # Filehandles
                    if lang == "english":
                        fh_chapter = open(
                            self.procFolder + "/" + lang[:2] + "/" + str(self.chapters[i][0]) + "/raw.txt", "r",
                            encoding="utf8")
                    else:
                        fh_chapter = open(
                            self.procFolder + "/" + lang[:2] + "/" + str(self.chapters[i][0]) + "/raw.sed", "r",
                            encoding="utf8")
                    fh_saveFile = open(self.procFolder + "/" + lang[:2] + "/" + str(self.chapters[i][0]) + "/raw.para",
                                       "w", encoding="utf8")

                    para_lines = "<p>\n"
                    raw_lines = fh_chapter.read()

                    subst = "\\n<p>"
                    regex = r"\n+$"
                    para_lines += re.sub(regex, subst, raw_lines, 0, re.MULTILINE)

                    fh_saveFile.write(para_lines)
                    fh_chapter.close()
                    fh_saveFile.close()

                    #############################
                    # 2. Sentence Split

                    fh_chapter = open(self.procFolder + "/" + lang[:2] + "/" + str(self.chapters[i][0]) + "/raw.para",
                                      "r", encoding="utf8")
                    fh_sentence_split = open(
                        self.procFolder + "/" + lang[:2] + "/" + str(self.chapters[i][0]) + "/raw.sent", "w",
                        encoding="utf8")
                    tab_text = fh_chapter.readlines()
                    tab_text_stripped = [tab_text[x].strip() for x in range(len(tab_text))]

                    sent_detector = nltk.data.load('tokenizers/punkt/' + lang + '.pickle')
                    fh_sentence_split.write('\n'.join(
                        sent_detector.tokenize(' '.join(tab_text_stripped))))

                    fh_sentence_split.close()
                    fh_chapter.close()


                    ################################
                    # 3. Stemming

                    fh_sentences = open(self.procFolder + "/" + lang[:2] + "/" + str(self.chapters[i][0]) + "/raw.sent",
                                        "r", encoding="utf8")
                    fh_stemmed = open(self.procFolder + "/" + lang[:2] + "/" + str(self.chapters[i][0]) + "/raw.stem",
                                      "w", encoding="utf8")
                    tab_text = fh_sentences.readlines()
                    tab_text = [(re.sub(r'\n', r" \\n ", x)) for x in tab_text]
                    """
					tagger = treetaggerwrapper.TreeTagger(TAGLANG=lang[:2],
					                                      TAGDIR="../lib/TreeTagger")

					tags = tagger.tag_text(tab_text, prepronly=True)
					"""

                    if lang == 'english':
                        snowball_stemmer = SnowballStemmer("english")
                        tok_file = open(self.procFolder + "/" + lang[:2] + "/"
                                        + str(self.chapters[i][0]) + "/en_tokens.txt", "w", encoding="utf8")
                    elif lang == 'french':
                        snowball_stemmer = FrenchStemmer()
                        tok_file = open(self.procFolder + "/" + lang[:2] + "/"
                                        + str(self.chapters[i][0]) + "/fr_tokens.txt", "w", encoding="utf8")
                    # print(tab_text)
                    # print(tags)


                    tokenizer = TreebankWordTokenizer()

                    tokens = tokenizer.tokenize(' '.join(tab_text))

                    # tokens = nltk.word_tokenize(' '.join(tab_text), language=lang)

                    stemmed = [snowball_stemmer.stem(x) for x in tokens]

                    for i in range(len(stemmed)):
                        if stemmed[i] != "<" and stemmed[i] != ">" and stemmed[i] != "p" and stemmed[i] != "\\n":
                            tok_file.write("0\t" + stemmed[i] + "\t" + tokens[i] + "\n")

                    stemmed = [(re.sub(r'\\n', r"\n", stemmed[x])) for x in range(len(stemmed))]
                    print(stemmed)
                    print(tokens)

                    fh_stemmed.write(' '.join(stemmed))

                    fh_sentences.close()
                    fh_stemmed.close()

                    # OTHER METHODS #####
                    # self.stopwords = list(punctuation)

                    # Essai

                    # tab_text = fh_chapter.read()
                    # tab_text = fh_chapter.readlines() #\r problem when .read()

                    # tab_text_stripped = [tab_text[x].strip() for x in range(len(tab_text))]
                    """
					tagger = treetaggerwrapper.TreeTagger(TAGLANG=lang[:2],
					                                      TAGDIR="../lib/TreeTagger")

					tags = tagger.tag_text(tab_text, prepronly=True)
					"""
                    # tags = tagger.tag_text(''.join(tab_text_stripped), prepronly=True)

                    # tokens = word_tokenize(''.join(tab_text_stripped),language=lang)

                    # sentence_split = sent_tokenize(''.join(tab_text_stripped),language=lang)

                    text = ""
                    """
					for tag in tags:
						if tag not in self.stopwords:
							text += tag +' '
						if tag in self.stopwords:
							text += tag+ "\n"
					fh_saveFile.write(text)
					"""
                # fh_saveFile.write('\n'.join(tags))
                # fh_saveFile.close()
                # convert_normalize.ligne_par_phrase(self.procFolder+"/"+lang[:2]+"/"+str(chapitre[0])+"/"+str(chapitre[0])+".txt")

    def alignChapters(self):
        fullPath = "/home/alican/Documents/LIG-StageM2/LibriSpeech/Alignements/data/" + str(self.book_id)
        for i in range(len(self.chapters)):  # for each chapter
            if self.alignedChapters[i]:  # if the chapter is extracted

                en_file = fullPath + "/en/" + str(self.chapters[i][0]) + "/raw.stem"

                fr_file = fullPath + "/fr/" + str(self.chapters[i][0]) + "/raw.stem"

                print("\n\n\t" + str(self.chapters[i][0]) + "\t" + str(self.chapters[i][1]) + "\t" + str(
                    self.chapters[i][2]) + "\t" + str(self.chapters[i][3]))
                if os.path.isdir(self.procFolder + "/Alignments/" + str(self.chapters[i][0])):
                    print("\n\t\t\tChapter already aligned passing!!!!\n")

                else:
                    ##########LFAligner Expects FULL PATH! ##############
                    cmd = "perl " + self.lfAlignerPath + \
                          " --segment=\"n\" --infiles \"" + en_file + "\",\"" + fr_file \
                          + "\" --languages=\"en\",\"fr\""

                    log = open(self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + ".meta", "w")
                    command = Command(cmd, log)
                    command.run(timeout=40)

                    currentPath = self.procFolder + "/en/" + str(self.chapters[i][0])
                    contents = [os.path.join(currentPath, o) for o in os.listdir(currentPath) if
                                os.path.isdir(os.path.join(currentPath, o))]

                    os.rename(contents[0], self.procFolder + "/Alignments/" + str(self.chapters[i][0]))

    def postProcessing(self):

        ### 1er Etape -> Reverse Stemming
        for i in range(len(self.chapters)):  # for each chapter
            if self.alignedChapters[i]:  # if the chapter is extracted


                fh = open(self.procFolder + "/Alignments/"
                          + str(self.chapters[i][0]) + "/aligned_raw-raw.txt", "r")

                alignedFile = fh.readlines()
                # Supprimer les <p>
                alignedFile = [(re.sub(r'<p>', r"", x)) for x in alignedFile]
                fh_ls = open(self.procFolder + "/Alignments/"
                             + str(self.chapters[i][0]) + "/stem_ls.txt", "w")
                fh_lc = open(self.procFolder + "/Alignments/"
                             + str(self.chapters[i][0]) + "/stem_lc.txt", "w")
                fh_scores = open(self.procFolder + "/Alignments/"
                                 + str(self.chapters[i][0]) + "/scores.txt", "w")
                count = 0

                for sublist in alignedFile:
                    translations = sublist.split("\t")
                    if translations[0] != "":
                        fh_ls.write("<" + str(count) + ">" + translations[0].strip() + "<" + str(count) + ">\n")
                    else:
                        fh_ls.write("<" + str(count) + ">" + "NA" + "<" + str(count) + ">\n")
                    if translations[1] != "":
                        fh_lc.write("<" + str(count) + ">" + translations[1].strip() + "<" + str(count) + ">\n")
                    else:
                        fh_lc.write("<" + str(count) + ">" + "NA" + "<" + str(count) + ">\n")

                    fh_scores.write("<" + str(count) + ">" + translations[2] + "<" + str(count) + ">\n")
                    count += 1

                fh_scores.close()
                fh_ls.close()
                fh_lc.close()

                """
				# Sed cmd sed -i -E "s/<p>//gm" hyp.txt
				copyfile(self.procFolder+ "/en/"
				                    + str(self.chapters[i][0]) + "/raw.sent",
				         self.procFolder + "/Alignments/"
				         + str(self.chapters[i][0]) + "/ls_sent.txt")
				copyfile(self.procFolder + "/fr/"
				         + str(self.chapters[i][0]) + "/raw.sent",
				         self.procFolder + "/Alignments/"
				         + str(self.chapters[i][0]) + "/lc_sent.txt")

				os.system("sed -i -E \"s/<p>//gm\" " + self.procFolder + "/Alignments/"
				         + str(self.chapters[i][0]) + "/ls_sent.txt")

				os.system("sed -i -E \"s/<p>//gm\" " + self.procFolder + "/Alignments/"
				         + str(self.chapters[i][0]) + "/lc_sent.txt")
				fh.close()
				fh_ls.close()
				fh_lc.close()

				os.remove("./example/ref.txt")
				os.remove("./example/hyp.txt")

				### LS_LC FILE as ref
				copyfile(self.procFolder + "/Alignments/"
				         + str(self.chapters[i][0]) + "/stem_ls.txt",
				         "./example/ref.txt")

				### Sent File as hyp
				copyfile(self.procFolder + "/Alignments/"
				         + str(self.chapters[i][0]) + "/ls_sent.txt",
				         "./example/hyp.txt")

				os.system("./mwerAlignTest > ../Alignements/data/"
				          +str(self.book_id)+"/Alignments/"
				          +str(self.chapters[i][0])+"/destemmed.txt")
				"""
                ######### Reverse stemming ######################

                # Pour l'anglais "en", "tok_file" , "stem_file"
                print("Chapter id: " + str(self.chapters[i][0]))

                # print("\t\tAnglais\n")
                language = "en"
                tok_file = self.procFolder + "/en/" + str(self.chapters[i][0]) + "/en_tokens.txt"
                stem_file = self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/stem_ls.txt"
                sortie_ls = self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/reversed_stem_ls.txt"
                diff_ls = self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/diff_ls.html"
                if not os.path.exists(sortie_ls):
                    num_stem_ls = wc(stem_file)

                    fh_sortie_ls = open(sortie_ls, "w", encoding="utf8")

                    fh_stem = open(stem_file, "r", encoding="utf8")
                    stem = fh_stem.readlines()
                    # stem = [(re.sub(r'\n', r" \ğ ", stem[x])) for x in range(len(stem))]
                    stem = [(re.sub(r'<\d+>', r"", stem[x])) for x in range(len(stem))]
                    stem = [(re.sub(r'\ufeff', r"", stem[x])) for x in range(len(stem))]
                    stem = [(re.sub(r'< p >', r"", stem[x])) for x in range(len(stem))]
                    # print(stem)
                    fh_ls_sent = open(self.procFolder + "/en/" + str(self.chapters[i][0]) + "/raw.sent")
                    ls_sent = fh_ls_sent.readlines()
                    ls_sent = [(re.sub(r'<p>', r"", ls_sent[x])) for x in range(len(ls_sent))]
                    ls_sent = [ls_sent[x].strip() for x in range(len(ls_sent))]
                    # print(ls_sent)
                    stem = ''.join(stem)
                    ls_sent = ''.join(ls_sent)

                    textA = stem
                    textB = ls_sent

                    # create a diff_match_patch object
                    dmp = diff_match_patch.diff_match_patch()

                    # Depending on the kind of text you work with, in term of overall length
                    # and complexity, you may want to extend (or here suppress) the
                    # time_out feature
                    dmp.Diff_Timeout = 0  # or some other value, default is 1.0 seconds

                    # All 'diff' jobs start with invoking diff_main()
                    diffs = dmp.diff_main(textA, textB)

                    # diff_cleanupSemantic() is used to make the diffs array more "human" readable
                    dmp.diff_cleanupSemanticLossless(diffs)

                    # print(diffs)
                    # and if you want the results as some ready to display HMTL snippet
                    htmlSnippet = dmp.diff_prettyHtml(diffs)
                    fh_html_ls = open(diff_ls, "w", encoding="utf8")
                    html_start = """<!DOCTYPE html><html>
					<head><meta charset="UTF-8"><title>TextDiff</title></head><body><pre>"""
                    fh_html_ls.write(html_start + htmlSnippet + "</pre></body></html>")
                    # print(htmlSnippet)
                    fh_html_ls.close()
                    text = diffs_to_text(diffs)
                    text_lines = text.split("\n")
                    cpt = 0
                    for l in range(len(text_lines) - 1):
                        startTag = "<" + str(cpt) + "> "
                        text_lines[l] = startTag + text_lines[l] + " <" + str(cpt) + ">\n"
                        cpt += 1
                    # print(text_lines)
                    # final = re.sub(r"ğ", "\n", ''.join(text), 0, re.I)
                    fh_sortie_ls.write(''.join(text_lines))
                    fh_sortie_ls.close()
                    num_rev_stem_ls = wc(sortie_ls)
                """
				prettyhtml = node_run('/var/www/html/Alignements/js/essai.js', stem, ls_sent)

				prettyhtml = prettyhtml[1]

				print(prettyhtml)

				soup = BeautifulSoup(prettyhtml, "lxml")
				firstTag = re.match(r"<(.+?)>",prettyhtml)

				firstHeader = soup.find(firstTag.group(1))
				text = []
				for tag in [firstHeader] + firstHeader.findNextSiblings():

					if tag.name == 'span':
						text.append(tag.string)

					elif tag.name == 'ins':
						text.append(tag.string)
					elif tag.name == "del":
						if re.search(r"<\d+>", tag.string, re.I):
							regex = r"[^ğNA\d<>]+"
							subst = ""
							result = re.sub(regex, subst, tag.string, 0)

							text.append(result)


				final = re.sub(r"ğ","\n",''.join(text),0,re.I)
				fh_sortie_ls.write(final)

				#print(final)
				fh_stem.close()
				#reverseStemming(language,tok_file,stem_file,fh_sortie_ls)
				fh_sortie_ls.close()
				sys.exit()
				"""

                # print("\n\tFrançais\n")
                language = "fr"
                tok_file = self.procFolder + "/fr/" + str(self.chapters[i][0]) + "/fr_tokens.txt"
                stem_file = self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/stem_lc.txt"
                sortie_lc = self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/reversed_stem_lc.txt"
                diff_lc = self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/diff_lc.html"
                if not os.path.exists(sortie_lc):
                    fh_sortie_lc = open(sortie_lc, "w", encoding="utf8")
                    num_stem_lc = wc(stem_file)
                    fh_stem = open(stem_file, "r", encoding="utf8")
                    stem = fh_stem.readlines()
                    # stem = [(re.sub(r'\n', r"ğ", stem[x])) for x in range(len(stem))]
                    stem = [(re.sub(r'<\d+>', r"", stem[x])) for x in range(len(stem))]
                    stem = [(re.sub(r'\ufeff', r"", stem[x])) for x in range(len(stem))]
                    stem = [(re.sub(r'< p >', r"", stem[x])) for x in range(len(stem))]
                    # print(stem)
                    fh_lc_sent = open(self.procFolder + "/fr/" + str(self.chapters[i][0]) + "/raw.sent")
                    lc_sent = fh_lc_sent.readlines()
                    lc_sent = [(re.sub(r'<p>', r"", lc_sent[x])) for x in range(len(lc_sent))]
                    lc_sent = [lc_sent[x].strip() for x in range(len(lc_sent))]
                    # print(lc_sent)
                    stem = ''.join(stem)
                    lc_sent = ''.join(lc_sent)

                    textA = stem
                    textB = lc_sent

                    # create a diff_match_patch object
                    dmp = diff_match_patch.diff_match_patch()

                    # Depending on the kind of text you work with, in term of overall length
                    # and complexity, you may want to extend (or here suppress) the
                    # time_out feature
                    dmp.Diff_Timeout = 0  # or some other value, default is 1.0 seconds

                    # All 'diff' jobs start with invoking diff_main()
                    diffs = dmp.diff_main(textA, textB)

                    # diff_cleanupSemantic() is used to make the diffs array more "human" readable
                    dmp.diff_cleanupSemanticLossless(diffs)

                    # and if you want the results as some ready to display HMTL snippet
                    htmlSnippet = dmp.diff_prettyHtml(diffs)
                    fh_html_lc = open(diff_lc, "w", encoding="utf8")
                    html_start = """<!DOCTYPE html><html>
										<head><meta charset="UTF-8"><title>TextDiff</title></head><body><pre>"""
                    fh_html_lc.write(html_start + htmlSnippet + "</pre></body></html>")
                    fh_html_lc.close()
                    # print(htmlSnippet)

                    text = diffs_to_text(diffs)
                    text_lines = text.split("\n")
                    cpt = 0
                    for l in range(len(text_lines) - 1):
                        startTag = "<" + str(cpt) + "> "
                        text_lines[l] = startTag + text_lines[l] + " <" + str(cpt) + ">\n"
                        cpt += 1
                    # print(text_lines)
                    # final = re.sub(r"ğ", "\n", ''.join(text), 0, re.I)
                    fh_sortie_lc.write(''.join(text_lines))
                    fh_sortie_lc.close()
                    num_rev_stem_lc = wc(sortie_lc)
                """
				prettyhtml = node_run('/var/www/html/Alignements/js/essai.js', stem, lc_sent)

				prettyhtml = prettyhtml[1]
				print(prettyhtml)
				soup = BeautifulSoup(prettyhtml, "lxml")
				firstTag = re.match(r"<(.+?)>", prettyhtml)

				firstHeader = soup.find(firstTag.group(1))
				text = []
				for tag in [firstHeader] + firstHeader.findNextSiblings():
					if tag.name == "span":
						text += tag.string
					elif tag.name == "ins":
						text += tag.string
					elif tag.name == "del":
						if re.search(r"<\d+>",tag.string,re.I):
							regex = r"[^ğNA\d<>]+"
							subst = ""
							result = re.sub(regex, subst, tag.string, 0)

							text.append(result)
				#print(text)
				final = re.sub(r"ğ", "\n", ''.join(text), 0, re.I)
				fh_sortie_lc.write(final)
				"""
                # reverseStemming(language, tok_file, stem_file, fh_sortie_lc)


                # Regular expressions after post stemming
                # book id, chapter id, lang

                ##Copying file as regex! -> when cleaning this should be cleaned
                if os.path.exists(self.procFolder + "/Alignments/"
                                          + str(self.chapters[i][0]) + "/reversed_stem_ls_regex.txt"):
                    os.remove(self.procFolder + "/Alignments/"
                              + str(self.chapters[i][0]) + "/reversed_stem_ls_regex.txt")
                if os.path.exists(self.procFolder + "/Alignments/"
                                          + str(self.chapters[i][0]) + "/reversed_stem_lc_regex.txt"):
                    os.remove(self.procFolder + "/Alignments/"
                              + str(self.chapters[i][0]) + "/reversed_stem_lc_regex.txt")

                copyfile(self.procFolder + "/Alignments/"
                         + str(self.chapters[i][0]) + "/reversed_stem_ls.txt",
                         self.procFolder + "/Alignments/"
                         + str(self.chapters[i][0]) + "/reversed_stem_ls_regex.txt")
                copyfile(self.procFolder + "/Alignments/"
                         + str(self.chapters[i][0]) + "/reversed_stem_lc.txt",
                         self.procFolder + "/Alignments/"
                         + str(self.chapters[i][0]) + "/reversed_stem_lc_regex.txt")

                # ASSERTION!
                try:
                    assert num_stem_ls == num_rev_stem_ls == num_rev_stem_lc == num_stem_lc
                except AssertionError:
                    print(num_stem_ls, num_stem_lc, num_rev_stem_ls, num_rev_stem_lc)
                    sys.exit("Assertion Error!")
                except UnboundLocalError:
                    pass

                """
				languages = ["en","fr"]
				for lang in languages:
					os.system("perl ./after_stem.pl " + str(self.book_id) + " "
					          + str(self.chapters[i][0]) + " " + lang)
				"""

                """
				if self.chapters[i][3] not in corpus_dev:

					easytrick(self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/forcedAlignment.txt",
					          self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/forcedAlignment2.txt")
					# Reversing the pre-processing for forced transcriptions
					fh_transcpt = open(self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/forcedAlignment2.txt"
					                   ,"r",encoding="utf8")
					fh_original = open(self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/reversed_stem_ls_regex.txt")
					original_sents = OrderedDict()

					fh_sortie = open(self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/transcriptions_aligned.txt","w",encoding="utf8")

					for line in fh_original:
						line = line.strip()
						id_phrase = re.search(r"<(.+?)> ?(.+?) ?<.+?>",line,re.I)
						if id_phrase:
							pass
							original_sents[str(id_phrase.group(1))] = id_phrase.group(2).strip()
						else:
							pass


					#Now changing the forced Alignment file
					forced_algnmts = fh_transcpt.readlines()
					fh_transcpt.close()

					forced_algnmts = [(re.sub(r'\n', r"ğ", forced_algnmts[x])) for x in range(len(forced_algnmts))]
					forced = ""
					for tag in forced_algnmts:
						forced += tag
					original = ""
					for k,v in original_sents.items():
						original += "<" + k +"> " +v+ " <"+k+"> "

					#d = difflib.Differ()
					#diff = d.compare(forced,original)
					diff = difflib.ndiff(forced, original)
					phrase = computeChanges(list(diff))
					phrase = re.sub(r"\\n","\n",phrase,0,re.I)
					fh_sortie.write(phrase)




					#regex = r"\n"
					#subst = "ğ"
					#forced_algnmts = re.sub(regex, subst, forced_algnmts, 0)



				"""

                # print(original_sents)

                """
				print("-------------"+str(self.chapters[i][0])+"----------------")
				for j in range(len(tags)-1):

					search = re.search(r"<(\d+)> ?(.+?) ?<\d+>",tags[j],re.IGNORECASE)
					id = search.group(1)
					phrase = search.group(2)

					#print(phrase,"\n",original_sents[id])



					#fh_sortie.write("<"+id+"> "+sent+ " <"+id+"> ")


					#print(id,phrase,original_sents[id])
				"""

    def forceTranscriptions(self):

        for i in range(len(self.chapters)):
            if self.alignedChapters[i]:
                # mwerAlign for forcing transcriptions

                if self.chapters[i][3] not in self.corpus_dev:

                    # Processing the transcription files for mwerAlign

                    transcription_file = self.procFolder + "/data/" + \
                                         str(self.chapters[i][0]) + "/" + \
                                         str(self.chapters[i][2]) + "-" + str(self.chapters[i][0]) + ".trans.txt"

                    fh_transcpt = open(transcription_file, "r", encoding="utf8")

                    transcriptions = OrderedDict()
                    transcr_str = ""
                    for line in fh_transcpt:
                        line = line.strip()
                        searchObj = re.search(r'(\d+-\d+-\d+) (.+?)$', line, re.I)
                        transcriptions[searchObj.group(1)] = searchObj.group(2)
                        transcr_str += searchObj.group(2).lower() + "\n"

                    fh_transcpt.close()

                    # Saving transcpt file as ref
                    fh_ref = open("./example/ref.txt", "w", encoding="utf8")
                    for sent in transcriptions.values():
                        sent = sent.lower()
                        fh_ref.write(sent.strip() + "\n")

                    fh_ref.close()

                    print("Forcing speech transcriptions to chapters with mwerAlign for " + str(self.book_id),
                          end="\n::")
                    print(self.chapters[i])
                    print("")
                    # Perl tolowercase saved as hyp file

                    if os.path.exists(self.procFolder + "/Alignments/"
                                              + str(self.chapters[i][0]) + "/reversed_stem_ls_regex.txt"):

                        os.system("perl -ple '$_=lc' " + self.procFolder + "/Alignments/"
                                  + str(self.chapters[i][0]) + "/reversed_stem_ls_regex.txt > ./example/hyp.txt")

                        # Regex before mwerAlign

                        # os.system("perl -pi -w -e 's/\.|,|:|;|\!|?//g;' ")
                        os.system("sed -i \"s/[\.,!?:;]//g\" ./example/hyp.txt")
                        os.system("sed -i \"s/--//g\" ./example/hyp.txt")
                        os.system("sed -i \"s/' //g\" ./example/hyp.txt")
                        os.system("perl -pi -w -e 's/`//g;' ./example/hyp.txt")
                        os.system("perl -pi -w -e \"s/> '/>  /g;\" ./example/hyp.txt")
                        os.system("perl -pi -w -e \"s/>'/> /g;\" ./example/hyp.txt")
                        os.system("perl -pi -w -e \"s/[()]//g;\" ./example/hyp.txt")

                        os.system("./mwerAlignTest > ../Alignements/data/"
                                  + str(self.book_id) + "/Alignments/"
                                  + str(self.chapters[i][0]) + "/forcedAlignment.txt")

                        # ref and hyp files copied to alignments folder
                        copyfile("./example/ref.txt", self.procFolder +
                                 "/Alignments/" + str(self.chapters[i][0]) + "/ref.txt")
                        copyfile("./example/hyp.txt", self.procFolder +
                                 "/Alignments/" + str(self.chapters[i][0]) + "/hyp.txt")

                        easytrick(self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/forcedAlignment.txt",
                                  self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/forcedAlignment2.txt")

                        ################## Problem starts here ! ################

                        # Reversing the pre-processing for forced transcriptions
                        fh_transcpt = open(
                            self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/forcedAlignment2.txt"
                            , "r", encoding="utf8")
                        fh_original = open(
                            self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/reversed_stem_ls_regex.txt")
                        original_sents = OrderedDict()

                        fh_sortie = open(
                            self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/transcriptions_aligned.txt",
                            "w", encoding="utf8")

                        for line in fh_original:
                            line = line.strip()
                            id_phrase = re.search(r"<(.+?)> ?(.+?) ?<.+?>", line, re.I)
                            if id_phrase:
                                pass
                                original_sents[str(id_phrase.group(1))] = id_phrase.group(2).strip()
                            else:
                                pass

                        # Now changing the forced Alignment file
                        forced_algnmts = fh_transcpt.read()
                        fh_transcpt.close()

                        """
						forced_algnmts = [(re.sub(r'\n', r"ğ", forced_algnmts[x])) for x in range(len(forced_algnmts))]
						forced = ""

						for tag in forced_algnmts:
							forced += tag
						original = ""
						for k, v in original_sents.items():
							original += "<" + k + "> " + v + " <" + k + "> "
						"""
                        forced_algnmts = re.sub(r'\n', r"ğ", forced_algnmts, 0, re.I | re.DOTALL)
                        original = ""
                        for k, v in original_sents.items():
                            original += "<" + k + "> " + v + " <" + k + "> "
                        prettyhtml = node_run('/var/www/html/Alignements/js/essai.js', forced_algnmts, original)
                        prettyhtml = prettyhtml[1]

                        soup = BeautifulSoup(prettyhtml, "lxml")

                        text = []

                        firstHeader = soup.find('span')
                        for tag in [firstHeader] + firstHeader.findNextSiblings():
                            if tag.name == 'span':
                                text.append(tag.string)
                            elif tag.name == 'ins':
                                text.append(tag.string)

                            elif tag.name == 'del' and re.search(r"ğ", tag.string, re.I):
                                text.append("\n")

                        fh_sortie.write(''.join(text))

                        """ Regex approach to the problem but it doesn't work very well either
						#print(forced)
						#print(original)
						forced_splitted = forced.split("ğ")
						#print(forced_splitted[0])
						regexList = " "+punctuation


						for x in range(len(forced_splitted)-1):

							changed = re.sub(r"<\d+>","",forced_splitted[x],0,re.I)
							changed = re.sub(r"''", "", changed, 0, re.I)
							tokenizer = tokenizer = TreebankWordTokenizer()

							tags = tokenizer.tokenize(changed)
							print(tags)
							try:
								toSearch = tags[-3]+ " "+ tags[-2] + " "+ tags[-1]
							except:
								break

							#print("toSearch",toSearch)
							toSearch = tags[-3] +"["+regexList+"\d]+" + tags[-2] +"["+regexList+"\d]+"\
							           + tags[-1]


							essai = re.search(r"(.+?"+toSearch+").+?",original,re.I)
							if essai:
								print("found",essai.group(1))

								print(essai.start(), essai.end())
								original = original[essai.end():]
								print("Replacing span\t", original)
								fh_sortie.write(essai.group(1)+"\n")

							else:
								print("splitted sentence\t", forced_splitted[x])
								print("failed i tried to search",toSearch)
								print("the sentence is ",original)
								fh_sortie.write(forced_splitted[x] + "\n")
								#sys.exit("hmm")


						sys.exit()
						# d = difflib.Differ()
						# diff = d.compare(forced,original)
						#diff = difflib.ndiff(forced, original)
						#print(list(diff))
						#sys.exit()
						#phrase = computeChanges(list(diff))
						#phrase = re.sub(r"\\n", "\n", phrase, 0, re.I)
						#fh_sortie.write(phrase)
						"""
                else:
                    pass
                    print("Diffmaxcommun algorithm is being applied to\n::", end="")
                    print(self.chapters[i])
                    if not os.path.exists(self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/final.txt"):
                        os.system("perl ./forceAlignments.pl " + str(self.book_id) +
                                  " " + str(self.chapters[i][0]) + " " + str(self.chapters[i][2]) + " dev")
                    else:
                        print("File already exists - passing!\n")

    # --------> Audio file manipulations <------------
    """
	Instead of using GIZA++ word alignments, would it be better to adjust audio files
	to the transcriptions : Forced Alignment with offset for each word
	"""

    # NEW -> According to the sentence split
    def forceAlignments(self, exclude_word_alignments=False):
        """
				Gentle: Robust yet lenient forced-aligner built on Kaldi.
				A tool for aligning speech with text.

				Input: Forced transcription file coming from mwerAlign.
				18.05.2017: Change: Adding a diff between transcriptions and original transcpt
				:return: NULL
		"""

        # For each chapter that is aligned
        for i in range(len(self.chapters)):
            # If the chapter is in dev/test it's not aligned with mwerAlign
            if self.alignedChapters[i] and self.chapters[i][3] not in self.corpus_dev:

                # Debug purposes
                # if self.chapters[i][0] != 232691:
                # continue

                # Excetions

                if self.chapters[i][0] in self.exceptions:
                    continue




                sys.stdout.write("Processing Chapter: " + str(self.chapters[i][0]) + "\t Book: " + str(self.book_id)+"\n")
                # Shortcuts to folders
                soundFolder = self.procFolder + "/gentle/" + str(self.chapters[i][0])
                chapter_flacs_folder = self.procFolder + "/data/" + str(self.chapters[i][0])

                # In order to pass the pipeline if the sound file is cut
                if os.path.exists(soundFolder+"/gentle.json") and os.path.exists(soundFolder+"/diff_transcpt.html"):
                    soundFolder_content = os.listdir(soundFolder)
                    if len(soundFolder_content) > 10:
                        continue

                # Makedirs
                # Creating audio manipulations folder/copying files
                sys.stdout.write("Creating audio/gentle folder \n")
                if not os.path.exists(self.procFolder + "/gentle"):
                    os.mkdir(self.procFolder + "/gentle")
                if not os.path.exists(self.procFolder + "/gentle/" + str(self.chapters[i][0])):
                    os.mkdir(self.procFolder + "/gentle/" + str(self.chapters[i][0]))

                # Opening the log file
                if os.path.exists(soundFolder + "/err_log.txt"):
                    log = open(soundFolder + "/err_log.txt", "a")
                else:
                    log = open(soundFolder + "/err_log.txt", "w")

                # Forced transcription file
                transcpt_path = self.procFolder + "/Alignments/" \
                                + str(self.chapters[i][0]) + "/transcriptions_aligned.txt"
                if not os.path.exists(transcpt_path):
                    continue
                with open(transcpt_path, "r", encoding="utf8") as f:
                    forced_transcpt = f.readlines()
                # Computing diff, removing punctuations
                sys.stdout.write("Pre-Process and computing diff between chapter and transcription\n")

                with open(self.procFolder + "/Alignments/" + str(
                        self.chapters[i][0]) + "/original.transcpt") as fh_original_transcpt:
                    original_transcpt = fh_original_transcpt.read()

                original_transcpt = re.sub(r"\d+-\d+-\d+ ?", "", original_transcpt, 0, re.I | re.M)
                # print(''.join(forced_transcpt))

                # Transforming to \n to an ascii char before removing punctuations
                forced_transcpt = re.sub(r"\n", "ğğğ ", ''.join(forced_transcpt), 0)

                # Removing punctuations -> not using the @staticmethod because it removes the tags and everything
                puncts = filter(lambda x: x not in ["<", ">", "-","'"], list(punctuation))
                forced_transcpt = re.sub(r"[" + re.escape(''.join(list(puncts))) + "]", "", forced_transcpt.upper(),
                                         0, re.I)

                # forced_transcpt = self.removePunctuations(forced_transcpt)

                # putting \n back
                forced_transcpt = re.sub(r"ğğğ", "\n", forced_transcpt, 0, re.I | re.M)

                # Before computing the diffs remove <\d+> NA <\d+>
                forced_transcpt = re.sub(r"<\d+> ?NA ?<\d+>", "", forced_transcpt, 0, re.I | re.M)

                #if not os.path.exists(soundFolder + "/diff_transcpt.html"):

                # Try to save at this stage for diffs after to see which parts are not re   ad
                with open(soundFolder + "/chapter.clean", "w", encoding="utf8") as fh:
                    fh.write(forced_transcpt)

                forced_transcpt = re.sub(r"\d+[ \n]|[ \n]\d+", "", forced_transcpt, 0, re.I)
                diffs = self.compute_diff(original_transcpt, forced_transcpt.upper(),
                                          fh_html=soundFolder + "/diff_transcpt.html")  # Great!
                """
				What do you need to keep in the diffs?
				Everything Removed: Put back in place
				Unchanged: Keep everything
				Added: Only tags and nothing else
				After the problam is gonna be tags that are empty? We can delete them after computing this
				"""

                add = ["<\d+>"]

                text = self.diffs_to_text(diffs, add)  # Good
                # Need to keep only tags and delete everything else
                result = re.sub(r"<(\d+)><\1>", "", text, 0)
                result = re.sub(r"<(\d+)>\n<\1>", "", result, 0)
                # Endtag and sent in nextline
                result = re.sub(r"<(\d+)>\n(.+?)<\1>", "\n<\\1>\\2<\\1>", result, 0, re.M)

                # Saving this result to soundFolder and working the rest of the pipeline from here
                with open(soundFolder + "/transcpt.clean", "w", encoding="utf8") as fh:
                    fh.write(result)

                with open(soundFolder + "/transcpt.clean", "r", encoding="utf8") as fh:
                    forced_transcpt = fh.readlines()

                """
				This is where the initial algorithm i proposed starts to change, instead determining places to BR
				i'm going to give the original text and decide after knowing the segments that are known
				"""
                text = ' '.join(forced_transcpt)
                text = re.sub(r"\n", "", text, 0)
                tuple_refs = re.findall(r"<(\d+)> ?(.+?) ?<\d+>", text)

                # Realigned but there are no <br> so it's the forced transcriptions text without any \n
                realigned = ""
                for tup in tuple_refs:
                    realigned += "<" + tup[0] + "> " + tup[1] + " <" + tup[0] + "> "

                # Save the realigned text file as transcription
                fh_transcpt = open(soundFolder + "/transcpt.txt", "w", encoding="utf8")
                puncts = filter(lambda x: x not in ["<", ">", "-"], list(punctuation))

                # To save the original for using with GIZA++
                realigned_original = realigned
                realigned = re.sub(r"[" + re.escape(''.join(list(puncts))) + "]", "", realigned.upper(), 0,
                                   re.I)
                fh_transcpt.write(realigned)
                fh_transcpt.close()

                ##SOUND FILE OPERATIONS and CALLING lowerquality/GENTLE from docker image
                # Calling sox to bring together all flac files for that chapter
                # sox  first_part.wav second_part.wav whole_part.wav
                sys.stdout.write("Sound file conversion \n")
                if not os.path.exists(soundFolder + "/" + str(self.chapters[i][0]) + ".flac"):
                    log = open(soundFolder + "/err_log.txt", "w")
                    cmd = "sox " + chapter_flacs_folder + "/*flac " + soundFolder + "/" + str(
                        self.chapters[i][0]) + ".flac"
                    command = Command(cmd, log)
                    command.run(timeout=40)
                # Save the realigned text file as transcription
                fh_transcpt = open(soundFolder + "/transcpt.txt", "w", encoding="utf8")
                puncts = filter(lambda x: x not in ["<", ">", "-"], list(punctuation))

                realigned_original = realigned
                realigned = re.sub(r"[" + re.escape(''.join(list(puncts))) + "]", "", realigned.upper(), 0,
                                   re.I)
                fh_transcpt.write(realigned)
                fh_transcpt.close()

                # Conversion du fichier vers .wav
                # soundconverter -b -m audio/x-flac -s .wav "total.flac"

                if not os.path.exists(soundFolder + "/" + str(self.chapters[i][0]) + ".wav"):
                    cmd = "soundconverter -b -m audio/x-flac -s .wav \"" \
                          + soundFolder + "/" + str(self.chapters[i][0]) + ".flac" + "\""
                    command = Command(cmd, log)
                    command.run(timeout=40)

                # Running Gentle
                # curl -F "audio=@./total.wav" -F "transcript=@./transcpt.txt" "http://localhost:32769/transcriptions?async=false" > sortie.txt


                wav_file = soundFolder + "/" + str(self.chapters[i][0]) + ".wav"
                transcpt_file = soundFolder + "/transcpt.txt"
                copyfile(transcpt_file, soundFolder + "/transcpt.regex.txt")

                os.system("perl -pi -e \"s/<\d+>//g\" " + soundFolder + "/transcpt.regex.txt")
                sys.stdout.write("Forced Alignment on audio/transcription\n")
                # Other regex in order to fix the number problems##
                if not os.path.exists(soundFolder + "/gentle.json"):
                    cmd = "curl -F \"audio=@" + wav_file + "\" -F \"transcript=@" + \
                          soundFolder + "/transcpt.regex.txt" + "\" \"http://localhost:32768/transcriptions?async=false\" > " \
                          + soundFolder + "/gentle.json"

                    command = Command(cmd, log)
                    command.run(timeout=999999)

                # Forced Alignment takes some time. Output is a json file
                sys.stdout.write("Assertion test for to see if the sound is recognized \n")
                data = loadJson(soundFolder + "/gentle.json")
                tab_transcpt = re.split(r" +", data['transcript'], 0)
                tab_transcpt = tab_transcpt[1:-1]
                try:
                    assert len(tab_transcpt) == len(data['words'])
                except AssertionError:
                    print(tab_transcpt,"\n"+str(len(tab_transcpt)))

                    print(data['words'],"\n"+str(len(data['words'])))
                    words = []
                    for item in(data['words']):
                        words.append(item['word'])


                    tokens_json = set(words)
                    difference_list = [x for x in tab_transcpt if x not in tokens_json]
                    print(difference_list) #This tokens shouldn't probably be in the transcription

                    raise AssertionError


                tokens_refs_file = re.split(r" +", realigned, 0)
                tokens_refs_file = tokens_refs_file[:-1]

                cpt_tokens = 0

                for y in range(len(tokens_refs_file)):
                    if not re.match(r"<\d+>", tokens_refs_file[y]):
                        cpt_tokens += 1


                # Assure that every one of these structures are the same length!
                # If there is an assertion error it means that the transcription does not correspond the audio file
                # Diff problems
                print(cpt_tokens, len(tab_transcpt), len(data['words']))
                sys.stdout.write("Computing second frames to cut \n")

                #Ungreedy
                try:
                    assert cpt_tokens == len(tab_transcpt)
                except AssertionError:  # If there is a problem than move on to the next chapter
                    raise AssertionError
                    #continue #Continue the loop if not greedy (will cause mismatchs)


                # Looping through tokens file to see where to cut
                # But before let's clear the beginning tags <\d+> tokens... (<\d+>)
                found = False
                for x in range(len(tokens_refs_file)):
                    if re.match(r"<\d+>", tokens_refs_file[x]) and not found:
                        found = True
                        tokens_refs_file[x] = ''
                    elif re.match(r"<\d+>", tokens_refs_file[x]) and found:
                        found = False
                # Delete the empty ones
                tokens_refs_file = list(filter(None, tokens_refs_file))

                for x in range(len(tokens_refs_file)):
                    if re.match(r"<\d+>", tokens_refs_file[x]):
                        tokens_refs_file[x - 1] += "<br>"
                        tokens_refs_file[x] = ""
                # Break indexes list has the index of the token that should be checked if it's aligned
                break_indexes = []
                tokens_refs_file = list(filter(None, tokens_refs_file))
                for y in range(len(tokens_refs_file)):
                    if re.search(r"<br>", tokens_refs_file[y]):
                        break_indexes.append(y)

                tab_seconds_to_cut = []  # After completing this list the previous algorithm could be used to cut files
                for index in break_indexes:
                    # print(tokens_refs_file[index],data['words'][index]['word'],data['words'][index]['case'])
                    if data['words'][index]['case'] == "success":
                        tab_seconds_to_cut.append(data['words'][index]['end'])

                    else:
                        # Means that the word to cut not recognized
                        print(data['words'][index]['word'], data['words'][index]['case'])
                        print(index)
                        right_left = 1
                        found = False
                        index_aligned = -1
                        while not found and right_left < 5:
                            try:
                                if data['words'][index + right_left]['case'] == "success":
                                    found = True
                                    index_aligned = index + right_left



                                elif data['words'][index - right_left]['case'] == "success":
                                    found = True
                                    index_aligned = index - right_left
                                right_left += 1
                            except IndexError:
                                break

                        if index_aligned == -1:
                            # If the word is still not recognized
                            continue
                            tab_seconds_to_cut.append(tab_seconds_to_cut[-1] + 2.5)
                        else:
                            tab_seconds_to_cut.append(data['words'][index_aligned]['end'])
                print(tab_seconds_to_cut)
                # SAME ALGORTIHM AS THE OLD _forceAlignments
                """
				Trimming all the sound files according to table that indicates
				the seconds to cut the sound file
				"""
                sys.stdout.write("Trimming the sound files \n")
                start = 0.0
                lastindex = -1
                for x in range(len(tab_seconds_to_cut)):
                    stop = tab_seconds_to_cut[x]
                    duration = stop - start
                    filename = soundFolder + "/" + str(x + 1) + ".wav"
                    cmd = "sox " + soundFolder + "/" + str(self.chapters[i][0]) + ".wav " \
                          + filename + " trim " + str(start) + " " + str(duration)
                    command = Command(cmd, log)
                    command.run(timeout=40)
                    start = stop
                    lastindex = x + 1

                # For adding the last segment until the end of the wav file
                lastindex = lastindex + 1
                filename = soundFolder + "/" + str(lastindex) + ".wav"
                cmd = "sox " + soundFolder + "/" + str(self.chapters[i][0]) + ".wav " \
                      + filename + " trim " + str(start)
                command = Command(cmd, log)
                command.run(timeout=40)
                """
				Reading french alignments for the same ids and scores that are associated
				"""
                french_assocs = {}
                scores = {}
                with open(self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/reversed_stem_lc_regex.txt",
                          encoding="utf8") as f:
                    for line in f:
                        associations = re.findall(r"<(\d+)> ?(.+?) ?<\d+>", line.strip(), 0)
                        try:
                            french_assocs[associations[0][0]] = "<" + str(associations[0][0]) + "> " + associations[0][
                                1] + " <" + str(associations[0][0]) + ">"
                        except IndexError:
                            pass
                with open(self.procFolder + "/Alignments/" + str(
                        self.chapters[i][0]) + "/scores.txt", encoding="utf8") as f:
                    for line in f:
                        score = re.findall(r"<(\d+)>(.+?)<\d+>", line.strip())

                        scores[score[0][0]] = score[0][1]

                # Charging the aligned sentences to write the sentences with punctuation
                aligned_with_puncts = {}
                with open(self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/reversed_stem_ls.txt",
                          "r", encoding="utf8") as fh:
                    reversed_stem = fh.readlines()
                for line in reversed_stem:
                    sent = re.search(r"<(\d+)> +(.+?) +<\d+>", line.strip(), re.I)
                    if sent:
                        aligned_with_puncts[sent.group(1)] = "<" + str(sent.group(1)) + "> " + sent.group(
                            2) + " <" + str(sent.group(1)) + "> "

                fh_final = open(self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/final.txt", "w",
                                encoding="utf8")
                # Read transcpt file
                with open(soundFolder + "/transcpt.txt", "r", encoding="utf8") as fh:
                    transcpt = fh.read()

                alignments = []
                tags = re.findall(r"<(\d+)> +(.+?) +<\d+>", transcpt, 0)

                for x in range(len(tags)):
                    informations = {}
                    (id, sent_transcpt) = str(tags[x][0]), tags[x][1]
                    informations['score'] = scores[id]
                    informations['transcpt'] = sent_transcpt
                    try:
                        informations['original_sent'] = aligned_with_puncts[id]
                    except KeyError:
                        informations['original_sent'] = "NA"
                    informations['french_sent'] = french_assocs[id]
                    informations['identifier'] = str(self.book_id) + "-" \
                                                 + str(self.chapters[i][0]) + "-" + str(x).zfill(4)
                    alignments.append(informations)

                # Now write to final
                for x in range(len(alignments)):
                    fh_final.write(
                        "<" + alignments[x]['identifier'] + "> " + alignments[x]['transcpt'] + " <" + alignments[x][
                            'identifier'] + ">\t"
                        + alignments[x]['original_sent'] + "\t" + alignments[x]['french_sent'] + "\t" + alignments[x][
                            'score'] + "\n")
                    # Changing the file names of wav files on the soundFolder to associate with the id tags of each sent

                    tab_files = os.listdir(soundFolder)
                    # Filter the tab to match only wav files that are newly created
                    tab_files = filter(lambda x: x.endswith("wav") and re.match(r"\d\d?\d?\.", x), tab_files)

                    # Sort nicely the files table and rename them with the corresponding
                    # identifier
                    try:
                        copyfile(soundFolder + "/" + self.sorted_nicely(list(tab_files))[x]
                                 , soundFolder + "/" + alignments[x]['identifier'] + ".wav")
                    except IndexError:
                        pass

                # Deleting temporary sound files

                tab_files = os.listdir(soundFolder)

                tab_files = list(filter(lambda x: x.endswith("wav") and re.match(r"\d\d?\d?\.", x), tab_files))

                files_count = len(tab_files)

                # print(tab_files)

                # print(list(tab_files))
                for file in list(tab_files):
                    # print(soundFolder+"/"+file)
                    os.remove(soundFolder + "/" + file)

                # Make sure that everything is allright
                try:
                    # print(files_count)
                    # print(wc(self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/final.txt"))
                    assert files_count == wc(
                        self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/final.txt")
                except AssertionError:
                    pass
                # raise PlusOneMinusOneError

                """
				At this stage if assert valids that file numbers, line counts, etc are correct => Next step is
				to determine sent segments that are not read. If it's a complete sentence, regular expression erases the sent
				but if it's the end of a full sent, beginning or worse (in the middle ) or even just a word subtitution, in
				the translation we find the translation of a text that the signal is not read.
				"""

                if not exclude_word_alignments:

                    # Computing the diff again in between <transcpt.txt> <=> <chapter.clean> (soundFolder)
                    with open(soundFolder + "/transcpt.txt", "r", encoding="utf8") as fh:
                        textA = fh.read()

                    with open(soundFolder + "/chapter.clean", "r", encoding="utf8") as fh:
                        textB = fh.read()

                    diffs = self.compute_diff(textA, textB)
                    # Well take only added and 0
                    text = ""
                    for tupl in diffs:
                        if tupl[0] == 0:
                            txt = re.sub(r"[^<\d+>]", "", tupl[1], 0)
                            text += txt
                        elif tupl[0] == 1:
                            text += tupl[1]

                    # print(text)
                    # This diff leaves us with only tags and text added to the transcript. All opened and closed tags
                    # should be exluded.
                    # 1st step : remove \n
                    text = re.sub(r"\n", "", text, 0, re.M)
                    # 2nd : remove all open closed simple tags
                    text = re.sub(r"<(\d+)> ?<\1>", "", text, 0, re.M)
                    text = re.sub(r"<(\d+)> +<\1>", "", text, 0, re.M)

                    tags = re.findall(r"<(\d+)>(.+?)<\d+>", text)
                    # Remove punctuation from tuple[1] and if it's emtpy means just a punctuation so exclude
                    tags_modified = []
                    for tag in tags:
                        tags_modified.append([tag[0], self.removePunctuations(tag[1])])

                    # Exlude the tags that are not found in the transcpt txt
                    alltags = re.findall(r"<(\d+)>", textA)

                    tags = []
                    for mod in tags_modified:
                        if len(mod[1]) <= 1:
                            pass
                        # Ne fait rien
                        else:
                            if mod[0] in set(alltags):
                                tags.append([mod[0], ' '.join(mod[1])])
                    # Tags contain lists (id,part of the text) which is cut in the audio file

                    # Extract GIZA sent alignments for the book if it's not already done

                    if not os.path.exists(self.procFolder + "/giza/giza.assocs"):
                        self.extractGIZAsentAlignments("../GIZA/15.05.2017_2")

                    # Read the final_file
                    with open(self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/final.txt", "r",
                              encoding="utf8") as fh:
                        final_file = fh.readlines()

                    fh_temp = open(self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/final_temp.txt", "w",
                                   encoding="utf8")
                    # This is where it gets a little more complicated. So we have the sentence that is cut and we extracted
                    # the word alignments. Before deciding where to cut | should be cut or not, let's extract these sents


                    for tag in tags:
                        # Tag[0] -> sent id , tag[1] -> sent that was cut
                        if self.getWordAlignment(self.chapters[i][0], tag[0], tag[1]):

                            cut_sent = self.getWordAlignment(self.chapters[i][0], tag[0], tag[1])

                            # Sent updated with <del> tags
                            # Find in the final alignment file the tag <tag[0]> and change the text with <del>
                            # print(cut_sent)
                            for line in final_file:
                                if re.search(r"<" + tag[0] + ">", line, 0):
                                    sent_info = re.search(r"(.+?)\t(.+?)\t(.+?)\t(.+?)\n", line)
                                    cut_sent = re.sub(r"__del__", "<del>", cut_sent.strip(), 0)
                                    cut_sent = re.sub(r"__\/del__", "</del>", cut_sent.strip(), 0)
                                    cut_sent = re.sub(r"\n", "", cut_sent, 0)
                                    newLine = sent_info.group(1) + "\t" + sent_info.group(
                                        2) + "\t" + cut_sent.strip() + "\t" + sent_info.group(4) + "\n"
                                    fh_temp.write(newLine)
                                else:
                                    fh_temp.write(line)
                    fh_temp.close()

                    # Rename the temporary files as the original
                    os.rename(self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/final_temp.txt",
                              self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/final.txt")

    # OLD -> Completing sentences
    def _forceAlignments(self):
        """
		Gentle: Robust yet lenient forced-aligner built on Kaldi.
		A tool for aligning speech with text.

		Input: Forced transcription file coming from mwerAlign.
		18.05.2017: Change: Adding a diff between transcriptions and original transcpt
		:return:
		"""
        # For each chapter that is aligned
        for i in range(len(self.chapters)):
            # If the chapter is in dev/test it's not aligned with mwerAlign
            if self.alignedChapters[i] and self.chapters[i][3] not in self.corpus_dev:

                """
				if self.chapters[i][0] != 123441:
					continue
				"""
                soundFolder = self.procFolder + "/gentle/" + str(self.chapters[i][0])

                # Forced transcription file
                transcpt_path = self.procFolder + "/Alignments/" \
                                + str(self.chapters[i][0]) + "/transcriptions_aligned.txt"
                with open(transcpt_path, "r", encoding="utf8") as f:
                    forced_transcpt = f.readlines()

                # Creating audio manipulations folder
                if not os.path.exists(self.procFolder + "/gentle"):
                    os.mkdir(self.procFolder + "/gentle")
                if not os.path.exists(self.procFolder + "/gentle/" + str(self.chapters[i][0])):
                    os.mkdir(self.procFolder + "/gentle/" + str(self.chapters[i][0]))

                """
				Applying the same method before calling wordAlignments class
				Each line corresponds to a transcription file, delimiter is \n
				closed linebreaks []: Shows transcription lines that finishes at the same time as the sent split
				transcpts []: Each segment that corresponds to an alignment. A <br> in a
				sentence means that it's cut -> therefore should bring together the audio file
				"""

                # Computing diff, removing punctuations

                with open(self.procFolder + "/Alignments/" + str(
                        self.chapters[i][0]) + "/original.transcpt") as fh_original_transcpt:
                    original_transcpt = fh_original_transcpt.read()

                original_transcpt = re.sub(r"\d+-\d+-\d+ ?", "", original_transcpt, 0, re.I | re.M)
                # print(''.join(forced_transcpt))

                # Transforming to \n to an ascii char before removing punctuations
                forced_transcpt = re.sub(r"\n", "ğğğ ", ''.join(forced_transcpt), 0)

                # Removing punctuations -> not using the @staticmethod because it removes the tags and everything
                puncts = filter(lambda x: x not in ["<", ">", "-"], list(punctuation))
                forced_transcpt = re.sub(r"[" + re.escape(''.join(list(puncts))) + "]", "", forced_transcpt.upper(), 0,
                                         re.I)

                # forced_transcpt = self.removePunctuations(forced_transcpt)

                # putting \n back
                forced_transcpt = re.sub(r"ğğğ", "\n", forced_transcpt, 0, re.I | re.M)

                # Before computing the diffs remove <\d+> NA <\d+>
                forced_transcpt = re.sub(r"<\d+> ?NA ?<\d+>", "", forced_transcpt, 0, re.I | re.M)

                # Try to save at this stage for diffs after to see which parts are not read
                with open(soundFolder + "/chapter.clean", "w", encoding="utf8") as fh:
                    fh.write(forced_transcpt)

                diffs = self.compute_diff(original_transcpt, forced_transcpt.upper(),
                                          fh_html=soundFolder + "/diff_transcpt.html")  # Great!
                """
				What do you need to keep in the diffs?
				Everything Removed: Put back in place
				Unchanged: Keep everything
				Added: Only tags and nothing else
				After the problam is gonna be tags that are empty? We can delete them after computing this
				"""
                add = ["<\d+>"]
                text = self.diffs_to_text(diffs, add)  # Good
                # Need to keep only tags and delete everything else
                result = re.sub(r"<(\d+)><\1>", "", text, 0)
                result = re.sub(r"<(\d+)>\n<\1>", "", result, 0)
                # Endtag and sent in nextline
                result = re.sub(r"<(\d+)>\n(.+?)<\1>", "\n<\\1>\\2<\\1>", result, 0, re.M)

                # Saving this result to soundFolder and working the rest of the pipeline from here
                with open(soundFolder + "/transcpt.clean", "w", encoding="utf8") as fh:
                    fh.write(result)

                with open(soundFolder + "/transcpt.clean", "r", encoding="utf8") as fh:
                    forced_transcpt = fh.readlines()

                # Finding all of closed sentences followed by a linebreak
                closed_linebreaks = re.findall(r"<(\d+)> ?\n", ' '.join(forced_transcpt), re.I)

                # Finding a proper segmentation: All of the sound files are brought together
                # and then splitted when there is a <br>

                text = ' '.join(forced_transcpt)
                text = re.sub(r"\n", "<br>", text, 0)
                tuple_refs = re.findall(r"<(\d+)> ?(.+?) ?<\d+>", text)
                """
				In order to do the alignments per sent_split, putting a <br> at the end of each ref is sufficient
				"""
                # <br> as sent split
                """
				sent_split = [(re.sub(r'<br>',"",x[1],re.M)) for x in tuple_refs]
				sent_split = [x+"<br>" for x in sent_split]
				tuple_refs_modified = []
				for x in range(len(tuple_refs)):
					tuple_refs_modified.append([tuple_refs[x][0],sent_split[x]])
				"""

                realigned = ""
                # for tup in tuple_refs: <-- Completing sentences
                for tup in tuple(tuple_refs):
                    if re.search(r"<br>", tup[1]):
                        result = re.sub(r"<br>", "", tup[1], 0)
                        realigned += ("<" + tup[0] + "> " + result + " <" + tup[0] + ">" + "<br>")
                    elif tup[0] in closed_linebreaks:  # Is this actually a good idea?
                        realigned += ("<" + tup[0] + "> " + tup[1] + " <" + tup[0] + ">" + "<br>")
                    # realigned += ("<" + tup[0] + "> " + tup[1] + " <" + tup[0] + ">")

                    else:
                        realigned += ("<" + tup[0] + "> " + tup[1] + " <" + tup[0] + ">")

                chapter_flacs_folder = self.procFolder + "/data/" + str(self.chapters[i][0])

                # Calling sox to bring together all flac files for that chapter
                # sox  first_part.wav second_part.wav whole_part.wav

                if not os.path.exists(soundFolder + "/" + str(self.chapters[i][0]) + ".flac"):
                    log = open(soundFolder + "/err_log.txt", "w")
                    cmd = "sox " + chapter_flacs_folder + "/*flac " + soundFolder + "/" + str(
                        self.chapters[i][0]) + ".flac"
                    command = Command(cmd, log)
                    command.run(timeout=40)

                # Save the realigned text file as transcription
                fh_transcpt = open(soundFolder + "/transcpt.txt", "w", encoding="utf8")
                puncts = filter(lambda x: x not in ["<", ">", "-"], list(punctuation))

                realigned_original = realigned
                realigned = re.sub(r"[" + re.escape(''.join(list(puncts))) + "]", "", realigned.upper(), 0, re.I)
                fh_transcpt.write(realigned)
                fh_transcpt.close()

                # Conversion du fichier vers .wav
                # soundconverter -b -m audio/x-flac -s .wav "total.flac"
                if os.path.exists(soundFolder + "/err_log.txt"):
                    log = open(soundFolder + "/err_log.txt", "a")
                else:
                    log = open(soundFolder + "/err_log.txt", "w")

                if not os.path.exists(soundFolder + "/" + str(self.chapters[i][0]) + ".wav"):
                    cmd = "soundconverter -b -m audio/x-flac -s .wav \"" \
                          + soundFolder + "/" + str(self.chapters[i][0]) + ".flac" + "\""
                    command = Command(cmd, log)
                    command.run(timeout=40)

                # Running Gentle
                # curl -F "audio=@./total.wav" -F "transcript=@./transcpt.txt" "http://localhost:32769/transcriptions?async=false" > sortie.txt
                if os.path.exists(soundFolder + "/err_log.txt"):
                    log = open(soundFolder + "/err_log.txt", "a")
                else:
                    log = open(soundFolder + "/err_log.txt", "w")

                wav_file = soundFolder + "/" + str(self.chapters[i][0]) + ".wav"
                transcpt_file = soundFolder + "/transcpt.txt"
                copyfile(transcpt_file, soundFolder + "/transcpt.regex.txt")

                os.system("perl -pi -e \"s/<\d+>//g\" " + soundFolder + "/transcpt.regex.txt")
                if not os.path.exists(soundFolder + "/gentle.json"):
                    cmd = "curl -F \"audio=@" + wav_file + "\" -F \"transcript=@" + \
                          soundFolder + "/transcpt.regex.txt" + "\" \"http://localhost:32768/transcriptions?async=false\" > " \
                          + soundFolder + "/gentle.json"

                    command = Command(cmd, log)
                    command.run(timeout=999999)

                # Forced Alignment takes some time. Output is a json file
                data = loadJson(soundFolder + "/gentle.json")
                # print(data['words'][0]) -> Each word
                tab_transcpt = re.split(r"[ -]", data['transcript'])

                tab_seconds_to_cut = []
                # Search for the word before the <br>
                for x in range(len(data['words'])):
                    if data['words'][x]['word'] == "BR":
                        # print(data['words'][x-1]['word'])
                        # if it's aligned push the second that the word ends to list
                        if data['words'][x - 1]['case'] == "success":
                            print(data['words'][x - 1]['word'], data['words'][x - 1]['end'])
                            tab_seconds_to_cut.append(data['words'][x - 1]['end'])
                        else:
                            # If the word before <br> isn't aligned, search for the closest
                            # word which is recognized
                            # print(data['words'][x - 1]['word'])
                            pos_closest = self.findClosestAligned(data, x - 1)
                            if pos_closest != -1:  # Make sure that it's sucessfuly aligned and push to list
                                assert data['words'][pos_closest]['case'] == "success"
                                tab_seconds_to_cut.append(data['words'][pos_closest]['end'])
                            # raise PlusOneMinusOneError

                print(tab_seconds_to_cut)
                """
				Trimming all the sound files according to table that indicates
				the seconds to cut the sound file
				"""
                start = 0.0
                lastindex = -1
                for x in range(len(tab_seconds_to_cut)):
                    stop = tab_seconds_to_cut[x]
                    duration = stop - start
                    filename = soundFolder + "/" + str(x + 1) + ".wav"
                    cmd = "sox " + soundFolder + "/" + str(self.chapters[i][0]) + ".wav " \
                          + filename + " trim " + str(start) + " " + str(duration)
                    command = Command(cmd, log)
                    command.run(timeout=40)
                    start = stop
                    lastindex = x + 1

                # For adding the last segment until the end of the wav file
                lastindex = lastindex + 1
                filename = soundFolder + "/" + str(lastindex) + ".wav"
                cmd = "sox " + soundFolder + "/" + str(self.chapters[i][0]) + ".wav " \
                      + filename + " trim " + str(start)
                command = Command(cmd, log)
                command.run(timeout=40)

                """
				Reading french alignments for the same ids and scores that are associated
				"""
                french_assocs = {}
                scores = {}
                with open(self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/reversed_stem_lc_regex.txt",
                          encoding="utf8") as f:
                    for line in f:
                        associations = re.findall(r"<(\d+)> ?(.+?) ?<\d+>", line.strip(), 0)
                        french_assocs[associations[0][0]] = associations[0][1]
                with open(self.procFolder + "/Alignments/" + str(
                        self.chapters[i][0]) + "/scores.txt", encoding="utf8") as f:
                    for line in f:
                        score = re.findall(r"<(\d+)>(.+?)<\d+>", line.strip())

                        scores[score[0][0]] = score[0][1]

                fh_final = open(self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/final.txt", "w",
                                encoding="utf8")
                realigned_original = realigned_original.split("<br>")
                for x in range(0, len(realigned_original) - 1):
                    tags = re.findall(r"<(\d+)> (.+?) ?<\d+>", realigned_original[x].strip())
                    score_tab = []
                    for tag in tags:
                        score_tab.append(float(scores[tag[0]]))
                    sent_mean = mean(score_tab)

                    identifier = str(self.book_id) + "-" \
                                 + str(self.chapters[i][0]) + "-" + str(x).zfill(4)

                    # print(identifier, sent_mean, realigned_original[x])
                    """
					Identifier = book-id - chapter_id - sent_id
					sent_mean = la score moyenne de l'alignement (scores de hunalign)
					realigned_original = Text anglais avec l'alignement qui correspond
					aux fichier recoupés (réaligné pour qu'il n'y a pas de coupure au milieu d'une phrase
					french_assocs = {} Les alignements en français  key: str(phrase_id) value: str
					phrase en français
					"""
                    french_sent = ""
                    for tag in tags:
                        french_sent += "<" + tag[0] + "> " + french_assocs[tag[0]] + " <" + tag[0] + "> "

                    id_tags = "<" + identifier + ">"

                    fh_final.write(id_tags + " " + realigned_original[x] + " " + id_tags
                                   + "\t" + realigned_original[x] + "\t" +
                                   french_sent + "\t" + str(sent_mean) + "\n")

                    tab_files = os.listdir(soundFolder)
                    # Filter the tab to match only wav files that are newly created
                    tab_files = filter(lambda x: x.endswith("wav") and re.match(r"\d\d?\d?\.", x), tab_files)

                    # Make sure that the final alignment files line count == count of the sound files
                    # assert len(list(tab_files)) == wc(self.procFolder+"/Alignments/"+str(self.chapters[i][0])+"/final.txt")

                    # Sort nicely the files table and rename them with the corresponding
                    # identifier
                    try:
                        copyfile(soundFolder + "/" + self.sorted_nicely(list(tab_files))[x]
                                 , soundFolder + "/" + identifier + ".wav")
                    except IndexError:
                        pass
                    # Delete the files after the loop is finished

                # Deleting temporary sound files

                tab_files = os.listdir(soundFolder)

                tab_files = list(filter(lambda x: x.endswith("wav") and re.match(r"\d\d?\d?\.", x), tab_files))

                files_count = len(tab_files)

                print(tab_files)

                print(list(tab_files))
                for file in list(tab_files):
                    # print(soundFolder+"/"+file)
                    os.remove(soundFolder + "/" + file)

                # Make sure that everything is allright
                try:
                    print(files_count)
                    print(wc(self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/final.txt"))
                    assert files_count == wc(self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/final.txt")
                except AssertionError:
                    pass
                # raise PlusOneMinusOneError

                """
				At this stage if assert valids that file numbers, line counts, etc are correct => Next step is
				to determine sent segments that are not read. If it's a complete sentence, regular expression erases the sent
				but if it's the end of a full sent, beginning or worse (in the middle ) or even just a word subtitution, in
				the translation we find the translation of a text that the signal is not read.
				"""

                # Computing the diff again in between <transcpt.txt> <=> <chapter.clean> (soundFolder)
                with open(soundFolder + "/transcpt.txt", "r", encoding="utf8") as fh:
                    textA = fh.read()

                with open(soundFolder + "/chapter.clean", "r", encoding="utf8") as fh:
                    textB = fh.read()

                diffs = self.compute_diff(textA, textB)
                # Well take only added and 0
                text = ""
                for tupl in diffs:
                    if tupl[0] == 0:
                        txt = re.sub(r"[^<\d+>]", "", tupl[1], 0)
                        text += txt
                    elif tupl[0] == 1:
                        text += tupl[1]

                # print(text)
                # This diff leaves us with only tags and text added to the transcript. All opened and closed tags
                # should be exluded.
                # 1st step : remove \n
                text = re.sub(r"\n", "", text, 0, re.M)
                # 2nd : remove all open closed simple tags
                text = re.sub(r"<(\d+)> ?<\1>", "", text, 0, re.M)
                text = re.sub(r"<(\d+)> +<\1>", "", text, 0, re.M)

                tags = re.findall(r"<(\d+)>(.+?)<\d+>", text)
                # Remove punctuation from tuple[1] and if it's emtpy means just a punctuation so exclude
                tags_modified = []
                for tag in tags:
                    tags_modified.append([tag[0], self.removePunctuations(tag[1])])

                # Exlude the tags that are not found in the transcpt txt
                alltags = re.findall(r"<(\d+)>", textA)

                tags = []
                for mod in tags_modified:
                    if len(mod[1]) <= 1:
                        pass
                    # Ne fait rien
                    else:
                        if mod[0] in set(alltags):
                            tags.append([mod[0], ' '.join(mod[1])])
                # Tags contain lists (id,part of the text) which is cut in the audio file

                # Extract GIZA sent alignments for the book if it's not already done

                if not os.path.exists(self.procFolder + "/giza/giza.assocs"):
                    self.extractGIZAsentAlignments("../GIZA/15.05.2017_2")

                # This is where it gets a little more complicated. So we have the sentence that is cut and we extracted
                # the word alignments. Before deciding where to cut | should be cut or not, let's extract these sents
                for tag in tags:
                    # Tag[0] -> sent id , tag[1] -> sent that was cut
                    self.getWordAlignment(self.chapters[i][0], tag[0], tag[1])

    def finalAlignment(self):
        for i in range(len(self.chapters)):
            if self.alignedChapters[i] and self.chapters[i][3] not in self.corpus_dev:
                print("Corpus not dev passing")
                copyfile(self.procFolder + "/data/" + str(self.chapters[i][0])
                         + "/" + str(self.chapters[i][2]) + "-" + str(self.chapters[i][0]) + ".trans.txt",
                         self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/original.transcpt")
                continue
                # Aligned Transcriptions
                print("********CHAPTER*********" + str(self.chapters[i][0]) + "***********************")
                fh_aligned = open(self.procFolder + "/Alignments/" + str(self.chapters[i][0]) \
                                  + "/transcriptions_aligned.txt", "r", encoding="utf8")

                fh_lc = open(self.procFolder + "/Alignments/" + str(self.chapters[i][0]) \
                             + "/reversed_stem_lc_regex.txt", "r", encoding="utf8")

                copyfile(self.procFolder + "/data/" + str(self.chapters[i][0])
                         + "/" + str(self.chapters[i][2]) + "-" + str(self.chapters[i][0]) + ".trans.txt",
                         self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/original.transcpt")

                lc = OrderedDict()
                tab_lc = fh_lc.readlines()
                for line in tab_lc:
                    line = line.strip()
                    infos = re.search(r"<(\d+)> ?(.+?) ?<\d+>", line, re.I)
                    if infos:
                        lc[str(infos.group(1))] = infos.group(2)

                fh_lc.close()

                aligned = fh_aligned.read()
                fh_aligned.close()

                ## ?? Pourquoi boucler sur les transcriptions originales ? ? ?  ?? ? ? ? ?? ? ?
                transcription_file = self.procFolder + "/Alignments/" + \
                                     str(self.chapters[i][0]) + "/transcriptions_aligned.txt"

                fh_transcpt = open(transcription_file, "r", encoding="utf8")

                transcpt = fh_transcpt.read()
                fh_transcpt.close()
                transcpt = re.sub(r"\n", "ğ", transcpt, 0, re.I | re.DOTALL)

                # Finding all of closed sentences followed by a linebreak
                closed_linebreaks = re.findall(r"<(\d+)> ?ğ", transcpt, re.I)

                transcpts = re.findall(r"<\d+> ?(.+?) ?<\d+>", transcpt, re.I)

                fh_sortie = open(self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/cut.txt", "w",
                                 encoding="utf8")

                for key in range(len(transcpts) - 1):
                    # print("<"+str(key)+"> " + transcpts[key]+ " <"+str(key)+">")
                    if not re.search(r"ğ", transcpts[key], re.I):

                        pass
                        ###Problem is here how do we know when to make a \n?
                        if str(key) in closed_linebreaks:
                            inx = closed_linebreaks.index(str(key))
                            del closed_linebreaks[inx]
                            fh_sortie.write("<" + str(key) + "> " + lc[str(key)] + " <" + str(key) + ">\n")
                        else:
                            fh_sortie.write("<" + str(key) + "> " + lc[str(key)] + " <" + str(key) + "> ")
                        # print(transcpts[key],lc[str(key)])
                    else:
                        print("------" + str(key) + "--------")

                        alignedTag = re.sub(r"ğ", "ğ ", transcpts[key], 0, re.I)
                        id = str(str(self.book_id) + "-" + str(self.chapters[i][0]) + "-" + str(key))
                        # print(id)
                        print(alignedTag)
                        # old =>
                        # alignObject = WordAlignments(alignedTag, id,self.procFolder+"/Alignments/"+str(self.chapters[i][0])+"/giza.assocs.txt",lc)
                        # new =>
                        alignObject = WordAlignments(alignedTag, id, self.procFolder + "/giza", lc)
                        cut = alignObject.getTargetSentence()
                        for c in range(len(cut) - 1):
                            fh_sortie.write("<" + str(key) + "> " + cut[c] + " <" + str(key) + ">\n")
                        if str(key) not in closed_linebreaks:
                            fh_sortie.write("<" + str(key) + "> " + cut[-1] + " <" + str(key) + "> ")
                        else:
                            fh_sortie.write("<" + str(key) + "> " + cut[-1] + " <" + str(key) + ">\n")
                            inx = closed_linebreaks.index(str(key))
                            del closed_linebreaks[inx]
                # print(closed_linebreaks)

                fh_sortie.close()

                # print("\nAssociating speeech to translations")

                fh_original = open(self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/original.transcpt",
                                   "r", encoding="utf8")
                original = fh_original.readlines()

                transcpt_original = {}
                for line in original:
                    line = line.strip()
                    searchObj = re.search(r"\d+-\d+-(\d+) ?(.*)", line, re.I)
                    if searchObj:
                        transcpt_original[searchObj.group(1)] = searchObj.group(2)

                fh_ls_aligned = open(
                    self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/transcriptions_aligned.txt")
                fh_cut = open(self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/cut.txt")
                ls_aligned = fh_ls_aligned.readlines()
                cut = fh_cut.readlines()
                final = open(self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/final.txt",
                             "w", encoding="utf8")
                for x in range(len(ls_aligned)):
                    id_transcpt = "<" + str(self.book_id) + "-" + str(self.chapters[i][0]) + "-" + str(x).zfill(
                        4) + "> "

                    try:
                        numbers = re.findall(r"<(\d+)>.+?<\d+>", cut[x], re.I)
                        try:
                            text_transcpt = transcpt_original[str(x).zfill(4)]
                        except KeyError:
                            text_transcpt = ""
                        sent_score = computeScoreforSent(numbers, self, self.chapters[i][0])
                        final.write(
                            id_transcpt + text_transcpt + " " + id_transcpt + "\t" + ls_aligned[x].strip() + "\t" + cut[
                                x].strip() + "\t" + str(sent_score) + "\n")
                    except IndexError or KeyError:
                        pass

                """
				sys.exit("Restart")

				#Original transcriptions
				# Processing the transcription files for mwerAlign

				transcription_file = self.procFolder + "/data/" + \
				                     str(self.chapters[i][0]) + "/" + \
				                     str(self.chapters[i][2]) + "-" + str(self.chapters[i][0]) + ".trans.txt"

				fh_transcpt = open(transcription_file, "r", encoding="utf8")

				transcriptions = OrderedDict()
				transcr_str = ""
				for line in fh_transcpt:
					line = line.strip()
					searchObj = re.search(r'\d+-\d+-(\d+) (.+?)$', line, re.I)
					transcriptions[searchObj.group(1)] = [searchObj.group(2)]
					transcr_str += searchObj.group(2).lower() + "\n"

				fh_transcpt.close()

				aligned = re.sub(r"\n","ğ",aligned,0,re.I)
				fh_sortie = open(self.procFolder+"/Alignments/"+str(self.chapters[i][0])+"/cut.txt","w",encoding="utf8")
				for k,v in transcriptions.items():
					print(k,v)

				sys.exit("stop")
				for key,values in transcriptions.items():
					searchObj = re.search(r"<"+str(round(int(key)))+"> ?(.+?) <"+str(round(int(key)))+">",aligned,re.I)
					if searchObj:
						alignedTag = searchObj.group(1)
						if 'ğ' not in alignedTag:
							fh_sortie.write("<"+str(round(int(key)))+"> "+ lc[str(round(int(key)))]+" <"+str(round(int(key)))+"> ")
						else:
							pass
							#beforeNAfter =alignedTag.split("ğ")
							#print(key)
							id = str(str(self.book_id)+"-"+str(self.chapters[i][0])+"-"+str(round(int(key))))
							#align_target_sent_words(beforeNAfter,id)
							alignedTag2 = re.sub(r"ğ","ğ ", alignedTag, 0 ,re.I)

							print(key)
							#print(alignedTag2)
							alignObject = WordAlignments(alignedTag2,id)

							cut = alignObject.getTargetSentence()
							for c in cut:
								fh_sortie.write(
									"<" + str(round(int(key))) + "> " + c + " <" + str(
										round(int(key))) + ">")
					else:
						print("There might be a problem!")

				print(transcriptions)
				"""

    def final_db_Integration(self):
        for i in range(len(self.chapters)):
            if self.alignedChapters[i]:
                sys.stdout.write("Getting the final result for chapter: " + str(self.chapters[i][0])+"\t"
                                                                "Book: "+str(self.book_id)+"\n")
                if self.chapters[i][0] in self.exceptions:
                    sys.stdout.write("Book in the exceptions list: Passing\n")
                    continue
                try:
                    fh_final = open(self.procFolder + "/Alignments/"
                                    + str(self.chapters[i][0]) + "/final.txt", "r", encoding="utf8")
                except FileNotFoundError:
                    continue
                final = fh_final.readlines()

                for x in range(len(final)):
                    final[x] = final[x].strip()
                    alignmnts = final[x].split("\t")
                    print(alignmnts)

                    id_sent = re.search(r"\d+-\d+-(\d+)", alignmnts[0], re.I)
                    seg_source = re.sub(r"<\d+>", "", alignmnts[1], 0, re.I)
                    seg_cible = re.sub(r"<\d+>", "", alignmnts[2], 0, re.I)
                    transcpt = re.sub(r"<.+?>", "", alignmnts[0], 0, re.I)

                    if self.chapters[i][3] in self.corpus_dev:
                        try:
                            audio_filename = str(self.chapters[i][2]) + "-" + str(
                                self.chapters[i][0]) + "-" + id_sent.group(1)
                        except AttributeError:
                            continue
                    else:
                        audio_filename = str(self.book_id) + "-" + str(self.chapters[i][0]) + "-" + id_sent.group(1)

                    DB_infos = dict(
                        audio_filename=audio_filename,
                        book_id=self.book_id,
                        chapter_id=self.chapters[i][0],
                        sentence_number=id_sent.group(1),
                        transcription=transcpt,
                        seg_source=seg_source,
                        seg_cible=seg_cible,
                        alignment_score=alignmnts[3]
                    )
                    DB = self.getDB_dataset("alignements")
                    DB.insert(DB_infos)

                ###
                # https://img.shields.io/badge/OCR-1-red.svg

    # Not in use anymore#
    def verifyAlignments(self):
        exceptionList = list(punctuation)
        for i in range(len(self.chapters)):
            if (self.alignedChapters[i]) and self.chapters[i][3] not in self.corpus_dev:
                # 1st Copy the transcription file to Alignments folder
                if not os.path.exists(self.procFolder + "/Alignments/" + str(
                        self.chapters[i][0]) + "/original.transcpt"):
                    copyfile(self.procFolder + "/data/" + str(self.chapters[i][0]) + "/"
                             + str(self.chapters[i][2]) + "-" + str(self.chapters[i][0]) + ".trans.txt",
                             self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/original.transcpt")

                # Read the alignments generated after mwerAlign and the original transcript
                fh_original = open(self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/original.transcpt")
                fh_mwer = open(self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/forcedAlignment2.txt")

                # Filehandles & Reading files
                mwer = fh_mwer.readlines()
                original = fh_original.readlines()

                # Asserting that these two files have the equal amount of lines
                assert len(mwer) - 1 == len(original)

                # Creating the data structure
                transcriptions = OrderedDict()
                transcr_str = ""
                for j in range(len(original)):
                    original[j] = original[j].strip()
                    searchObj = re.search(r'(\d+-\d+-\d+) (.+?)$', original[j], re.I)
                    transcriptions[searchObj.group(1)] = [searchObj.group(2), mwer[j]]
                    transcr_str += searchObj.group(2).lower() + "\n"
                sortie = open(self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/aligned.txt", "w",
                              encoding="utf8")
                for key, values in transcriptions.items():

                    sys.stdout.write(str(key) + "\t" + values[0].lower() + "\t" + values[1].lower() + "\n")
                    # Tokenize both sentences and see the difference between lists
                    tokenizer = TreebankWordTokenizer()
                    tokens_original = tokenizer.tokenize(values[0].lower())
                    tokens_mwer = tokenizer.tokenize(values[1].lower())

                    difference = [item for item in tokens_mwer if item not in tokens_original
                                  and item not in list(punctuation) and not item.isnumeric()
                                  and not re.search(r"^[ivxldc]+\.?$", item, re.I)]

                    for token in difference:
                        if "-" in token:
                            twoparts = token.split("-")
                            if twoparts[0] and twoparts[1] in tokens_original:
                                difference.remove(token)
                        if re.search(r"'\w+", token, re.I):
                            difference.remove(token)


                        # In order to erase the added part correctly you should ensure that the added
                        # part is in an order. So erase everything in between these tokens -> and / or

                sys.exit("Chapter ended!")

    # Optimization for GIZA -> extracting individual sent alignments to improve perf
    def extractGIZAsentAlignments(self, workpath):

        # Create books giza folder in the alignment path
        if not os.path.exists(self.procFolder + "/giza"):
            os.mkdir(self.procFolder + "/giza")

        # Read the general refs file
        fh_refs = open(workpath + "/refs.txt", "r", encoding="utf8")
        fh_assocs = open(workpath + "/giza.assocs", "r", encoding="utf8")

        # Sortie
        refs_sortie = open(self.procFolder + "/giza/refs.txt", "w", encoding="utf8")
        assocs_sortie = open(self.procFolder + "/giza/giza.assocs", "w", encoding="utf8")

        refs = fh_refs.readlines()
        tab_refs = []
        # Extracting refs
        for line in refs:
            (assoc, id_ls, id_lc) = line.strip().split("\t")
            try:
                assert id_ls == id_lc
            except AssertionError:
                print(id_ls, id_lc)
                sys.exit("Assertion error! Check the file!")

            if re.match(str(self.book_id) + "-", id_ls):
                refs_sortie.write(line.strip() + "\n")
                tab_refs.append(str(int(assoc) + 1))
        refs_sortie.close()
        print(tab_refs)

        with open(workpath + "/giza.assocs") as f:
            for lines in grouper(f, 3, ''):
                # print(lines)
                assert len(lines) == 3
                searchObj = re.search(r"\((.+?)\)", lines[0], re.I)

                if searchObj and searchObj.group(1) in tab_refs:

                    for tup in lines:
                        # print(tup)
                        assocs_sortie.write(tup)

        """ OLD ======>
		for i in range(len(self.chapters)):
			if self.alignedChapters[i] and self.chapters[i][3] not in self.corpus_dev:
				fh_sortie = open(self.procFolder+"/Alignments/"+str(self.chapters[i][0])+"/giza.assocs.txt","w",encoding="utf8")
				id_to_search = str(self.book_id) + "-" + str(self.chapters[i][0]) + "-" +"\d+"
				with open("../GIZA/aligned_words.txt") as f:
					for lines in grouper(f, 3, ''):
						assert len(lines) == 3
						#print(lines)
						if re.search(id_to_search,lines[1],re.I):
							for tup in lines:
								fh_sortie.write(tup)
		"""

    # Not in use -> Preparing data for GIZA++
    def GIZA(self):
        """
		Transfering alignment files to train GIZA++
		:return:
		"""

        fh_save = open("../Alignements/GIZA/ls.txt", "a", encoding="utf8")
        fh_save_fr = open("../Alignements/GIZA/lc.txt", "a", encoding="utf8")
        # Gotta put all of the ls and lc files to the same file but adding id's

        for i in range(len(self.chapters)):
            if self.alignedChapters[i] and self.chapters[i][3] not in self.corpus_dev and self.chapters[i][-1] != "0.0":

                ls_file = self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/reversed_stem_ls_regex.txt"
                lc_file = self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/reversed_stem_lc_regex.txt"

                fh_ls = open(ls_file, "r", encoding="utf8")
                lsFile = fh_ls.readlines()
                idNumber = str(self.book_id) + "-" + str(self.chapters[i][0]) + "-"
                lsFile = [(re.sub(r'<(\d+)>', r"<" + idNumber + "\\1>", x)) for x in lsFile]
                for line in lsFile:
                    fh_save.write(line)

                fh_lc = open(lc_file, "r", encoding="utf8")
                lcFile = fh_lc.readlines()
                idNumber = str(self.book_id) + "-" + str(self.chapters[i][0]) + "-"
                lcFile = [(re.sub(r'<(\d+)>', r"<" + idNumber + "\\1>", x)) for x in lcFile]
                for line in lcFile:
                    fh_save_fr.write(line)

        """
		corpus_dev = ["test-other", "test-clean", "dev-other", "dev-clean"]
		for i in range(len(self.chapters)):
			if self.alignedChapters[i] and self.chapters[i][3] not in corpus_dev:
				#Move to mozes folder and run perl script to tokenize
				ls_file = self.procFolder+"/Alignments/"+str(self.chapters[i][0])+"/reversed_stem_ls_regex.txt"
				lc_file = self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/reversed_stem_lc_regex.txt"
				transcpt = self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/transcriptions_aligned.txt"
				tokenizer_path = "../lib/mosesdecoder-master/scripts/tokenizer"
				giza_path = "../lib/giza-pp-master/project"
				giza_bin_dir = "../lib/giza-pp-master/GIZA++-v2"
				giza_cls_bin = "../lib/giza-pp-master/mkcls-v2/mkcls"
				#Remove <>, convert to lc and tokenize and
				copyfile(ls_file,tokenizer_path+"/ls.txt")
				copyfile(lc_file,tokenizer_path+"/lc.txt")
				os.system("perl -pi -w -e \"s/<\d+>//g;\" "+ tokenizer_path+"/ls.txt")
				os.system("perl -pi -w -e \"s/<\d+>//g;\" " + tokenizer_path + "/lc.txt")
				os.system("perl -ple '$_=lc' " + tokenizer_path+"/ls.txt > "+ tokenizer_path+"/ls.lw.txt")
				os.system("perl -ple '$_=lc' " + tokenizer_path + "/lc.txt > " + tokenizer_path + "/lc.lw.txt")
				os.system("perl "+ tokenizer_path+ "/tokenizer.perl -l \"en\" <"+tokenizer_path+"/ls.lw.txt"+"> "+giza_path +"/raw.en")
				os.system("perl " + tokenizer_path + "/tokenizer.perl -l \"fr\" <"+tokenizer_path+"/lc.lw.txt"+"> "+giza_path +"/raw.fr")

				#Creating giza sentence files
				os.system(giza_bin_dir+"/plain2snt.out " + giza_path +"/raw.en" + " " + giza_path +"/raw.fr" )
				#Creating cls files
				os.system(giza_cls_bin + " -p"+giza_path +"/raw.en "+" -V"+giza_path +"/raw.en.vcb.classes")
				os.system(giza_cls_bin + " -p" + giza_path + "/raw.fr " + " -V" + giza_path + "/raw.fr.vcb.classes")
				#Creating coocurence file
				os.system(giza_bin_dir+"/snt2cooc.out "+giza_path+"/raw.en.vcb "+giza_path+"/raw.fr.vcb "+ giza_path+"/raw.en_raw.fr.snt"+" > " + giza_path+"/cooc.cooc")

				#Launching giza++
				os.system(giza_bin_dir+"/GIZA++ ")
				#os.system("perl -pi -w -e \"s/> '/>  /g;\" ./example/hyp.txt")

				#Perl tolowercase saved as hyp file
					os.system("perl -ple '$_=lc' " + self.procFolder + "/Alignments/"
					          + str(self.chapters[i][0]) + "/reversed_stem_ls_regex.txt > ./example/hyp.txt")


				break
			"""

    def getBasicStats(self, dic):

        for i in range(len(self.chapters)):
            if self.chapters[i][-1] != 0.0:
                dic[self.chapters[i][0]] = self.chapters[i][-1]

    def visualize_html(self):

        absolute_path = "/var/www/html/Alignements/book_pages"

        fh_save = open(absolute_path + "/" + str(self.book_id) + ".php", "w", encoding="utf8")

        # Making pipeline Json files
        if not os.path.exists(self.procFolder + "/json"):
            os.makedirs(self.procFolder + "/json")

        php_folder = "/var/www/html/Alignements/audio_files"
        if not os.path.exists(php_folder + "/" + str(self.book_id)):
            os.mkdir(php_folder + "/" + str(self.book_id))

        # move the sound files
        for i in range(len(self.chapters)):
            if self.alignedChapters[i] and self.chapters[i][3] not in self.corpus_dev:
                folder = self.procFolder + "/gentle/" + str(self.chapters[i][0])
                folder_contents = os.listdir(folder)
                # Making the chapter folder
                if not os.path.exists(php_folder + "/" + str(self.book_id) + "/" + str(self.chapters[i][0])):
                    os.mkdir(php_folder + "/" + str(self.book_id) + "/" + str(self.chapters[i][0]))

                chapter_audios = php_folder + "/" + str(self.book_id) + "/" + str(self.chapters[i][0])
                wav_files = list(filter(lambda x: x.endswith("wav") and "-" in x, folder_contents))

                for wav in wav_files:
                    copyfile(folder + "/" + wav, chapter_audios + "/" + wav)
            elif self.chapters[i][3] in self.corpus_dev:
                # Than it means that flac files should be converted in to wav files and moved to php folder

                # Getting file contents
                folder = self.procFolder + "/data/" + str(self.chapters[i][0])
                folder_contents = os.listdir(folder)
                flac_files = list(filter(lambda x: x.endswith("flac"), folder_contents))

                # Making the chapter folder
                if not os.path.exists(php_folder + "/" + str(self.book_id) + "/" + str(self.chapters[i][0])):
                    os.mkdir(php_folder + "/" + str(self.book_id) + "/" + str(self.chapters[i][0]))

                # Converting flac files
                for flac in flac_files:
                    # Conversion du fichier vers .wav
                    # soundconverter -b -m audio/x-flac -s .wav "total.flac"
                    if os.path.exists(folder + "/err_log.txt"):
                        log = open(folder + "/err_log.txt", "a")
                    else:
                        log = open(folder + "/err_log.txt", "w")

                    cmd = "soundconverter -b -m audio/x-flac -s .wav \"" \
                          + folder + "/" + flac + "\""
                    command = Command(cmd, log)
                    command.run(timeout=40)

                    # Then move these sound files to the corresponding chapter folder
                    os.rename(folder + "/" + re.sub(r"\.flac", ".wav", flac), php_folder + "/" + str(self.book_id)
                              + "/" + str(self.chapters[i][0]) + "/" + re.sub(r"\.flac", ".wav", flac))

        html = """<?php include_once('../php/heading.php'); ?>

			<?php include_once('../php/navbar.php'); ?>
			<div class="container">
		    <!-- Example row of columns -->
		    <div class="row">
		        <?php

		            include("../php/traitements.php");

				"""
        html += "$current_id = " + str(self.book_id) + ";\n"
        html += "$original_title = \"" + str(self.original_title) + "\";\n"
        html += "$translated_title = \"" + str(self.translated_title) + "\";\n"
        html += "$corpus_dev = " + str(self.corpus_dev) + ";\n"
        html += "$aligned_chapters = " + str(self.alignedChapters) + ";\n"
        html += "$chapters = " + str(self.chapters) + ";\n"
        html += "$aligned_minutes = " + str(self.alignedMinutes) + ";\n"
        html += "$alignmentQuality = " + str(self.alignmentQuality) + ";\n"

        html += "print(\"<h1 class='text-center'>" + self.original_title + "</h1>\");"
        html += """include("../php/generateTable.php");
        ?>
        <hr>
        <h2 class="text-center">Statistics </h2>
    <div class="row text-center">
    <?php
        include_once("../php/statistiques.php");

    ?>
        </div>
    </div>
    <div class="row">
    <h2 class="text-center">Chapters</h2>

		<div class="row text-center">
            <?php
            for($i=0;$i<count($chapters);$i++){
                print("<a style='font-size: 18px;' href='#".$chapters[$i][0]."'>".$chapters[$i][0]."&nbsp;&nbsp;&nbsp;</a>");
                if($i%14 == 0){
                    print("<br>");
                }
            }
            ?>
        </div>


        <br><hr>
        <?php

        $data = [];
        include_once('../php/pipeline.php');

        ?>
        <hr><br>
        <h2 class="text-center">Alignments</h2>

        <?php
        include_once('../php/alignements.php');

        ?>

        <?php
        include_once("../php/alignements_finaux.php");
        ?>


        </div>

        </div>
    </div>
</div>

<?php include_once('../php/end.php') ?>
		"""

        fh_save.write(html)

    # Not in use -> clear rev_stem_files
    def checkForceTranscriptions(self):
        for i in range(len(self.chapters)):
            if self.alignedChapters[i]:
                stem_file_ls = self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/reversed_stem_ls.txt"
                stem_file_lc = self.procFolder + "/Alignments/" + str(self.chapters[i][0]) + "/reversed_stem_lc.txt"
                rev_stem_file_ls = self.procFolder + "/Alignments/" + str(
                    self.chapters[i][0]) + "/reversed_stem_ls_regex.txt"
                rev_stem_file_lc = self.procFolder + "/Alignments/" + str(
                    self.chapters[i][0]) + "/reversed_stem_lc_regex.txt"

                tab = [stem_file_ls, rev_stem_file_ls, stem_file_lc, rev_stem_file_lc]
                for file in tab:
                    if os.path.exists(file):
                        print("Deleting file: " + file)
                        os.remove(file)

    # To fix the sync problem
    def encodeFilenames(self):
        # check the ls chapitres folfder


        ls_chapitres = self.procFolder + "/en/chapitres"
        lc_chapitres = self.procFolder + "/fr/chapitres"

        if os.path.exists(ls_chapitres):
            shutil.rmtree(ls_chapitres)
        if os.path.exists(lc_chapitres):
            shutil.rmtree(lc_chapitres)

    # Utilities
    def align(self):
        self.alignChapters()
        self.postProcessing()
        self.forceTranscriptions()
        self.extractGIZAsentAlignments("../GIZA/nouveau_rev_stemmed")
        self.finalAlignment()

    def clear_DB_alignments(self, book_id=-1):
        """
		Deleting all alignments for a given book_id from the table alignments.
		:param book_id: Book id to remove
		:return: null
		"""
        table = self.getDB_dataset("alignements")

        # If no parameter is given drops all the rows
        if book_id == -1:
            table.delete()
        else:
            table.delete(book_id=book_id)

    def getWordAlignment(self, chapter_id, sent_id, txt_cut):
        """
		Parses GIZA++ output for the chapter and retursn sentence alignments for that sentence
		(Note: the WordAlignments() class deals with this in a better way. Extract all of the alignments once and
		computes after). This is an easier alternative and not as the chapters are not long shouldn't be exhaustive to
		compute
		:param chapter_id: chapter id to be searched
		:param sent_id: id of sent which is cut
		:param txt_cut: the part of the text which is cut (all of the text cannot be cut because they're already excluded)
		:return: tuple (sent_pair_id,french_tokens,english_assocs)
		"""
        line_number = -1
        with open(self.procFolder + "/giza/refs.txt", "r", encoding="utf8")as fh:
            for line in fh:
                (sent_line, id, id2) = line.split("\t")
                if id == str(self.book_id) + "-" + str(chapter_id) + "-" + str(sent_id):
                    line_number = int(sent_line) + 1
                    break
        if line_number == -1:
            raise RegularExpressionNotFound
        # If the sent is found that sentence should be extracted from giza assocs file


        with open(self.procFolder + "/giza/giza.assocs", "r", encoding="utf8") as fh:
            for lines in grouper(fh, 3, ''):
                assert len(lines) == 3
                if re.search(r"\(" + str(line_number) + "\)", lines[0]):
                    alignments_tuple = lines

        # Verify if the cut segment is at the end | beginning | middle
        # Take the alignments tuple, delete all of the ({}) and determine where is the text situated

        word_alignments = re.sub(r"\({.+?}\) |NULL ", "", alignments_tuple[2], 0)

        ##Sequence match in list is a good idea, but the punctuations are really a problem. Either a new training with only text is require
        # or rearranging the associations by verifying for each
        assocs = re.findall(r"(\w+) \({(.+?)}\)", alignments_tuple[2], 0)
        french_sent = alignments_tuple[1]
        txt_cut_split = txt_cut.split(" ")
        first_three = []

        for x in range(1, len(assocs)):
            if x < 4:
                first_three.append(assocs[x][0])
        try:
            last_three = [assocs[-3][0], assocs[-2][0], assocs[-1][0]]
        except IndexError:
            last_three = [assocs[-2][0], assocs[-1][0]]

        # TODO: Add left_right search if the token assoc is not known
        # TODO: If the sent is in the middle look to see if it's more than 3 tokens and if it is, see if it's properly aligned with -1 +1 treshold

        # Means that it's cut in the beginning
        index_to_cut = -1
        if len(set(first_three) - set(txt_cut_split)) <= 1:
            lastToken = txt_cut_split[-1]
            to_verify = txt_cut_split[-2]

            for x in range(len(assocs)):
                if assocs[x][0] == lastToken and assocs[x - 1][0] == to_verify:
                    # print(assocs[x][0], assocs[x][1])
                    possibilities = assocs[x][1].split(" ")
                    possibilities = list(filter(None, possibilities))

                    # If the length is more than 1 means that a word is associated with more than one words, then get the consecutive words
                    #
                    if len(possibilities) > 1:
                        possibilities = [int(possibility) for possibility in possibilities]
                        consecutive_lists = get_sub_list(possibilities)
                        for l in consecutive_lists:
                            if len(l) > 1:
                                index_to_cut = l[-1]  # Cut from the last word. Ex: mal a l'aise(<->)
                    elif len(possibilities) == 1:
                        index_to_cut = int(possibilities[0])
                    elif len(possibilities) < 1:
                        pass

            # Return the sent with <del>
            start_ph = "__del__"

            if index_to_cut != -1:
                french_sent = start_ph + french_sent

                french_sent = french_sent.split(" ")
                french_sent[index_to_cut] += "__/del__"

                return ' '.join(french_sent)
            else:
                return None

        elif len(set(last_three) - set(txt_cut_split)) <= 1:  # Means it at the end
            firstToken = txt_cut_split[0]
            to_verify = txt_cut_split[1]
            for x in range(len(assocs)):
                if assocs[x][0] == firstToken and assocs[x + 1][0] == to_verify:
                    # print(assocs[x][0], assocs[x][1])
                    possibilities = assocs[x][1].split(" ")
                    possibilities = list(filter(None, possibilities))

                    # If the length is more than 1 means that a word is associated with more than one words, then get the consecutive words
                    #
                    if len(possibilities) > 1:
                        possibilities = [int(possibility) for possibility in possibilities]
                        consecutive_lists = get_sub_list(possibilities)
                        for l in consecutive_lists:
                            if len(l) > 1:
                                index_to_cut = l[-1]  # Cut from the last word. Ex: mal a l'aise(<->)
                    elif len(possibilities) == 1:
                        index_to_cut = int(possibilities[0])
                    elif len(possibilities) < 1:
                        pass

                # Return


                if index_to_cut != -1:
                    french_sent = french_sent.split(" ")
                    start_ph = "__del__" + french_sent[index_to_cut]
                    french_sent[index_to_cut] = start_ph
                    french_sent.append("__/del__")

                    return ' '.join(french_sent)
                else:
                    return None




    @staticmethod
    def seq_in_seq(subseq, seq):
        while subseq[0] in seq:
            index = seq.index(subseq[0])
            if subseq == seq[index:index + len(subseq)]:
                return index
            else:
                seq = seq[index + 1:]
        else:
            return -1

    # Not in use -> Added GIZA alignments at the beginning so they start with the correct count
    @staticmethod
    def giza_recount(regex, path):
        """
		In order to associate book_id-chapter_id-sent_id to a alignment, sentences are in a spesific order. This count
		should be started from 0 when there are other train sents are used to improve results.
		:param regex: The regex that will be used to find the first sentence (count = 0)
		:param path: Path of the GIZA word asssociations file
		:return: null
		"""

        # Path management
        tab_path = path.split("/")
        folder = '/'.join(tab_path[:-1])
        fh_sortie = open(folder + "/giza.assocs", "w", encoding="utf8")

        # Extract only the alignments from the whole training
        with open(path) as f:
            lines = f.readlines()
        found = False

        for x in range(len(lines)):
            if re.match(regex, lines[x], re.I):
                found = True
                # Write the previous line too
                fh_sortie.write(lines[x - 1])
            if found:
                fh_sortie.write(lines[x])
        fh_sortie.close()

        # Recount from 0 on a temporary file
        fh_assocs = open(folder + "/giza.assocs", "r", encoding="utf8")
        fh_temp = open(folder + "/giza.temp", "w", encoding="utf8")
        cpt = 0
        for line in fh_assocs:
            if re.search(r"Sentence pair \(\d+\)", line, re.I):
                line = re.sub(r"Sentence pair \(\d+\)", "Sentence pair (" + str(cpt) + ")", line, re.I)
                fh_temp.write(line)
                cpt += 1
            else:
                fh_temp.write(line)
        fh_temp.close()

        # Make sure that the length of the file matches & rename the file as the original
        assert wc(folder + "/giza.assocs") == wc(folder + "/giza.temp")
        os.rename(folder + "/giza.temp", folder + "/giza.assocs")

    @staticmethod
    def findClosestAligned(structure, pos):

        i = 1
        closest = -1
        found = None
        while not found:
            try:
                if structure['words'][pos + i]['case'] == "success":
                    found = True
                    closest = pos + i
                elif structure['words'][pos - i]['case'] == "success":
                    found = True
                    closest = pos - i
            except IndexError:
                break
            i += 1

        return closest

    # print(structure['words'][pos])

    @staticmethod
    def sorted_nicely(l):
        """ Sort the given iterable in the way that humans expect."""
        convert = lambda text: int(text) if text.isdigit() else text
        alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
        return sorted(l, key=alphanum_key)

    @staticmethod
    def removePunctuations(txt):
        """
		Remove all punctuations with NLTK
		:param txt: string to tokenize
		:return: A list of tokens without punctuation
		"""
        tokens = nltk.wordpunct_tokenize(txt)

        text = nltk.Text(tokens)

        words = [w.lower() for w in text if w.isalpha()]

        return words

    @staticmethod
    def compute_diff(source, target, fh_html=None):
        """
		Google's diff-patch-match algorithm. As i'm calling it quite often, this static method could help that
		:param source: textA
		:param target: textB
		:param fh_html: filename to open if we want as well a html output
		:return: list of diffs
		"""
        # create a diff_match_patch object
        dmp = diff_match_patch.diff_match_patch()

        # Depending on the kind of text you work with, in term of overall length
        # and complexity, you may want to extend (or here suppress) the
        # time_out feature
        dmp.Diff_Timeout = 0  # or some other value, default is 1.0 seconds

        # All 'diff' jobs start with invoking diff_main()
        diffs = dmp.diff_main(source, target)

        # diff_cleanupSemantic() is used to make the diffs array more "human" readable
        dmp.diff_cleanupSemanticLossless(diffs)

        # and if you want the results as some ready to display HMTL snippet
        htmlSnippet = dmp.diff_prettyHtml(diffs)

        if fh_html:
            with open(fh_html, "w", encoding="utf8") as fh:
                fh.write(htmlSnippet)

        return diffs

    @staticmethod
    def diffs_to_text(diffs, l_add):
        """
		Takes diffs list coming from diff-patch-match algorithm and adds everything removed and unchanged, however deleting
		everything else that is added except a given list(creates a regex)
		:param diffs:
		:param l_add:
		:return:
		"""
        text = ""
        regex_added = '|'.join(l_add)

        for tupl in diffs:
            if tupl[0] == 1:
                text += re.sub(r"[^" + regex_added + "]", "", tupl[1], 0, re.I | re.M)
            elif tupl[0] == -1:
                text += tupl[1]
            else:
                text += tupl[1]

        return text


############# Functions ######################

def split_list(n):
    """will return the list index"""
    return [(x + 1) for x, y in zip(n, n[1:]) if y - x != 1]


def get_sub_list(my_list):
    """will split the list base on the index"""
    my_index = split_list(my_list)
    output = list()
    prev = 0
    for index in my_index:
        new_list = [x for x in my_list[prev:] if x < index]
        output.append(new_list)
        prev += len(new_list)
    output.append([x for x in my_list[prev:]])
    return output


def dumpJson(path, data):
    with open(path, 'w') as outfile:
        json.dump(data, outfile)


def loadJson(path):
    with open(path) as json_data:
        data = json.load(json_data)
        return data


def getExtension(values):
    reg = re.search(r'\.(.+?)$', values, re.I)
    return reg.group(1)


def inbetweenExtractor(chapters, instance, lang, STOP=""):
    for i in range(len(chapters)):

        saveFile = instance.procFolder + "/" + lang + "/chapitres/" + chapters[i].strip() + ".txt"
        cptFile = 1

        if not os.path.isfile(saveFile):
            fh = open(saveFile, "w", encoding="utf8")
        else:
            saveFile = instance.procFolder + "/" + lang + "/chapitres/" + chapters[i].strip() \
                       + "_" + str(cptFile) + ".txt"
            cptFile += 1
            fh = open(saveFile, "w", encoding="utf8")

        if lang == 'en':
            file_to_open = instance.lsFile
        else:
            file_to_open = instance.lcFile[:-len(getExtension(instance.fileName))] + "txt"
        with open(file_to_open) as input_data:
            while True:  # While EOF
                text = ""
                # Pass until block
                for line in input_data:
                    if re.search(r"^" + re.escape(chapters[i]) + "$", line):
                        fh.write(line)  # Exclusion du titre!
                        break
                # Read until block
                for line in input_data:
                    text += "\n"  # Add newlines!
                    try:
                        para_fin = re.search(r'^' + re.escape(chapters[i + 1]) + "$", line)
                        if para_fin:
                            fh.write(text)
                            break
                    except IndexError:
                        para_fin = re.search(r'^' + re.escape(STOP) + "$", line)
                        if para_fin:
                            fh.write(text)
                            break
                    # print(line)  # For debug purposes

                    # Extract letter and append to text while in the same block
                    letter = re.search(r'(.*)', line, re.I)
                    if letter:
                        text += letter.group(1)
                break


def replaceHTMLchars(x, y):
    subs_x = re.sub(r'&apos;', "'", x)
    subs_x = re.sub(r'&quot;', "\"", subs_x)
    subs_x = re.sub(r'&amp;', "&", subs_x)
    subs_x = re.sub(r'^\W+', "", subs_x)
    subs_x = re.sub(r'^\'+', "", subs_x)
    subs_x = re.sub(r'&lt;p&gt;', "", subs_x)
    subs_x = re.sub(r'&lt;|lt;', "<", subs_x)
    subs_x = re.sub(r'&gt;', ">", subs_x)
    subs_y = re.sub(r'&apos;', "'", y)
    subs_y = re.sub(r'&quot;', "\"", subs_y)
    subs_y = re.sub(r'^\W+', "", subs_y)
    subs_y = re.sub(r'^\'+', "", subs_y)
    subs_y = re.sub(r'&lt;p&gt;', "", subs_y)
    subs_y = re.sub(r'&lt;|lt;', "<", subs_y)
    subs_y = re.sub(r'&gt;', ">", subs_y)
    return subs_x, subs_y


def reverseStemming(language, token, stem, output):
    if language == "en":
        en_tok_file = token
        en_stem_file = stem

        # Ouverture des fichiers
        fh_en_toks = open(en_tok_file, "r", encoding="utf8")
        fh_en_stem = open(en_stem_file, "r", encoding="utf8")

        # Tableau des tokens
        tab_en_toks = []
        for line in fh_en_toks:
            line = line.strip()
            splitted = line.split("\t")

            if splitted[1] != "\\n" and splitted[1] != "<p>":
                # print(splitted[1],splitted[2])
                if not splitted[1].isalnum():
                    """
					Possible cases: 1) punctuation 2) \w+-\w 3) punctuation+ 4) '\w
					"""
                    if re.match(r"'\w", splitted[1], re.I):
                        tab_en_toks.append([splitted[1], splitted[2]])
                    elif re.match(r"\w+-\w+", splitted[1], re.I):
                        tab_en_toks.append([splitted[1], splitted[2]])
                    elif re.search(r"[" + punctuation + "]+", splitted[1], re.I):
                        pass
                    else:
                        print("There might be an exception in tokens_ls")
                else:
                    tab_en_toks.append([splitted[1], splitted[2]])
        fh_en_toks.close()

        # Perl regex replace on stemfiles
        cmd1 = "perl -pi -e 's/(\w+)\./$1 \./gm' " + en_stem_file
        os.system(cmd1)
        # cmd2= "perl -pi -e 's/(\w+)\'s /$1 \'s /gm' " + en_stem_file
        # os.system(cmd2)

        alignedFile = fh_en_stem.readlines()
        fh_en_stem.close()
        alignedFile = [(re.sub(r'<\d+>|\ufeff|< p >', r"", item.strip())) for item in alignedFile]
        stemmed_tokens = []
        for subl in tab_en_toks:
            stemmed_tokens.append(subl[0])

        # Replacing tokens
        j = 0
        lineCount = 0
        for line in alignedFile:

            tokenizer = TreebankWordTokenizer()
            tags = tokenizer.tokenize(line)
            tags.append("\\n")  # To know when to break the line
            # print(tab_en_toks)
            # print(tags)
            output.write("<" + str(lineCount) + "> ")
            for i in range(len(tags)):
                """
				Either is a puncutation -> then put the punctuation if not search in the list,
				replace and delete the token from the list
				"""
                if tags[i] in punctuation or re.match(r"[" + punctuation + "]+", tags[i], re.I):
                    output.write(tags[i] + ' ')
                elif tags[i] == "NA":
                    output.write("NA ")
                elif tags[i] != "\\n":
                    try:
                        tok_index = stemmed_tokens.index(tags[i], j)
                        output.write(tab_en_toks[tok_index][1] + " ")
                        j += 1
                    except ValueError:
                        output.write(tags[i] + " ")
                    # lineCount += 1
                    # break
                elif tags[i] == "\\n":
                    output.write("<" + str(lineCount) + ">\n")
            lineCount += 1

    if language == "fr":
        fr_tok_file = token
        fr_stem_file = stem
        fh_fr_toks = open(fr_tok_file, "r", encoding="utf8")
        fh_fr_stem = open(fr_stem_file, "r", encoding="utf8")

        tab_fr_toks = []

        # regex changes
        # 1st perl sed to replace \w+\.

        os.system("perl -pi -e 's/…/.../gm' " + fr_tok_file)
        os.system("perl -pi -e 's/\d+\t(\w+)(\.)+\t(.+?)\./0\t$1\t$1\n0\t$2\t$2/gmrg' " + fr_tok_file)
        os.system("perl -pi -e 's/\d+\t(\w+)—\t(.+?)\./0\t$1\t$1\n0\t—\t—/gmrg' " + fr_tok_file)

        # Tokens file
        for line in fh_fr_toks:
            line = line.strip()
            splitted = line.split("\t")
            if splitted[1] != "\\n" and splitted[1] != "<p>":
                # print(splitted[1],splitted[2])
                if not splitted[1].isalnum():
                    """
					Possible cases: 1) punctuation 2) \w+-\w 3) punctuation+ 4) '\w
					"""
                    if re.match(r"'\w", splitted[1], re.I):
                        tab_fr_toks.append([splitted[1], splitted[2]])
                    elif re.match(r"\w+-\w+", splitted[1], re.I):
                        tab_fr_toks.append([splitted[1], splitted[2]])
                    elif re.search(r"[" + punctuation + "]+", splitted[1], re.I):
                        if re.search(r"\w", splitted[1], re.I):
                            tab_fr_toks.append([splitted[1], splitted[2]])
                        else:
                            pass  # Only punctuation
                    else:
                        if re.search(r"[" + punctuation + "—«»]+", splitted[1], re.I):
                            pass  # different punctuations
                        elif re.search(r"['’]", splitted[1], re.I):
                            tab_fr_toks.append([splitted[1], splitted[2]])
                        else:
                            tab_fr_toks.append([splitted[1], splitted[2]])
                        # sys.exit("There is an exception in the tokens file")
                else:
                    tab_fr_toks.append([splitted[1], splitted[2]])

        # Stem file regex
        os.system("perl -pi -e 's/(\w+)\./$1 \./gmrg' " + fr_stem_file)

        stemmed_tokens = []
        for subl in tab_fr_toks:
            stemmed_tokens.append(subl[0])

        # Stem - tok replacements
        j = 0
        lineCount = 0
        alignedFile = fh_fr_stem.readlines()

        alignedFile = [(re.sub(r'<\d+>|\ufeff|< p >', r"", item.strip())) for item in alignedFile]
        alignedFile = [(re.sub(r'(\w+)\.', r"\1 .", item.strip(), re.UNICODE)) for item in alignedFile]
        alignedFile = [(re.sub(r'(\w+)—', r"\1 .", item.strip(), re.UNICODE)) for item in alignedFile]
        alignedFile = [(re.sub(r'…', r"...", item.strip(), re.UNICODE)) for item in alignedFile]
        #
        for line in alignedFile:

            tokenizer = TreebankWordTokenizer()
            tags = tokenizer.tokenize(line)
            tags.append("\\n")  # To know when to break the line
            # print(tab_en_toks)
            # print(tags)
            output.write("<" + str(lineCount) + "> ")
            for i in range(len(tags)):
                """
				Either is a puncutation -> then put the punctuation if not search in the list,
				replace and delete the token from the list
				"""
                if tags[i] in punctuation or re.match(r"[" + punctuation + "«»—]+", tags[i], re.I):
                    output.write(tags[i] + " ")

                elif tags[i] == "NA":

                    output.write("NA ")
                elif tags[i] != "\\n":
                    try:
                        tok_index = stemmed_tokens.index(tags[i], j)
                        output.write(tab_fr_toks[tok_index][1] + " ")
                        j += 1
                    except ValueError:
                        retry = re.sub(r"î", "i", tags[i], re.UNICODE, re.IGNORECASE)
                        try:
                            tok_index = stemmed_tokens.index(retry, j)
                            output.write(tab_fr_toks[tok_index][1] + " ")
                            # lineCount += 1
                            j += 1
                        except ValueError:
                            output.write(tags[i] + " ")
                            # lineCount += 1
                            pass
                elif tags[i] == "\\n":

                    output.write("<" + str(lineCount) + ">\n")
            lineCount += 1


# Not in use anymore#
def easytrick(input, output):
    fh = open(input, "r")
    text = ""
    for line in fh:
        text += line

    import re

    regex = r"(<-?\d+>) \n"
    subst = "\\n\\1 "

    # You can manually specify the number of replacements by changing the 4th argument
    result = re.sub(regex, subst, text, 0, re.MULTILINE)
    fh2 = open(output, "w")
    if result:
        fh2.write(result)


def takeClosest(myList, myNumber):
    pos = bisect_left(myList, myNumber)
    if pos == 0:
        return myList[0]
    if pos == len(myList):
        return myList[-1]
    before = myList[pos - 1]
    after = myList[pos]
    if after - myNumber < myNumber - before:
        return after
    else:
        return before


def computeScoreforSent(l, alignObj, chapter_id):
    # print(l)
    fh = open(alignObj.procFolder + "/Alignments/" + str(chapter_id) + "/scores.txt", "r", encoding="utf8")
    scores = fh.readlines()
    dic_scores = {}
    for score in scores:
        score = score.strip()
        searchObj = re.search(r"<(\d+)>(.+?)<\d+>", score, re.I)
        if (searchObj):
            dic_scores[searchObj.group(1)] = searchObj.group(2)

    l = [dic_scores[x] for x in l]
    l = [float(x) for x in l]
    return mean(l)


# Not in use -> replaced with WordAlignments class
def align_target_sent_words(l, target_sent_id):
    # association dictionary
    associations = {}
    lc_line = {}
    giza_file_path = "../GIZA/alice_example"
    with open(giza_file_path) as f:

        for lines in grouper(f, 3, ''):

            assert len(lines) == 3
            # print(lines)

            # process N lines here
            id = re.search(r"(\d+-\d+-\d+)", lines[1].strip(), re.I)
            if id:
                sent_id = id.group(1)
                lc_line[sent_id] = lines[1].strip()
                # lines[1] = re.sub(r"\d+-\d+-\d+","",lines[1],0,re.I)
                word_associations = []

                alignments = re.findall(r"(.+?) \({(.+?)}\)", lines[2].strip(), re.I)

                for tup in alignments:
                    possblts = tup[1][1:-1]
                    if possblts != "":
                        all_possblts = possblts.split(" ")
                        word_associations.append([tup[0], ','.join(all_possblts)])
                    else:
                        word_associations.append([tup[0], None])

                associations[sent_id] = word_associations


            else:
                # print(lines[1])
                pass
            # print("There might be a little problem")


            # alignments = re.findall(r"(\w+) \({(.+?)}\)", lines[2].strip(), re.I)
    # print(l)
    # print(associations)
    # print(lc_line)

    # print(l)
    # print(associations[target_sent_id])
    cutTargetSentence(l, associations, target_sent_id, lc_line, [])
    sys.exit()


# Not in use
def cutTargetSentence(l, assocs, identifier, lc, lc_sortie):
    """
	Recursive function that cuts the target sentence according to the number of \n of the
	english sentence
	:param l [] : List that contains cut sentences by \n. (At least 2, max ?)
	:param assocs {} : GIZA++ word alignment indexes (in order of the english text).
	Keys: book_id-chapter_id-line_id , Values: [word,index]
	:param identifier (str): book_id-chapter_id-line_id that we need
	:param lc {} : French sentences that is going to be used for searching the indexes
	:return: NOT DECIDED YET
	"""

    # End of the recursion
    if l == []:
        return lc_sortie

    # 1. Get the first part of the sentence ( (...) \n (...) )
    source_sentence = l[0].strip().split(" ")

    # Debug purposes
    # print(assocs[identifier])
    # print(l)
    # print(lc[identifier])

    # the length of the source sentence brings us to the token that we should cut the french text
    # assocs[identifier][len(source_sentence)]) => list of the english word and its position in the
    # french sentence

    # print(assocs[identifier][len(source_sentence)])

    # lists' first index contains the word(str), the second contains the position of that token in the french
    # sentence

    word_to_cut = assocs[identifier][len(source_sentence)][0]
    ref_to_token = assocs[identifier][len(source_sentence)][1]

    print(ref_to_token)
    # if the last token is not aligned by GIZA++,
    if ref_to_token == None:
        slide_to_right = 0
        # Search in the rest of the list for a word that is aligned and return how many indexes
        # we slided to the right
        while ref_to_token == None:  # while we find a token that's aligned!
            # slide to the right
            ref_to_token = assocs[identifier][len(source_sentence) + slide_to_right][1]
            slide_to_right += 1

        # How many indexes we went right
        print(slide_to_right)
        # The token that's aligned and it's the positioning of the french word that's aligned with
        print(assocs[identifier][len(source_sentence) + slide_to_right][0]
              , assocs[identifier][len(source_sentence) + slide_to_right][1])
        # We keep the last position that we cut the sentence
        print(assocs[identifier][len(source_sentence) + slide_to_right][1])

        lastIndex = int(assocs[identifier][len(source_sentence) + slide_to_right][1])
        # print(lastIndex)
        # Search in the french sentence the indexed token
        frenchSent = lc[identifier].split(" ")

        # The aligned sentences
        print(l[0])
        print(' '.join(frenchSent[0:int(lastIndex) - slide_to_right]))
        print(source_sentence[lastIndex:int(assocs[identifier][len(source_sentence) + slide_to_right][1])])
        lc_sortie.append(' '.join(frenchSent[0:int(lastIndex) - slide_to_right]))

        # print(lc_sortie)
        # Delete l[0] and
        del l[0]
    else:
        # Token ref is not not None
        sys.exit("easy peasy")

    # Recursion!
    return cutTargetSentence(l, assocs, identifier, lc, lc_sortie)


def grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def diffs_to_text(l):
    text = ""

    for tup in l:
        # Unchanged -> put it exactly
        if tup[0] == 0:
            text += tup[1]
        # Add the stems that are removed
        if tup[0] == 1:
            text += tup[1]
        # Here comes the tricky part -> keep only NA \n but remove all others
        if tup[0] == -1:
            modified = re.sub(r"[^NA\n]+", "", tup[1], 0)
            text += modified
    return text


def wc(filename):
    return int(check_output(["wc", "-l", filename]).split()[0])


def pickle_data(path, data):
    fh = open(path, "wb")
    pickle.dump(data, fh)


def depickle_data(path):
    try:
        fh = open(path, "rb")
        return pickle.Unpickler(fh).load()
    except pickle.PickleError as err:
        return err


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


class WordAlignments:
    def __init__(self, l, target_sent_id, giza_path, dic_lc):
        self.ls_segments = l
        self.id = target_sent_id
        self.giza_sortie_path = giza_path
        self.associations = self._getAssociations()
        self.lc_originals = dic_lc

    def _getAssociations(self):
        self.lc_lines = {}
        associations = {}
        path_refs = self.giza_sortie_path + "/refs.txt"
        giza_assocs = self.giza_sortie_path + "/giza.assocs"
        refs = {}
        fh_refs = open(path_refs, "r", encoding="utf8")
        tab_refs = fh_refs.readlines()
        for line in tab_refs:
            line = line.strip()
            splitted = line.split("\t")
            assert splitted[1] == splitted[2]
            refs[str(int(splitted[0]) + 1)] = splitted[1]

        with open(giza_assocs) as f:
            for lines in grouper(f, 3, ''):
                assert len(lines) == 3

                id = re.search(r"\((\d+)\)", lines[0].strip(), re.I)
                if id:
                    sent_id = refs[id.group(1)]
                    self.lc_lines[sent_id] = lines[1].strip()
                    word_associations = []
                    alignments = re.findall(r"(.+?) \({(.+?)}\)", lines[2].strip(), re.I)

                    for tup in alignments:
                        possblts = tup[1][1:-1]
                        if possblts != "":
                            all_possblts = possblts.split(" ")
                            word_associations.append([tup[0], ','.join(all_possblts)])
                        else:
                            word_associations.append([tup[0], None])

                    associations[sent_id] = word_associations

                else:
                    sys.exit("giza assocs id for sent not found!")
            return associations

    # OLD METHOD! use _getAssociations
    def getAssociations(self):
        self.lc_lines = {}
        associations = {}
        with open(self.giza_sortie_path) as f:
            for lines in grouper(f, 3, ''):
                assert len(lines) == 3
                id = re.search(r"(\d+-\d+-\d+)", lines[1].strip(), re.I)
                if id:
                    sent_id = id.group(1)
                    self.lc_lines[sent_id] = lines[1].strip()
                    # lines[1] = re.sub(r"\d+-\d+-\d+","",lines[1],0,re.I)
                    word_associations = []

                    alignments = re.findall(r"(.+?) \({(.+?)}\)", lines[2].strip(), re.I)

                    for tup in alignments:
                        possblts = tup[1][1:-1]
                        if possblts != "":
                            all_possblts = possblts.split(" ")
                            word_associations.append([tup[0], ','.join(all_possblts)])
                        else:
                            word_associations.append([tup[0], None])

                    associations[sent_id] = word_associations

                else:
                    pass
            return associations

    def getTargetSentence(self):

        try:
            lc_sent = self.lc_lines[self.id].split(" ")
            ls_sent_assocs = self.associations[self.id]
            ls_sent_segs = self.ls_segments.split(" ")
            self.lc_sent_segments = []
        except KeyError:
            # Means that GIZA shortened the sentence -> pass
            print(self.ls_segments)
            print(self.id)
            key = re.search(r"\d+-\d+-(\d+)", self.id, re.I)
            key = key.group(1)

            sys.exit("KEY ERROR!")

        # For debug purposes
        print(lc_sent)
        print(ls_sent_assocs)
        print(ls_sent_segs)

        ###### THE LAST IDEA ###########
        # Instead of having three lists think of concatenating all of the lists together
        # And then add ğ to indicate that you have to put into another list in french
        # As the tokens of ls_sent et ls_seg are the same, use the same structure to cut the
        # whole sentence -> This way you won't have to deal with lastCutted, last Associated
        # it'll be easier!

        # Creating the union of lists to have segments and punctuation at the same time
        text_intermediare = ""
        # print(ls_sent_assocs)
        for x in range(1, len(ls_sent_assocs)):
            text_intermediare += ls_sent_assocs[x][0]

        tab_text_intermediaire = text_intermediare.split(" ")

        assert len(tab_text_intermediaire) == len(ls_sent_assocs)

        possible_index = []
        # Find all of the tokens that are surely aligned!
        # When there are more than one possibility assure that possibilities are less
        # than the next one surely aligned 2,3,53 -> for instance 2,3 ok but 53 not possible
        for x in range(len(tab_text_intermediaire)):
            if ls_sent_assocs[x][1] != None and ',' not in ls_sent_assocs[x][1]:
                # print(tab_text_intermediaire[x],ls_sent_assocs[x][1])
                possible_index.append(x)
            elif ls_sent_assocs[x][1] != None and ',' in ls_sent_assocs[x][1]:
                pass  # ??? Hard to compute !? Actually not

        print(possible_index)
        segs_to_cut = []
        indexes_ls_to_cut = []
        for y in range(len(ls_sent_segs)):
            if ls_sent_segs[y] == "ğ":
                print("ğ Found at: " + str(y))
                indexes_ls_to_cut.append(int(y))
                # intermediaire = filter(lambda x: x >= y, possible_index)
                try:
                    closest = takeClosest(possible_index, y - 1)
                except IndexError:

                    retour_count = 0
                    for item in ls_sent_segs:
                        if item == "ğ":
                            retour_count += 1
                    if retour_count > 1:
                        sys.exit("More than one ğ")

                    if lc_sent[0] == "na":
                        fr_segments = ls_sent_segs
                        for i, outter in enumerate(fr_segments):
                            if outter != "ğ":
                                fr_segments[i] = "_NA_"
                        retour_index = fr_segments.index("ğ")
                        fr_segments = [fr_segments[retour_index - 1], fr_segments[retour_index],
                                       fr_segments[retour_index + 1]]
                        return ' '.join(fr_segments).split("ğ")
                    if possible_index == []:
                        retour_count = 0
                        for item in ls_sent_segs:
                            if item == "ğ":
                                retour_count += 1
                        if not retour_count > 1:
                            return (' '.join(lc_sent) + "ğ" + ' '.join(lc_sent)).split("ğ")

                    else:
                        sys.exit("Index Error!")
                    # closest = takeClosest(list(intermediaire), y - 1)
                if closest != 0:
                    # difference = int(closest) - int(y)
                    # segs_to_add.append(difference)
                    segs_to_cut.append(closest)
                else:
                    print(possible_index)
                    closest = takeClosest(possible_index, y - 1)
                    # closest = takeClosest(intermediaire[1:], y - 1)
                    # difference = int(closest) - int(y)
                    print("\t\t\t" + str(closest))
                    # segs_to_add.append(difference)
                    segs_to_cut.append(closest)
                print("And the closest is : " + str(closest))
        # print(segs_to_add)
        print(segs_to_cut)
        print(indexes_ls_to_cut)

        for x in range(len(segs_to_cut)):
            # To see the resultst
            print(segs_to_cut[x], ls_sent_assocs[segs_to_cut[x]], lc_sent[int(ls_sent_assocs[segs_to_cut[x]][1]) - 1])
            if segs_to_cut[x] - indexes_ls_to_cut[x] == 0:
                lc_sent[int(ls_sent_assocs[segs_to_cut[x]][1]) - 1] += "ğ"
            else:
                lc_sent[int(ls_sent_assocs[segs_to_cut[x]][1]) - 1] += "ğ"
                """
				if segs_to_cut[x] > indexes_ls_to_cut[x]:
					diff = segs_to_cut[x] - indexes_ls_to_cut[x] + 1
					lc_sent[int(ls_sent_assocs[segs_to_cut[x]][1]) - 1 -diff] += "ğ"
				else:
					diff = indexes_ls_to_cut[x] - segs_to_cut[x] + 1
					lc_sent[int(ls_sent_assocs[segs_to_cut[x]][1])] += "ğ"
				"""
        print(lc_sent)

        # <--------------------- OLD -------------------------->
        fr_segments = ' '.join(lc_sent).split("ğ")
        return fr_segments

        ##Pour revenir a l'état avec les ponctuations
        # NEW

        print(' '.join(lc_sent))

        hyp = re.sub(r"ğ", "\n", ' '.join(lc_sent), re.I)
        print(self.id)
        key = re.search(r"\d+-\d+-(\d+)", self.id, re.I)
        key = key.group(1)

        print(hyp)
        print(self.lc_originals[str(key)])

        textA = hyp
        textB = self.lc_originals[str(key)]

        # create a diff_match_patch object
        dmp = diff_match_patch.diff_match_patch()

        # Depending on the kind of text you work with, in term of overall length
        # and complexity, you may want to extend (or here suppress) the
        # time_out feature
        dmp.Diff_Timeout = 0  # or some other value, default is 1.0 seconds

        # All 'diff' jobs start with invoking diff_main()
        diffs = dmp.diff_main(textA, textB)

        # diff_cleanupSemantic() is used to make the diffs array more "human" readable
        dmp.diff_cleanupSemanticLossless(diffs)

        # print(diffs)
        # and if you want the results as some ready to display HMTL snippet

        # print(htmlSnippet)

        text = diffs_to_text(diffs)
        return text.split("\n")

        """
		#Find the closest index that could be cut to the place of \n
		for y in range(len(ls_sent_segs)):
			if ls_sent_segs[y] == "ğ":
				print("ğ found at : " +str(y))
				try:
					intermediaire = filter(lambda x: x >= y,possible_index)
					closest = takeClosest(list(intermediaire),y-1)
					#print(possible_index[-1])
					print("\t\t"+str(closest))
					difference = int(closest) - int(y)
					print("difference is: ",str(difference))
					if closest != 0:
						segs_to_cut.append(closest)
					else:

						print(possible_index)
						closest = takeClosest(possible_index[1:],y-1)
						print("\t\t\t"+str(closest))
						segs_to_cut.append(closest)

				except IndexError:
					if lc_sent[0] == "na":
						segs_to_cut.append(-1)


		#print(segs_to_cut)
		for index in segs_to_cut:
			if index > 0:
				lc_sent[int(ls_sent_assocs[index][1])] += "ğ"




		#fr_segments = ' '.join(lc_sent).split("ğ")
		### -> Revenir a l'état avec les poncutations

		hyp = re.sub(r"ğ", " ğ",' '.join(lc_sent), re.I)
		id = re.search(r"\d+-\d+-(\d+)",hyp,re.I)
		if id:
			id = id.group(1)

		#print(hyp,self.lc_originals[str(id)])
		try:
			prettyhtml = node_run('/var/www/html/Alignements/js/essai.js', hyp, self.lc_originals[str(id)])
		except KeyError:
			searchObj = re.search(r"\d+-\d+-(\d+)",str(self.id),re.I)
			if searchObj:
				id = searchObj.group(1)

			prettyhtml = node_run('/var/www/html/Alignements/js/essai.js', hyp, self.lc_originals[str(id)])

		prettyhtml = prettyhtml[1]
		#print(prettyhtml)
		soup = BeautifulSoup(prettyhtml, "lxml")

		text = []
		print(prettyhtml)
		if lc_sent[0] != "na":

			firstHeader = soup.find('span')
			for tag in [firstHeader] + firstHeader.findNextSiblings():
				try:
					if tag.name == 'span':
						text.append(tag.string)
					elif tag.name == 'ins':
						text.append(tag.string)

					elif tag.name == 'del' and re.search(r"ğ", tag.string, re.I):
							text.append("ğ")
				except TypeError:
					#text.append("ğ")
					pass

		fr_segments = ''.join(text).split("ğ")

		#print()
		return fr_segments
		"""

        """
		text = []

		firstHeader = soup.find('span')
		for tag in [firstHeader] + firstHeader.findNextSiblings():
			if tag.name == 'span':
				text.append(tag.string)
			elif tag.name == 'ins':
				text.append(tag.string)

			elif tag.name == 'del' and re.search(r"ğ",tag.string,re.I):
				text.append(" ğ")

		ls_text_normalized = ''.join(text)

		tab_ls_text_norm = ls_text_normalized.split(" ")
		y = 1
		lastAligned = 0
		tok_index_to_cut = []
		tab_ls_text_norm = tab_ls_text_norm[1:]
		for x in range(len(tab_ls_text_norm[1:-1])):
			if tab_ls_text_norm[x] == "ğ":
				print("<-------------HERE-------------->")
				found = False
				tempx = x
				while not found:
					print(ls_sent_assocs[tempx+1][1],ls_sent_assocs[tempx+1][0])
					if ls_sent_assocs[tempx+1][1] == None:
						tempx += 1
					else:
						found = True
						print(ls_sent_assocs[tempx + 1][1], ls_sent_assocs[tempx + 1][0])
						tok_index_to_cut.append(tempx+1)
				print("<-------------HERE-------------->")
				continue
			else:
				pass
				#print(tab_ls_text_norm[x],ls_sent_assocs[x])
		print(ls_sent_segs)
		for index in tok_index_to_cut:
			lc_sent[index] += "ğ"
		lc_sent = lc_sent[:-1]
		text_lc = ' '.join(lc_sent)
		essai = text_lc.split("ğ")
		return essai
		"""
        """
		for x in range(len(tab_ls_text_norm)):
			try:
				if tab_ls_text_norm[x] == "ğ":
					print("LAST Aligned is : \t:",lastAligned, ls_sent_assocs[lastAligned][0],ls_sent_assocs[lastAligned][1])
					alignment_possblt = ls_sent_assocs[lastAligned][1].split(",")
					middleIndex = int((len(alignment_possblt) - 1) / 2)

					tok_index_to_cut.append(alignment_possblt[middleIndex])
					print("<-------------HERE-------------->")
					continue
				else:
					if ls_sent_assocs[y][1] != None:
						lastAligned = y
					#print(tab_ls_text_norm[x],ls_sent_assocs[y])

				y += 1
			except IndexError:
				pass

		#print(tok_index_to_cut)
		tok_index_to_cut.append(len(lc_sent))
		startIndex = 0
		for index in tok_index_to_cut:
			self.lc_sent_segments.append(' '.join(lc_sent[startIndex:int(index)]))
			startIndex = int(index)

		return self.lc_sent_segments
		"""
        """
		#For all of the segmentated cuts \n
		for slist in ls_sent_segments:
			tab_tokens = slist.split(" ") #Tokenize in the same way
			tab_tokens = list(filter(None, tab_tokens)) #Filtering out the empty ones

			max_last_aligned = 0
			for x in range(len(tab_tokens)):
				#print(ls_sent_assocs[x+1],tab_tokens[x])

				#print(ls_sent_assocs[x+1],tab_tokens[x])
				if (ls_sent_assocs[x+1][1] != None):
					max_last_aligned = x

			#print(max_last_aligned,len(tab_tokens))
			#max_last_aligned = index of the last aligned in the list
			pushed_to_left = len(tab_tokens)-max_last_aligned-1
			#print(lc_sent[:max_last_aligned+pushed_to_left])
			self.lc_sent_segments.append(lc_sent[:max_last_aligned+pushed_to_left])
			self.lastFrenchCut = max_last_aligned+pushed_to_left





			sys.exit()
			"""

    ########### MAIN ##########################


# Spesific Exception classes
@Exception
class RegularExpressionNotFound(Exception):
    """
		Returns an exception when there is no match for a spesific regular expression
		"""
    pass


@Exception
class PlusOneMinusOneError(Exception):
    pass


@Exception
class WordNotRecognized(Exception):
    """Means that the word to be recognized in the audio is not recongized and +1 index is not recognized either"""
    pass


def main():
    # 1. Recuperation des données de la BD et construction des instances
    books = {}
    for liste in loadJson("../DB/librispeech.json"):
        books[liste['book_id']] = liste

    """
	bookCount = len(books)
	for key,values in books.items():
		print("Books remaining: " + str(bookCount))
		try:
			bookObject = Alignements(values['book_id'], values['original_title'],
			                       values['translated_title'], values['file'])
		except AttributeError:
			pass # ne fait rien

		bookObject.encodeFilenames()
		bookCount -= 1

	"""
    """
	dico = {}
	for key,values in books.items():

		try:
			bookObject = Alignements(values['book_id'], values['original_title'],
			                       values['translated_title'], values['file'])
		except AttributeError:
			pass

		dico[bookObject.book_id] = bookObject.alignmentQuality

	import operator

	sorted_x = sorted(dico.items(), key=operator.itemgetter(1),reverse=True)

	#fh= open("./qualities.php","w",encoding="utf8")
	"""

    # Pour lancer uniquement sur id 11 = Alice au pays des merveilles
    Alice = Alignements(books[11]['book_id'], books[11]['original_title'],
                        books[11]['translated_title'], books[11]['file'])
    # Alice.finalAlignment()
    """
	my_db = Alice.getDB_dataset('alignements')
	fh_gtanslate = open("../DB/dumps/gtranslate.txt","r",encoding="utf8")
	gtranslate = fh_gtanslate.readlines()
	xcount = 0
	for row in my_db:
		print(row['seg_source'])
	"""
    """
	for line in fh_gtanslate:
		line = line.strip()
	"""
    # Alice.extractGIZAsentAlignments()


    # Alice.finalAlignment()
    #
    # Alice.visaulize_html()

    """
	Alice = Alignements(books[11]['book_id'],books[11]['original_title'],
	                     books[11]['translated_title'],books[11]['file'])

	#Alice.finalAlignment()
	Alice.visaulize_html()
	"""
    """
	fh_save_temp = open("../Alignements/GIZA/ls.txt","w",encoding="utf8")
	fh_save_temp.write("")
	fh_save_temp.close()
	fh_save_temp_fr = open("../Alignements/GIZA/lc.txt","w",encoding="utf8")
	fh_save_temp_fr.write("")
	fh_save_temp_fr.close()

	##Preparing data for GIZA++
	for key,values in books.items():
		if key != 1000007:
			#Create object
			try:
				bookObject = Alignements(values['book_id'], values['original_title'],
				                       values['translated_title'], values['file'])
			except AttributeError:
				pass # ne fait rien
			try:
				bookObject.GIZA()
			except FileNotFoundError:
				pass

	sys.exit("Done here1")
	"""
    """
	for key,values in books.items():
		if key != 1000007:
			#Create object
			try:
				bookObject = Alignements(values['book_id'], values['original_title'],
				                       values['translated_title'], values['file'])
			except AttributeError:
				pass # ne fait rien
			try:
				bookObject.checkForceTranscriptions()
			except FileNotFoundError:
				pass

	sys.exit("Yeps!")
	"""
    ##Alice -> last modification on reverse stemming, the method improved
    # Returning to improving wordAlignments! -> Idea is to change the getClosest to
    # getClosest to the right but

    """
	error_log = "../Alignements/log/postproc_err.txt"
	fh_error_log = open(error_log,"w",encoding="utf8")
	countBooks = len(books)
	for key,values in books.items():
		try:
			print("Book number: "+ str(countBooks))
			AlignmentObject = Alignements(values['book_id'], values['original_title'],
					                       values['translated_title'], values['file'])
		except AttributeError:
			pass
		#AlignmentObject.createPipeline()
		#AlignmentObject.alignChapters()
		try:
			AlignmentObject.postProcessing()
		except FileNotFoundError:
			print("Passing this chapter!")
			print(AlignmentObject.chapters)
			fh_error_log.write(str(values['book_id'])+"\n")
			pass
		countBooks -= 1

	"""

    # Finding the best n alignmnets
    """
	tab1= []
	tab2 = []
	for k,v in books.items():
		try:
			AlignObject = Alignements(v['book_id'],v['original_title'],
		                     v['translated_title'],v['file'])
		except AttributeError:
			pass

		for chapter in AlignObject.chapters:
			tab1.append(float(chapter[5]))
			tab2.append(int(chapter[0]))

	tab3 = sorted(range(len(tab1)), key=lambda i: tab1[i], reverse=True)[:5]
	for index in tab3:
		print(tab2[index])
	"""
    """
	Nietzche = Alignements(books[33]['book_id'],books[33]['original_title'],
	                     books[33]['translated_title'],books[33]['file'])
	Nietzche.createPipeline()
	Nietzche.alignChapters()
	Nietzche.postProcessing()
	Nietzche.forceTranscriptions()
	Nietzche.extractGIZAsentAlignments()

	Nietzche.finalAlignment()

	Nietzche.final_db_Integration()
	Nietzche.visaulize_html()
	"""
    # Pipeline pour Alice
    """
	#Pour lancer uniquement sur id 11 = Alice au pays des merveilles
	Alice = Alignements(books[11]['book_id'],books[11]['original_title'],
	                     books[11]['translated_title'],books[11]['file'])
	"""
    # 2. Creation du dossier de la chaine de traitement
    # Creating the processingFolder
    # Alice.createProcessingFolder()

    # 3. Conversion du ls & lc au format txt
    # Alice.convertFormat()

    ############################################
    # Travail Manuel -> Decoupage en Chapitres #
    ############################################

    # Version Automatique
    # Alice.extractChapters()

    # Tokenisation & Decoupage en phrases
    # Alice.createPipeline()

    # Alignement avec LFAligner
    # Alice.alignChapters()



    #################################################
    #   Creation du pipeline pour tous les livres & Decoupages en chapitres
    #   # semi automatique

    # Other pipelines
    """
	#Alignements
	#alignObject.createProcessingFolder()
	#alignObject.convertFormat()
	#alignObject.GIZA()

	alignObject.createPipeline()
	alignObject.alignChapters()

	alignObject.createProcessingFolder()
	alignObject.createPipeline()
	#alignObject.alignChapters()
	alignObject.postProcessing()
	"""

    # Chapter Extraction and creating raw.txt
    # alignObject.createPipeline()
    # alignObject.alignChapters()
    # alignObject.extractChapters("VOL. [IVX]+\.","CHAPITRE [IVXCLD]+.?\n")
    # alignObject.STOPWORD_en = "End of Project Gutenberg's"
    # alignObject.STOPWORD_fr = "Cet ouvrage est le 747e"

    ## Pour calculer de façon simple totalMinutes alignés

    # Pour calculer le temps total pour tout le corpus

    # Pour calculer le temps total aligné

    # Running all the pipeline for all the books
    """
	totalsum = 0.0


	for key,values in books.items():
		try:
			myObject = Alignements(values['book_id'], values['original_title'],
			                       values['translated_title'], values['file'])

		except AttributeError:
			pass
		if myObject.book_id ==  1000007 or values['book_id'] == 1000007:
			pass
		else:
			try:
				print("\t-----"+str(values['book_id']), values['original_title'],
					                       values['translated_title'], values['file']+"-----")
			except TypeError or AttributeError:
				pass

			else:
				try:
					pass
					#myObject.createProcessingFolder()
					#myObject.createPipeline()
					#myObject.alignChapters()
					myObject.postProcessing()
				except IOError or UnicodeError or UnicodeDecodeError:
					pass




	print(totalsum)
	"""

    # Running GIZA++ on all the books
    """
	fh_save_temp = open("../Alignements/GIZA/ls.txt","w",encoding="utf8")
	fh_save_temp.write("")
	fh_save_temp.close()
	fh_save_temp_fr = open("../Alignements/GIZA/lc.txt","w",encoding="utf8")
	fh_save_temp_fr.write("")
	fh_save_temp_fr.close()

	##Preparing data for GIZA++
	for key,values in books.items():
		if key != 1000007:
			#Create object
			try:
				bookObject = Alignements(values['book_id'], values['original_title'],
				                       values['translated_title'], values['file'])
			except AttributeError:
				pass # ne fait rien
			try:
				bookObject.GIZA()
			except FileNotFoundError:
				pass
	"""

    # Running forceAlignments for all the books
    """
	for key,values in books.items():

		#Create object
		try:
			bookObject = Alignements(values['book_id'], values['original_title'],
			                       values['translated_title'], values['file'])
		except AttributeError:
			pass # ne fait rien

		bookObject.forceTranscriptions()
	"""
