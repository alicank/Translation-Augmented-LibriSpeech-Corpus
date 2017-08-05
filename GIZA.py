#!/usr/bin/python
# -*- coding: utf-8 -*-


import sys,os,re
import alignements
import dataset
import nltk.data
from nltk.stem import SnowballStemmer
from nltk.stem.snowball import FrenchStemmer
from nltk.tokenize import TreebankWordTokenizer
from shutil import copyfile
import diff_match_patch
class GIZA:



	def __init__(self):
		self.librispeech_books = self.initialize()
		self.procFolder = self.createProcessingFolder()

	def initialize(self):
		table = get_database("librispeech")
		books = table.distinct('book_id')

		collection = []
		for book in books:
			book_id = book['book_id']
			row = table.find(book_id=book_id)
			row = list(row)
			collection.append(row[0])
		return collection

	def createProcessingFolder(self):
		folder = "../Alignements/GIZA_data"
		if not os.path.exists(folder):
			os.mkdir(folder)
		return folder

	def alignGutenberg(self):
		for book in self.librispeech_books:
			if re.match(r"gutenberg",book['source'],re.I) and book['book_id'] != 1000007:
				#1st locate ls_lc files and verify if they exist
				book_folder = "../Alignements/data/"+str(book['book_id'])
				lsFiles = []
				lcFiles = []
				for items in os.listdir(book_folder):
					if items.startswith("ls_"):
						lsFiles.append(items)
					elif items.startswith("lc_"):
						lcFiles.append(items)

				## If the length of the two tables are the same -> no manual intervention
				if len(lsFiles) == len(lcFiles):

					lsFile = book_folder+"/"+lsFiles[0]
					lcFile = book_folder+"/"+lcFiles[0]
					traitement = (lsFile,lcFile)

					sys.stdout.write("Creating processing folder for book: "+
					                 str(book['book_id'])+" \n")

					#1. Create folder
					procFolder = self.procFolder+"/"+str(book['book_id'])
					if not os.path.exists(procFolder):
						os.mkdir(procFolder)
					if not os.path.exists(procFolder+"/raw.ls"):
						copyfile(lsFile,procFolder+"/raw.ls")
					if not os.path.exists(procFolder + "/raw.lc"):
						copyfile(lcFile,procFolder+"/raw.lc")


					#2. Add Paragraph tags
					sys.stdout.write("Adding para tags for book: " +
					                 str(book['book_id']) + " \n")
					#Entree
					fh_book_ls = open(traitement[0], "r", encoding="utf8")
					fh_book_lc = open(traitement[1], "r", encoding="utf8")

					#Sortie
					fh_save_para_ls = open(procFolder+"/ls.para","w",encoding="utf8")
					fh_save_para_lc = open(procFolder+"/lc.para","w",encoding="utf8")

					#Text_strings
					raw_lines_ls = fh_book_ls.read()
					raw_lines_lc = fh_book_lc.read()

					# Regex
					para_lines_ls = "<p>\n"
					para_lines_lc = "<p>\n"
					subst = "\\n<p>"
					regex = r"\n+$"

					#Search and replace + write to saveFile
					para_lines_ls += re.sub(regex, subst, raw_lines_ls, 0, re.MULTILINE)
					para_lines_lc += re.sub(regex, subst, raw_lines_lc, 0, re.MULTILINE)
					fh_save_para_ls.write(para_lines_ls)
					fh_save_para_lc.write(para_lines_lc)

					#Close filehandles
					fh_book_lc.close()
					fh_book_ls.close()
					fh_save_para_lc.close()
					fh_save_para_ls.close()

					#. Sentence Split
					sys.stdout.write("Sentence split for book: " +
					                 str(book['book_id']) + " \n")


					#Entree
					fh_book_ls = open(procFolder+"/ls.para", "r", encoding="utf8")
					fh_book_lc = open(procFolder+"/lc.para", "r", encoding="utf8")

					#Sortie
					fh_save_sent_ls = open(procFolder+"/ls.sent","w",encoding="utf8")
					fh_save_sent_lc = open(procFolder+"/lc.sent","w",encoding="utf8")

					#Input + Strip
					tab_text = fh_book_ls.readlines()
					tab_text_stripped = [tab_text[x].strip() for x in range(len(tab_text))]

					tab_text_lc = fh_book_lc.readlines()
					tab_text_lc_stripped = [tab_text_lc[x].strip() for x in range(len(tab_text_lc))]

					#Sentence split + write to file
					sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')
					fh_save_sent_ls.write('\n'.join(
						sent_detector.tokenize(' '.join(tab_text_stripped))))

					sent_detector = nltk.data.load('tokenizers/punkt/french.pickle')
					fh_save_sent_lc.write('\n'.join(
						sent_detector.tokenize(' '.join(tab_text_lc_stripped))))

					#Filehandles close
					fh_book_lc.close()
					fh_book_ls.close()
					fh_save_sent_ls.close()
					fh_save_sent_lc.close()

					#4. Stemming
					sys.stdout.write("Snowball Stemmer on book: " +
					                 str(book['book_id']) + " \n")

					# Entree
					fh_book_ls = open(procFolder+"/ls.sent", "r", encoding="utf8")
					fh_book_lc = open(procFolder+"/lc.sent", "r", encoding="utf8")

					# Sortie
					fh_save_stem_ls = open(procFolder + "/ls.stem", "w", encoding="utf8")
					fh_save_stem_lc = open(procFolder + "/lc.stem", "w", encoding="utf8")

					#Regex
					tab_text = fh_book_ls.readlines()
					tab_text = [(re.sub(r'\n', r" \\n ", x)) for x in tab_text]

					tab_text_lc = fh_book_lc.readlines()
					tab_text_lc = [(re.sub(r'\n', r" \\n ", x)) for x in tab_text_lc]

					#Initialize stemmer
					snowball_stemmer_ls = SnowballStemmer("english")
					snowball_stemmer_lc = FrenchStemmer()

					#Tokens file
					tok_file_ls = open(procFolder + "/en_tokens.txt", "w", encoding="utf8")
					tok_file_lc = open(procFolder + "/fr_tokens.txt", "w", encoding="utf8")

					#Tokenizer
					tokenizer = TreebankWordTokenizer()
					tokens_ls = tokenizer.tokenize(' '.join(tab_text))
					tokens_lc = tokenizer.tokenize(' '.join(tab_text_lc))

					# Stemming + regex
					stemmed_ls = [snowball_stemmer_ls.stem(x) for x in tokens_ls]

					for i in range(len(stemmed_ls)):
						if stemmed_ls[i] != "<" and stemmed_ls[i] != ">" and stemmed_ls[i] != "p" and stemmed_ls[
							i] != "\\n":
							tok_file_ls.write("0\t" + stemmed_ls[i] + "\t" + tokens_ls[i] + "\n")

					stemmed_ls = [(re.sub(r'\\n', r"\n", stemmed_ls[x])) for x in range(len(stemmed_ls))]

					stemmed_lc = [snowball_stemmer_lc.stem(x) for x in tokens_lc]

					for i in range(len(stemmed_lc)):
						if stemmed_lc[i] != "<" and stemmed_lc[i] != ">" and stemmed_lc[i] != "p" and stemmed_lc[
							i] != "\\n":
							tok_file_lc.write("0\t" + stemmed_lc[i] + "\t" + tokens_lc[i] + "\n")

					stemmed_lc = [(re.sub(r'\\n', r"\n", stemmed_lc[x])) for x in range(len(stemmed_lc))]

					#Writing to file
					fh_save_stem_ls.write(' '.join(stemmed_ls))
					fh_save_stem_lc.write(' '.join(stemmed_lc))

					#Close Filehandles
					tok_file_lc.close()
					tok_file_ls.close()
					fh_save_stem_ls.close()
					fh_save_stem_lc.close()
					fh_book_ls.close()
					fh_book_lc.close()


					#. Aligning Chapters with LFAligner
					sys.stdout.write("Aligning Chapters with LFAligner for book: " +
					                 str(book['book_id']) + " \n")


					fullPath = "/home/alican/Documents/LIG-StageM2/LibriSpeech/Alignements/GIZA_data/" + str(book['book_id'])
					en_file = fullPath+"/ls.stem"
					fr_file = fullPath+"/lc.stem"
					lfAlignerPath = "../Alignements/data/aligner/scripts/LF_aligner_3.11_with_modules.pl"
					##########LFAligner Expects FULL PATH! ##############
					cmd = "perl " + lfAlignerPath + \
					      " --segment=\"n\" --infiles \"" + en_file + "\",\"" + fr_file \
					      + "\" --languages=\"en\",\"fr\""

					log = open(self.procFolder +"/"+ str(book['book_id']) + "/info.meta", "w")
					command = alignements.Command(cmd, log)
					command.run(timeout=40)
				else:
					#There is only one ls file
					if len(lsFiles) == 1:
						#Then concat all the lc files into one and do the same steps
						lsFile = book_folder + "/" + lsFiles[0]
						start = book_folder+"/"
						etc = start.join(sorted_nicely(lcFiles))
						etc = book_folder+"/"+ etc
						etc = re.sub(r"txt","txt ",etc,0,re.I)

						os.system("cat " + etc + " > " + book_folder + "/temp.lc")
						lcFile = book_folder + "/temp.lc"

						traitement = (lsFile, lcFile)
						sys.stdout.write("Creating processing folder for book: " +
						                 str(book['book_id']) + " \n")

						# 1. Create folder
						procFolder = self.procFolder + "/" + str(book['book_id'])
						if not os.path.exists(procFolder):
							os.mkdir(procFolder)
						if not os.path.exists(procFolder + "/raw.ls"):
							copyfile(lsFile, procFolder + "/raw.ls")
						if not os.path.exists(procFolder + "/raw.lc"):
							copyfile(lcFile, procFolder + "/raw.lc")

						# 2. Add Paragraph tags
						sys.stdout.write("Adding para tags for book: " +
						                 str(book['book_id']) + " \n")
						# Entree
						fh_book_ls = open(traitement[0], "r", encoding="utf8")
						fh_book_lc = open(traitement[1], "r", encoding="utf8")

						# Sortie
						fh_save_para_ls = open(procFolder + "/ls.para", "w", encoding="utf8")
						fh_save_para_lc = open(procFolder + "/lc.para", "w", encoding="utf8")

						# Text_strings
						raw_lines_ls = fh_book_ls.read()
						raw_lines_lc = fh_book_lc.read()

						# Regex
						para_lines_ls = "<p>\n"
						para_lines_lc = "<p>\n"
						subst = "\\n<p>"
						regex = r"\n+$"

						# Search and replace + write to saveFile
						para_lines_ls += re.sub(regex, subst, raw_lines_ls, 0, re.MULTILINE)
						para_lines_lc += re.sub(regex, subst, raw_lines_lc, 0, re.MULTILINE)
						fh_save_para_ls.write(para_lines_ls)
						fh_save_para_lc.write(para_lines_lc)

						# Close filehandles
						fh_book_lc.close()
						fh_book_ls.close()
						fh_save_para_lc.close()
						fh_save_para_ls.close()

						#Remove the lcFile
						if os.path.exists(lcFile):
							os.remove(lcFile)

						# . Sentence Split
						sys.stdout.write("Sentence split for book: " +
						                 str(book['book_id']) + " \n")

						# Entree
						fh_book_ls = open(procFolder + "/ls.para", "r", encoding="utf8")
						fh_book_lc = open(procFolder + "/lc.para", "r", encoding="utf8")

						# Sortie
						fh_save_sent_ls = open(procFolder + "/ls.sent", "w", encoding="utf8")
						fh_save_sent_lc = open(procFolder + "/lc.sent", "w", encoding="utf8")

						# Input + Strip
						tab_text = fh_book_ls.readlines()
						tab_text_stripped = [tab_text[x].strip() for x in range(len(tab_text))]

						tab_text_lc = fh_book_lc.readlines()
						tab_text_lc_stripped = [tab_text_lc[x].strip() for x in range(len(tab_text_lc))]

						# Sentence split + write to file
						sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')
						fh_save_sent_ls.write('\n'.join(
							sent_detector.tokenize(' '.join(tab_text_stripped))))

						sent_detector = nltk.data.load('tokenizers/punkt/french.pickle')
						fh_save_sent_lc.write('\n'.join(
							sent_detector.tokenize(' '.join(tab_text_lc_stripped))))

						# Filehandles close
						fh_book_lc.close()
						fh_book_ls.close()
						fh_save_sent_ls.close()
						fh_save_sent_lc.close()

						# 4. Stemming
						sys.stdout.write("Snowball Stemmer on book: " +
						                 str(book['book_id']) + " \n")

						# Entree
						fh_book_ls = open(procFolder + "/ls.sent", "r", encoding="utf8")
						fh_book_lc = open(procFolder + "/lc.sent", "r", encoding="utf8")

						# Sortie
						fh_save_stem_ls = open(procFolder + "/ls.stem", "w", encoding="utf8")
						fh_save_stem_lc = open(procFolder + "/lc.stem", "w", encoding="utf8")

						# Regex
						tab_text = fh_book_ls.readlines()
						tab_text = [(re.sub(r'\n', r" \\n ", x)) for x in tab_text]

						tab_text_lc = fh_book_lc.readlines()
						tab_text_lc = [(re.sub(r'\n', r" \\n ", x)) for x in tab_text_lc]

						# Initialize stemmer
						snowball_stemmer_ls = SnowballStemmer("english")
						snowball_stemmer_lc = FrenchStemmer()

						# Tokens file
						tok_file_ls = open(procFolder + "/en_tokens.txt", "w", encoding="utf8")
						tok_file_lc = open(procFolder + "/fr_tokens.txt", "w", encoding="utf8")

						# Tokenizer
						tokenizer = TreebankWordTokenizer()
						tokens_ls = tokenizer.tokenize(' '.join(tab_text))
						tokens_lc = tokenizer.tokenize(' '.join(tab_text_lc))

						# Stemming + regex
						stemmed_ls = [snowball_stemmer_ls.stem(x) for x in tokens_ls]

						for i in range(len(stemmed_ls)):
							if stemmed_ls[i] != "<" and stemmed_ls[i] != ">" and stemmed_ls[i] != "p" and stemmed_ls[
								i] != "\\n":
								tok_file_ls.write("0\t" + stemmed_ls[i] + "\t" + tokens_ls[i] + "\n")

						stemmed_ls = [(re.sub(r'\\n', r"\n", stemmed_ls[x])) for x in range(len(stemmed_ls))]

						stemmed_lc = [snowball_stemmer_lc.stem(x) for x in tokens_lc]

						for i in range(len(stemmed_lc)):
							if stemmed_lc[i] != "<" and stemmed_lc[i] != ">" and stemmed_lc[i] != "p" and stemmed_lc[
								i] != "\\n":
								tok_file_lc.write("0\t" + stemmed_lc[i] + "\t" + tokens_lc[i] + "\n")

						stemmed_lc = [(re.sub(r'\\n', r"\n", stemmed_lc[x])) for x in range(len(stemmed_lc))]

						# Writing to file
						fh_save_stem_ls.write(' '.join(stemmed_ls))
						fh_save_stem_lc.write(' '.join(stemmed_lc))

						# Close Filehandles
						tok_file_ls.close()
						tok_file_lc.close()
						fh_save_stem_ls.close()
						fh_save_stem_lc.close()
						fh_book_ls.close()
						fh_book_lc.close()

						# . Aligning Chapters with LFAligner
						sys.stdout.write("Aligning Chapters with LFAligner for book: " +
						                 str(book['book_id']) + " \n")

						fullPath = "/home/alican/Documents/LIG-StageM2/LibriSpeech/Alignements/GIZA_data/" + str(
							book['book_id'])
						en_file = fullPath + "/ls.stem"
						fr_file = fullPath + "/lc.stem"
						lfAlignerPath = "../Alignements/data/aligner/scripts/LF_aligner_3.11_with_modules.pl"
						##########LFAligner Expects FULL PATH! ##############
						cmd = "perl " + lfAlignerPath + \
						      " --segment=\"n\" --infiles \"" + en_file + "\",\"" + fr_file \
						      + "\" --languages=\"en\",\"fr\""

						log = open(self.procFolder + "/" + str(book['book_id']) + "/info.meta", "w")
						command = alignements.Command(cmd, log)
						command.run(timeout=40)

	def alignOthers(self):
		for book in self.librispeech_books:
			if not re.match(r"gutenberg",book['source'],re.I):
				book_folder = "../Alignements/data/" + str(book['book_id'])
				lsFiles = []
				lcFiles = []
				for items in os.listdir(book_folder):
					if items.startswith("ls") and items.endswith("txt"):
						lsFiles.append(items)
					elif items.startswith("lc") and items.endswith("txt"):
						lcFiles.append(items)
				if len(lsFiles) == len(lcFiles):


					lsFile = book_folder + "/" + lsFiles[0]
					lcFile = book_folder + "/" + lcFiles[0]
					traitement = (lsFile, lcFile)

					sys.stdout.write("Creating processing folder for book: " +
					                 str(book['book_id']) + " \n")

					# 1. Create folder
					procFolder = self.procFolder + "/" + str(book['book_id'])
					if not os.path.exists(procFolder):
						os.mkdir(procFolder)
					if not os.path.exists(procFolder + "/raw.ls"):
						copyfile(lsFile, procFolder + "/raw.ls")
					if not os.path.exists(procFolder + "/raw.lc"):
						copyfile(lcFile, procFolder + "/raw.lc")


					# 2. Add Paragraph tags
					sys.stdout.write("Adding para tags for book: " +
					                 str(book['book_id']) + " \n")
					#Preprocessing before
					os.system("perl -pi -e 's/-\n/-/g' " +procFolder + "/raw.lc" )

					os.system("perl -pi -e 's/^(https?:\/\/)?[0-9a-zA-Z]+\.[-_0-9a-zA-Z]+\.[0-9a-zA-Z]+$//g' " + procFolder + "/raw.lc")
					os.system("perl -pi -e 's/- ?\d+ ?-//g' " +procFolder+"/raw.lc")
					os.system("perl -pi -e 's/\d+\n//g' " + procFolder + "/raw.lc")

					# Entree
					fh_book_ls = open(procFolder + "/raw.ls", "r", encoding="utf8")
					fh_book_lc = open(procFolder + "/raw.lc", "r", encoding="utf8")

					# Sortie
					fh_save_para_ls = open(procFolder + "/ls.para", "w", encoding="utf8")
					fh_save_para_lc = open(procFolder + "/lc.para", "w", encoding="utf8")

					# Text_strings
					raw_lines_ls = fh_book_ls.read()
					raw_lines_lc = fh_book_lc.read()

					# Regex
					para_lines_ls = "<p>\n"
					para_lines_lc = "<p>\n"
					subst = "\\n<p>"
					regex = r"\n+$"

					# Search and replace + write to saveFile
					para_lines_ls += re.sub(regex, subst, raw_lines_ls, 0, re.MULTILINE)
					para_lines_lc += re.sub(regex, subst, raw_lines_lc, 0, re.MULTILINE)
					fh_save_para_ls.write(para_lines_ls)
					fh_save_para_lc.write(para_lines_lc)

					# Close filehandles
					fh_book_lc.close()
					fh_book_ls.close()
					fh_save_para_lc.close()
					fh_save_para_ls.close()

					# . Sentence Split
					sys.stdout.write("Sentence split for book: " +
					                 str(book['book_id']) + " \n")

					# Entree
					fh_book_ls = open(procFolder + "/ls.para", "r", encoding="utf8")
					fh_book_lc = open(procFolder + "/lc.para", "r", encoding="utf8")

					# Sortie
					fh_save_sent_ls = open(procFolder + "/ls.sent", "w", encoding="utf8")
					fh_save_sent_lc = open(procFolder + "/lc.sent", "w", encoding="utf8")

					# Input + Strip
					tab_text = fh_book_ls.readlines()
					tab_text_stripped = [tab_text[x].strip() for x in range(len(tab_text))]

					tab_text_lc = fh_book_lc.readlines()
					tab_text_lc_stripped = [tab_text_lc[x].strip() for x in range(len(tab_text_lc))]

					# Sentence split + write to file
					sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')
					fh_save_sent_ls.write('\n'.join(
						sent_detector.tokenize(' '.join(tab_text_stripped))))

					sent_detector = nltk.data.load('tokenizers/punkt/french.pickle')
					fh_save_sent_lc.write('\n'.join(
						sent_detector.tokenize(' '.join(tab_text_lc_stripped))))

					# Filehandles close
					fh_book_lc.close()
					fh_book_ls.close()
					fh_save_sent_ls.close()
					fh_save_sent_lc.close()

					# 4. Stemming
					sys.stdout.write("Snowball Stemmer on book: " +
					                 str(book['book_id']) + " \n")

					# Entree
					fh_book_ls = open(procFolder + "/ls.sent", "r", encoding="utf8")
					fh_book_lc = open(procFolder + "/lc.sent", "r", encoding="utf8")

					# Sortie
					fh_save_stem_ls = open(procFolder + "/ls.stem", "w", encoding="utf8")
					fh_save_stem_lc = open(procFolder + "/lc.stem", "w", encoding="utf8")

					# Regex
					tab_text = fh_book_ls.readlines()
					tab_text = [(re.sub(r'\n', r" \\n ", x)) for x in tab_text]

					tab_text_lc = fh_book_lc.readlines()
					tab_text_lc = [(re.sub(r'\n', r" \\n ", x)) for x in tab_text_lc]

					# Initialize stemmer
					snowball_stemmer_ls = SnowballStemmer("english")
					snowball_stemmer_lc = FrenchStemmer()

					#Tokens file
					tok_file_ls = open(procFolder + "/en_tokens.txt", "w", encoding="utf8")
					tok_file_lc = open(procFolder + "/fr_tokens.txt", "w", encoding="utf8")

					# Tokenizer
					tokenizer = TreebankWordTokenizer()
					tokens_ls = tokenizer.tokenize(' '.join(tab_text))
					tokens_lc = tokenizer.tokenize(' '.join(tab_text_lc))




					# Stemming + regex
					stemmed_ls = [snowball_stemmer_ls.stem(x) for x in tokens_ls]

					for i in range(len(stemmed_ls)):
						if stemmed_ls[i] != "<" and stemmed_ls[i] != ">" and stemmed_ls[i] != "p" and stemmed_ls[i] != "\\n":
							tok_file_ls.write("0\t" + stemmed_ls[i] + "\t" + tokens_ls[i] + "\n")

					stemmed_ls = [(re.sub(r'\\n', r"\n", stemmed_ls[x])) for x in range(len(stemmed_ls))]

					stemmed_lc = [snowball_stemmer_lc.stem(x) for x in tokens_lc]

					for i in range(len(stemmed_lc)):
						if stemmed_lc[i] != "<" and stemmed_lc[i] != ">" and stemmed_lc[i] != "p" and stemmed_lc[i] != "\\n":
							tok_file_lc.write("0\t" + stemmed_lc[i] + "\t" + tokens_lc[i] + "\n")

					stemmed_lc = [(re.sub(r'\\n', r"\n", stemmed_lc[x])) for x in range(len(stemmed_lc))]

					# Writing to file
					fh_save_stem_ls.write(' '.join(stemmed_ls))
					fh_save_stem_lc.write(' '.join(stemmed_lc))

					# Close Filehandles
					tok_file_lc.close()
					tok_file_ls.close()
					fh_save_stem_ls.close()
					fh_save_stem_lc.close()
					fh_book_ls.close()
					fh_book_lc.close()

					# . Aligning Chapters with LFAligner
					sys.stdout.write("Aligning Chapters with LFAligner for book: " +
					                 str(book['book_id']) + " \n")

					fullPath = "/home/alican/Documents/LIG-StageM2/LibriSpeech/Alignements/GIZA_data/" + str(
						book['book_id'])
					en_file = fullPath + "/ls.stem"
					fr_file = fullPath + "/lc.stem"
					lfAlignerPath = "../Alignements/data/aligner/scripts/LF_aligner_3.11_with_modules.pl"
					##########LFAligner Expects FULL PATH! ##############
					cmd = "perl " + lfAlignerPath + \
					      " --segment=\"n\" --infiles \"" + en_file + "\",\"" + fr_file \
					      + "\" --languages=\"en\",\"fr\""

					log = open(self.procFolder + "/" + str(book['book_id']) + "/info.meta", "w")
					command = alignements.Command(cmd, log)
					command.run(timeout=40)
				else:
					if lcFiles == []:
						continue
					try:
						wc_ls = alignements.wc(book_folder+"/"+sorted_nicely(lsFiles)[0])
						wc_lc = alignements.wc(book_folder + "/" + sorted_nicely(lcFiles)[0])
					except FileNotFoundError:
						pass
					print(wc_ls)
					print(wc_lc)

	def getGlobalQuality(self,path):
		fh = open(path,"r",encoding="utf8")
		file = fh.read()
		searchObj = re.search(r"Quality (.*)$",file,re.M)
		if searchObj:
			return searchObj.group(1)
		else:
			return 0

	def postProcessing(self):
		totalCount = 0
		for books in os.listdir(self.procFolder):
			contents = os.listdir(self.procFolder+"/"+books)
			procFolder = self.procFolder+"/"+books

			alignFolder = filter(lambda x: x.startswith("align"), contents)
			alignFolder = list(alignFolder)
			if alignFolder != []:
				#Get the quality of the global alignment
				quality = float(self.getGlobalQuality(self.procFolder+"/"+books+"/info.meta"))
				if quality > 0.0 and quality < 0.3:
					pass
					#pass completely
				elif quality > 0.3 and quality < 0.8 :
					continue
					#Only take the best sentences
					print("Working on",quality,books)
					create_ls_lc(self.procFolder+"/"+books+"/"+alignFolder[0])
					#print(self.procFolder+"/"+books+"/"+alignFolder[0])

					if not os.path.exists(self.procFolder+"/"+books+"/"+alignFolder[0] +  "/reversed_stem_ls.txt"):
						language = "en"
						tok_file = procFolder + "/en_tokens.txt"
						stem_file = self.procFolder+"/"+books+"/"+alignFolder[0] + "/stem_ls.txt"
						sortie_ls = self.procFolder+"/"+books+"/"+alignFolder[0] +  "/reversed_stem_ls.txt"
						fh_sortie_ls = open(sortie_ls, "w", encoding="utf8")

						alignements.reverseStemming(language, tok_file, stem_file, fh_sortie_ls)
						fh_sortie_ls.close()
					if not os.path.exists(self.procFolder+"/"+books+"/"+alignFolder[0] + "/reversed_stem_lc.txt"):
						language = "fr"
						tok_file = procFolder + "/fr_tokens.txt"
						stem_file = self.procFolder+"/"+books+"/"+alignFolder[0] + "/stem_lc.txt"
						sortie_lc = self.procFolder+"/"+books+"/"+alignFolder[0] + "/reversed_stem_lc.txt"
						fh_sortie_lc = open(sortie_lc, "w", encoding="utf8")
						print("Starting reverse stemming!")
						alignements.reverseStemming(language, tok_file, stem_file, fh_sortie_lc)
						fh_sortie_lc.close()

					print("Starting extracting sents!")
					extractBisents(self.procFolder+"/"+books+"/"+alignFolder[0],1.0)

					sys.exit(":)")

				elif quality >= 0.8:
					# Only take the best sentences
					print("Working on", quality, books)
					create_ls_lc(self.procFolder + "/" + books + "/" + alignFolder[0])
					# print(self.procFolder+"/"+books+"/"+alignFolder[0])

					if not os.path.exists(self.procFolder + "/" + books + "/" + alignFolder[
						0] + "/reversed_stem_ls.txt"):
						language = "en"
						tok_file = procFolder + "/en_tokens.txt"
						stem_file = self.procFolder + "/" + books + "/" + alignFolder[0] + "/stem_ls.txt"
						sortie_ls = self.procFolder + "/" + books + "/" + alignFolder[0] + "/reversed_stem_ls.txt"
						fh_sortie_ls = open(sortie_ls, "w", encoding="utf8")

						alignements.reverseStemming(language, tok_file, stem_file, fh_sortie_ls)
						fh_sortie_ls.close()
					if not os.path.exists(self.procFolder + "/" + books + "/" + alignFolder[
						0] + "/reversed_stem_lc.txt"):
						language = "fr"
						tok_file = procFolder + "/fr_tokens.txt"
						stem_file = self.procFolder + "/" + books + "/" + alignFolder[0] + "/stem_lc.txt"
						sortie_lc = self.procFolder + "/" + books + "/" + alignFolder[0] + "/reversed_stem_lc.txt"
						fh_sortie_lc = open(sortie_lc, "w", encoding="utf8")
						print("Starting reverse stemming!")
						alignements.reverseStemming(language, tok_file, stem_file, fh_sortie_lc)
						fh_sortie_lc.close()

					print("Starting extracting sents!")
					count = extractBisents(self.procFolder + "/" + books + "/" + alignFolder[0], 0.4)
					if count == None:
						continue
					else:
						totalCount += count
			else:
				continue
		print(totalCount)

	def bringTogether(self):
		cat_tab = []

		for books in os.listdir(self.procFolder):
			if os.path.isdir(self.procFolder+"/"+books):
				contents = os.listdir(self.procFolder+"/"+books)
				procFolder = self.procFolder+"/"+books

				alignFolder = filter(lambda x: x.startswith("align"), contents)
				alignFolder = list(alignFolder)
				if alignFolder != []:
					folder_path = procFolder+"/"+alignFolder[0]

					if os.path.exists(folder_path+"/giza_ls.txt") and os.path.exists(folder_path+"/giza_lc.txt"):
						#print(folder_path)
						cat_tab.append(folder_path)

		tab_ls_paths = [item+"/giza_ls.txt" for item in cat_tab]
		tab_lc_paths = [item + "/giza_lc.txt" for item in cat_tab]
		os.system("cat " + ' '.join(tab_ls_paths) +" > " + self.procFolder+"/ls.txt")
		os.system("cat " + ' '.join(tab_lc_paths) + " > " + self.procFolder + "/lc.txt")

