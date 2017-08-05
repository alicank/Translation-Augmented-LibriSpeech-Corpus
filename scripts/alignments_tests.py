import json,os,re,sys,dataset
import alignements

books = {}
for liste in alignements.loadJson("../DB/librispeech.json"):
	books[liste['book_id']] = liste


"""
#Run all of the steps before finalAlignment
fh_log = open("./log/giza_prep_errors.txt","w",encoding="utf8")
for key,values in books.items():
	try:
		bookObject = alignements.Alignements(values['book_id'], values['original_title'],
		                       values['translated_title'], values['file'])
	except AttributeError:
		fh_log.write(str(bookObject.book_id)+ "\t" + "Attribute Error!\n")
		pass

	#Create pipeline
	try:
		bookObject.GIZA()
	except UnicodeDecodeError:
		fh_log.write(str(bookObject.book_id) +"\t" +"Unicode Decode Error!\n")
		pass
	except FileNotFoundError:
		fh_log.write(str(bookObject.book_id) + "\t" + "File Not Found Error!\n")
"""
"""
Alice = alignements.Alignements(books[11]['book_id'], books[11]['original_title'],
                    books[11]['translated_title'], books[11]['file'])
"""


#Alice.extractGIZAsentAlignments("../GIZA/15.05.2017_2")
#Alice.clear_DB_alignments()
#Alice.forceTranscriptions()
#Alice.forceAlignments()
#Alice.final_db_Integration()
#Alice.visualize_html()


#Alice.extractGIZAsentAlignments("../GIZA/12.05.2017")
#Alice.giza_recount("i où le lecteur fait connaissance avec la famille","../GIZA/11.05.2017/117-05-11.183838.alican.A3.final")
#Alice.giza_recount("i où le lecteur fait connaissance avec la famille","../GIZA/12.05.2017/117-05-12.231958.alican.A3.final")

#Book.align()
#Alice.giza_recount("i où le lecteur fait connaissance avec la famille","../GIZA/13.05.2017/117-05-14.031147.alican.A3.final")
#Alice.finalAlignment()
#Alice.extractGIZAsentAlignments("../GIZA/13.05.2017")
#Alice.visualize_html()

#Launching all the pipeline for all of the corpus
"""
for key,values in books.items():
	try:
		bookObject = alignements.Alignements(values['book_id'], values['original_title'],
			                       values['translated_title'], values['file'])
	except AttributeError:
		pass

	#Force Transcriptions
	#bookObject.forceTranscriptions()

	#Extract GIZA sent alignments for each chapter
	#bookObject.extractGIZAsentAlignments("../GIZA/13.05.2017")
"""
"""
2017: transcriptions are really short compared to the chapters (PASS)(IMPORTANT comme exemple de chapitre)
24055 (book) : transcriptions are really short compared to the chapters PASS
142304 (chapter): not recognized audio PASS (index out of range)
9455 (book) : 1 chapter not recognized PASS (index out of range)
"""
#Tests for First n books
# let's take some books to launch them in a loop

#3600 -> chapter causes a problem : excluding (101622 -> no need)
#,21700,24055,28054
idbooks = [19211,19212,19213,19214,19215] #Launch 1399 take backup
#1862




for id_book in idbooks:

	bookObject = alignements.Alignements(books[id_book]['book_id'], books[id_book]['original_title'],
								books[id_book]['translated_title'], books[id_book]['file'])



	"""
	bookObject.exceptions.append(131882)
	tab_chapters = bookObject.chapters
	for x in range(len(tab_chapters)):
		if tab_chapters[x][0] == 131882:
			bookObject.alignedChapters[x] = False
	"""

	#bookObject.exceptions.append(126208)
	#bookObject.alignedChapters[0] = False


	#Alice.clear_DB_alignments(book_id=12)
	# bookObject.createProcessingFolder()
	# bookObject.createPipeline()
	# bookObject.alignChapters()
	# bookObject.postProcessing()
	# bookObject.forceTranscriptions()
	# bookObject.extractGIZAsentAlignments("../GIZA/15.05.2017_2")
	# bookObject.finalAlignment()
	# bookObject.extractGIZAsentAlignments("../GIZA/15.05.2017_2")
	# bookObject.clear_DB_alignments(book_id=id_book)
	# bookObject.finalAlignment()
	# bookObject.forceAlignments(exclude_word_alignments=True)
	# bookObject.final_db_Integration()
	bookObject.visualize_html()


# bookObject = alignements.Alignements(books[76]['book_id'], books[76]['original_title'],
# 	                    books[76]['translated_title'], books[76]['file'])
#
# bookObject.clear_DB_alignments(book_id=76)
# bookObject.createPipeline()
# bookObject.alignChapters()
# bookObject.postProcessing()
# bookObject.forceTranscriptions()
# bookObject.finalAlignment()
# bookObject.forceAlignments(exclude_word_alignments=True)
# bookObject.final_db_Integration()
# bookObject.visualize_html()
