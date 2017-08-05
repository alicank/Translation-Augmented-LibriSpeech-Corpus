#!/usr/bin/python
# -*- coding: utf-8 -*-

import dataset
import urllib
import time
import os
import sys
import re
from bs4 import BeautifulSoup


def download(db,link,file_path,result):
	print("\tDownloading from " + db['source'] + "")
	if not os.path.isfile(file_path):
		urllib.request.urlretrieve(link, file_path)
		return file_path
	else:
		print("\tFile already exists! Downloading a different version from " + result['source'] + "!")
		source = result['source']
		if result['source'] == 'archive' or result['source'] == 'Archive':
			extension = file_path[-5:]
			newFile = file_path[:-5] + "_" + source + extension
			if not os.path.isfile(newFile):
				urllib.request.urlretrieve(link, file_path[:-5] + "_" + source + extension)
			else:
				"There is probably a problem somewhere!"
		else:
			extension = file_path[-4:]
			newFile = file_path[:-4] + "_" + source + extension
			if not os.path.isfile(newFile):
				urllib.request.urlretrieve(link, file_path[:-4] + "_" + source + extension)
			else:
				"There is probably a problem somewhere!"

		return newFile

def parse_organize(path, query, type,db_table):
	corpus_files = os.listdir("../corpus_data")

	bookID_prec = -99
	for result in query:
		print("Downloading the book:\t" + result['translated_title'])
		bookID = result['book_id']

		if bookID != bookID_prec:

			if type == "Gutenberg":
				if result['link'].endswith("utf-8"):
					downloaded_path = download(result, result['link'],
					                           path + "/" + str(result['book_id']) + result['link'][-10:-6],result)
					file = downloaded_path[2:]

				else:
					downloaded_path = download(result, result['link'],
					                           path + "/" + str(result['book_id']) + result['link'][-4:],result)
					file = downloaded_path[2:]

				bookID_prec = result['book_id']
			elif type == "Wikisource":

				if result['link'].endswith("djvu"):
					file = None
					pass

				else:

					if str(result['book_id'])+".txt" in corpus_files:
						print("File already downloaded passing!")
						file = "/corpus_data/" + str(result['book_id']) + ".txt"
						pass
					else:
						response = urllib.request.urlopen(result['link'])
						book = response.read()
						soup = BeautifulSoup(book, "html5lib")

						letters = soup.find_all("li", id="ca-edit")

						#For debug
						if result['book_id'] == 1938:
							file = None
							pass
						else:

							searchObj = re.search(r'title=(.+?)&amp', str(letters[0]), re.I)

							bookName = searchObj.group(1)

							link = "https://tools.wmflabs.org/wsexport/tool/book.php?lang=fr&page="

							link += bookName + "&format=txt&font="

							downloaded_path = download(result, link,
							                           path + "/" + str(result['book_id']) + ".txt",result)
							print("\tTéléchargement complété --\n " + "\t" + link)
							file = downloaded_path[2:]

				bookID_prec = result['book_id']
			elif type == "archive":

				endswith_txt = re.search(r"txt$", str(result['link']), re.I)
				if endswith_txt:
					downloaded_path = download(result, result['link'],
					                           path + "/" + str(result['book_id']) + ".html",result)

					fh = open(path + "/" + str(result['book_id']) + ".html", "r", encoding="utf8")
					text = ""
					for line in fh:
						text += line

					text = re.sub(r'<p>|<\/p>', "__lineBreak__", text)  # Etape 1
					text = re.sub(r'<.+?>', "", text)  # Etape 2
					text = re.sub(r'__lineBreak__', "\n", text)  # Etape 3
					fh.close()
					os.remove(path + "/" + str(result['book_id']) + ".html")
					fh2 = open(path + "/" + str(result['book_id']) + ".txt", "w", encoding="utf8")

					fh2.write(text)
					fh2.close()
					file = downloaded_path[2:-4] + "txt"
					bookID_prec = result['book_id']
				else:
					searchObj = re.search(r"\/(\w+)[\/]?$", str(result['link']), re.I)

					link = "https://archive.org/download/" + searchObj.group(1) + \
					       "/" + searchObj.group(1) + ".epub"

					print("Verify: " + str(result['book_id']))

					downloaded_path = download(result, link,
					                           path + "/" + str(result['book_id']) + ".epub",result)
					file = downloaded_path[2:]
					bookID_prec = result['book_id']

			elif type == "gallica":
				if str(result['book_id']) + ".txt" in corpus_files:
					print("File already downloaded passing!")
					file = "/corpus_data/" + str(result['book_id']) + ".txt"
					pass
				else:

					if result['link'].endswith("texteBrut"):

						bookID_prec = result['book_id']
						print(result['link'])
						downloaded_path = download(result, result['link'],
						                           path + "/" + str(result['book_id']) + ".html",result)

						fh = open(path + "/" + str(result['book_id']) + ".html", "r", encoding="utf8")
						text = ""
						for line in fh:
							text += line

						text = re.sub(r'<p>|<\/p>', "__lineBreak__", text)  # Etape 1
						text = re.sub(r'<.+?>', "", text)  # Etape 2
						text = re.sub(r'__lineBreak__', "\n", text)  # Etape 3
						fh.close()
						os.remove(path + "/" + str(result['book_id']) + ".html")
						fh2 = open(path + "/" + str(result['book_id']) + ".txt", "w", encoding="utf8")

						fh2.write(text)
						fh2.close()
						file = downloaded_path[2:-4] + "txt"
					else:
						print("OCR Required passing")
						file = ""
						pass

			else:
				search = re.search(r'=pdf$', result['link'], re.I)
				if not search:
					downloaded_path = download(result, result['link'],
					                           path + "/" + str(result['book_id']) + result['link'][-4:],result)
					file = downloaded_path[2:]
					bookID_prec = result['book_id']
				else:
					downloaded_path = download(result, result['link'],
					                           path + "/" + str(result['book_id']) + ".pdf",result)
					file = downloaded_path[2:]
					bookID_prec = result['book_id']

		data_insert = dict(id=result['id'], file=file)
		db_table.update(data_insert, ['id'], ensure=True)

		time.sleep(0.3)