###Functions
def get_database(table):
	db = dataset.connect('sqlite:///../DB/csv.db')
	return db[table]

def sorted_nicely( l ):
    """ Sort the given iterable in the way that humans expect."""
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
    return sorted(l, key = alphanum_key)

def create_ls_lc(folder):
	fh = open(folder + "/aligned_ls-lc.txt", "r")

	alignedFile = fh.readlines()
	# Supprimer les <p>
	alignedFile = [(re.sub(r'< p >', r"", x)) for x in alignedFile]
	fh_ls = open(folder + "/stem_ls.txt", "w")
	fh_lc = open(folder + "/stem_lc.txt", "w")
	fh_scores = open(folder + "/scores.txt", "w")
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

def reverse_stem(folder,file,lang):

	if lang == "en":

		stem_file = folder + "/stem_ls.txt"
		sortie_ls = folder + "/reversed_stem_ls.txt"
		diff_ls = folder + "/diff_ls.html"
		if not os.path.exists(sortie_ls):

			fh_sortie_ls = open(sortie_ls, "w", encoding="utf8")

			fh_stem = open(stem_file, "r", encoding="utf8")
			stem = fh_stem.readlines()
			# stem = [(re.sub(r'\n', r" \ğ ", stem[x])) for x in range(len(stem))]
			stem = [(re.sub(r'<\d+>', r"", stem[x])) for x in range(len(stem))]
			stem = [(re.sub(r'\ufeff', r"", stem[x])) for x in range(len(stem))]
			stem = [(re.sub(r'< p >', r"", stem[x])) for x in range(len(stem))]
			#print(stem)
			fh_ls_sent = open(file)
			ls_sent = fh_ls_sent.readlines()
			ls_sent = [(re.sub(r'<p>', r"", ls_sent[x])) for x in range(len(ls_sent))]
			ls_sent = [ls_sent[x].strip() for x in range(len(ls_sent))]
			#print(ls_sent)
			stem = ''.join(stem)
			ls_sent = ''.join(ls_sent)

			textA = stem
			textB = ls_sent

			# create a diff_match_patch object
			dmp = diff_match_patch.diff_match_patch()

			# Depending on the kind of text you work with, in term of overall length
			# and complexity, you may want to extend (or here suppress) the
			# time_out feature
			dmp.Diff_Timeout = 1800.0  # or some other value, default is 1.0 seconds

			# All 'diff' jobs start with invoking diff_main()
			diffs = dmp.diff_main(textA, textB)

			# diff_cleanupSemantic() is used to make the diffs array more "human" readable
			dmp.diff_cleanupSemanticLossless(diffs)

			#print(diffs)
			# and if you want the results as some ready to display HMTL snippet
			htmlSnippet = dmp.diff_prettyHtml(diffs)
			fh_html_ls = open(diff_ls, "w", encoding="utf8")
			html_start = """<!DOCTYPE html><html>
							<head><meta charset="UTF-8"><title>TextDiff</title></head><body><pre>"""
			fh_html_ls.write(html_start + htmlSnippet + "</pre></body></html>")
			#print(htmlSnippet)
			fh_html_ls.close()
			text = alignements.diffs_to_text(diffs)
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

	elif lang == "fr":

		stem_file = folder + "/stem_lc.txt"
		sortie_lc = folder + "/reversed_stem_lc.txt"
		diff_lc = folder + "/diff_lc.html"
		if not os.path.exists(sortie_lc):
			fh_sortie_lc = open(sortie_lc, "w", encoding="utf8")

			fh_stem = open(stem_file, "r", encoding="utf8")
			stem = fh_stem.readlines()
			# stem = [(re.sub(r'\n', r"ğ", stem[x])) for x in range(len(stem))]
			stem = [(re.sub(r'<\d+>', r"", stem[x])) for x in range(len(stem))]
			stem = [(re.sub(r'\ufeff', r"", stem[x])) for x in range(len(stem))]
			stem = [(re.sub(r'< p >', r"", stem[x])) for x in range(len(stem))]
			# print(stem)
			fh_lc_sent = open(file)
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
			dmp.Diff_Timeout = 1800.0  # or some other value, default is 1.0 seconds
			print("Starting diffs")
			# All 'diff' jobs start with invoking diff_main()
			print(dmp.diff_commonPrefix(textA,textB))
			sys.exit(":)")
			diffs = dmp.diff_main(textA, textB)
			print("diffs finished!")
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

			text = alignements.diffs_to_text(diffs)
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

