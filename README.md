

Translation-Augmented-LibriSpeech-Corpus
========================================

This project is an extension of LibriSpeech ASR Corpus which is a corpus of approximatively 1000 hours of speech aligned with their transcriptions (`LibriSpeech: an ASR corpus based on public domain audio books", Vassil Panayotov, Guoguo Chen, Daniel Povey and Sanjeev Khudanpur, ICASSP 2015
<http://www.danielpovey.com/files/2015_icassp_librispeech.pdf>`_) for speech translation systems. 

Speech recordings and source texts are originally from `Gutenberg Project
<http://www.gutenberg.org>`_ which is a digital library of public domain books read by volunteers. We gathered open domain ebooks in French and aligned chapters from LibriSpeech project with the chapters of translated e-books. Furthermore, we aligned the transcriptions with their respective translations in order to provide a corpus of speech recordings aligned with their translations. Our corpus is licenced under a `Creative Commons Attribution 4.0 License
<https://creativecommons.org/licenses/by/4.0/legalcode>`_ 


Project Structure
=================
*Folder name convention corresponds to book id's from LibriSpeech Project and Gutenberg Project. For example: folder 11 would correspond
to "Alice's Adventures in Wonderland by Lewis Carroll" at both Gutenberg and LibriSpeech Projects. *

This corpus is composed of three sections:
- Audio Files: Resegmented audio files for each book id in the project
- HTML alignment visualisation interface : HTML visualisation for textual alignments with audio files avaliable to listen
- Alignments folder: All of the processing steps: pre-processing, alignment, forced transcriptions, forced alignments, etc.

- TA LibriSpeech Corpus(~26GB)

	- **audio_files/** : folder contains ~130.000 audio segments aligned with their translations
		- book id/
			- Chapter id/
				- book_id-chapter_id-sentence_number.wav
				- reader_id-chapter_id-sentence_number.wav ** if the corpus comes from the dev/test pool of LibriSpeech

	- **Alignments/** : Folder contains processing steps used in different alignment stages
		chapter_id/
			-raw.txt
	- **en/** : Folder contains preProcessing steps for english used before alignment
		- book id/ 	
			-chapter_id/ *Contains an individual chapter*
				- raw.txt *Raw text file of a chapter*
				- raw.para *p tags added to raw text files*
				- raw.sent *NLTK sentence split files, 1 sentence per line*
				- raw.stem *NLTK stemmer applied to sentence split file*
				- en.tokens *File contains tokens of the chapter*
	- **fr/** Contains nltk processing steps for each chapter for a given book

	- **speechcoco_API/**
		- speechcoco/
			- __init__.py
			- speechcoco.py
			- setup.py

	- ls_book_id.txt (Gutenberg original text)
	- lc_book_id.format (pdf,epub,txt,...)
	- lc_book_id.htmlz






