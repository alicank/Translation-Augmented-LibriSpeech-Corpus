#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from SPARQLWrapper import SPARQLWrapper, JSON
import re
import dataset
import urllib


class LibriSpeech:

	def __init__(self,name):
		self.corpus = name


	def totalMinutes(self):
		f = open("./CHAPTERS.txt","r",encoding="utf8")

		cpt = 0.0
		for line in f:
			if line.startswith(";ID"):
				title = line[1:].split("|")
				self.titleLine = title

			if line[0].isdigit():
				data = line.split("|")

				if data[3].strip() == self.corpus:
					cpt += float(data[2].strip())
		f.close()

		return cpt


	def data(self):

		f = open("./CHAPTERS.txt", "r", encoding="utf8")
		data = []
		for line in f:
			if line[0].isdigit():
				data.append([line.strip()])
		f.close()
		return data

	# We need book_id ! id ! reader_id!  minute !  corpus_name ! chapter ! book ! title_translation ! status
	
	def tabData(self):

		tabData = []
		for liste in self.data():
			for item in liste:
				items = item.split("|")
				if items[3].strip() == self.corpus:
					tabData.append([
						items[5].strip(), items[0].strip(), items[2].strip(),
						self.corpus, items[6].strip(), items[7].strip()
					])

		return tabData

	def fetchFrenchNames(self):
		titles = {}
		for liste in self.tabData():
			titles[liste[5]] = ""

		for books in titles.keys():

			# Replacing '
			books = re.sub(r"'", "%27", books)
			# Replacing ()
			books = re.sub(r"\(.+?\)", "", books)
			# Underscores
			book = re.sub(r" ", "_", books)
			# Dbpedia prefixe
			prefixe = "prefix sameAs: <http://www.w3.org/2002/07/owl#sameAs>"
			# resource to search
			resource = "<http://dbpedia.org/resource/" + book + ">"

			# query itself
			query = prefixe + "\n" \
							  "SELECT ?language WHERE {" \
					+ resource + " sameAs: ?language}"

			results = dev_clean.sparql(query)

			if results['results']['bindings']:  # ça veut dire qu'il y a des résultats!
				for liste in results['results']['bindings']:
					for key in liste:
						if liste[key]['value'].startswith("http://fr"):
							frenchName = re.sub(r"_", " ", liste[key]['value'])
							frenchName = re.sub(r"http://fr.dbpedia.org/resource/", "", frenchName)
							titles[books] = frenchName

		return titles

	def savetoCSV(self):
		f = open("./" + self.corpus + ".csv", "w", encoding="utf8")
		print("Saving CSV file to directory folder")

		hash = self.fetchFrenchNames()
		"""
		for k, v in hash.items():
			if v is not "":
				print(k + " ----- " + v)
		"""

		f.write("book_id\tid\tminute\tcorpus_name\tchapter\tbook\ttitle_translation\tstatus\n")
		for tabs in self.tabData():
			lastValue= ""
			if tabs[5] in hash.keys():
				lastValue = hash[tabs[5]]

			for item in tabs:

				f.write(item + "\t")


			f.write(lastValue+"\n")
		f.close()
		return("Fichier sauvegardé!")


	def sparql(self,query):
		sparql = SPARQLWrapper("http://dbpedia.org/sparql")
		sparql.setReturnFormat(JSON)

		sparql.setQuery(query)  # the previous query as a literal string

		return sparql.query().convert()