def extractBisents(folder,minVal):

	extract = {}
	#Open the scores file
	fh_scores = open(folder+"/scores.txt","r",encoding="utf8")
	scores = fh_scores.readlines()
	fh_scores.close()

	for score in scores:
		infos = re.search(r"<(\d+)>(.+?)<\d+>",score.strip(),re.I)
		if infos:
			(id,score) = infos.group(1),float(infos.group(2))
		if score >= minVal:
			extract[id] = [score]

	fh_ls = open(folder+"/reversed_stem_ls.txt","r",encoding="utf8")
	ls = fh_ls.readlines()
	fh_ls.close()
	fh_lc = open(folder + "/reversed_stem_lc.txt", "r", encoding="utf8")
	lc = fh_lc.readlines()
	fh_ls.close()
	try:
		assert len(ls) == len(lc)
	except AssertionError:
		return None
	for x in range(len(ls)):
		id = re.match(r"<(\d+)>",ls[x],re.I)
		if id.group(1) in extract.keys():
			extract[id.group(1)] += ls[x].strip(),lc[x].strip()

	fh_sortie_ls = open(folder+"/giza_ls.txt","w",encoding="utf8")
	fh_sortie_lc = open(folder+"/giza_lc.txt","w",encoding="utf8")
	for k,v in extract.items():
		fh_sortie_ls.write(v[1]+"\n")
		fh_sortie_lc.write(v[2]+"\n")
	fh_sortie_ls.close()
	fh_sortie_lc.close()

	assert alignements.wc(folder+"/giza_ls.txt") == alignements.wc(folder+"/giza_lc.txt")
	return alignements.wc(folder+"/giza_ls.txt")
GIZAObj = GIZA()


GIZAObj.bringTogether()