# 1er étape récupération des liens & livres de la BD
db = dataset.connect('sqlite:///../DB/csv.db')
table = db['librispeech']
project = ""
path = "../corpus_data"

#### 1. Les liens directs
#results = table.find(source='direct_link', order_by='translated_title')
#parse_organize(path,results,project,table)

#### 2. Les liens BEQ
#results = table.find(source="beq", order_by='translated_title')
#parse_organize(path,results,project,table)

#### 3. Les liens Gutenberg
#results = table.find(source="Gutenberg", order_by='translated_title')
#project = "Gutenberg"
#parse_organize(path,results,project,table)


#### 4. Uqac & bnr & ebooksgratuit & scholarsportal
#results = table.find(source="ebooksgratuit", order_by='translated_title')
#parse_organize(path, results, project, table)

#results = table.find(source="bnr", order_by='translated_title')
#parse_organize(path, results, project, table)

#results = table.find(source="uqac", order_by='translated_title')
#parse_organize(path, results, project, table)

#results = table.find(source="scholarsportal", order_by='translated_title')
#parse_organize(path, results, project, table)

#### 5. Wikisource
#project = "Wikisource"
#results = table.find(source="Wikisource", order_by='translated_title')
#parse_organize(path, results, project, table)

#### 6. Archive
#project = "archive"
#results = table.find(source="archive", order_by='translated_title')
#results = table.find(source="Archive", order_by='translated_title')
#parse_organize(path, results, project, table)
#results = table.find(source="Archive", order_by='translated_title')

#### 7. Gallica
#project = "gallica"
#results = table.find(source="Gallica", order_by='translated_title')
#parse_organize(path, results, project, table)










