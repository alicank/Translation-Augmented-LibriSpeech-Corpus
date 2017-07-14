Translation-Augmented-LibriSpeech-Corpus
========================================

This project is an extension of LibriSpeech ASR Corpus which is a corpus of approximatively 1000 hours of speech aligned with their transcriptions (`LibriSpeech: an ASR corpus based on public domain audio books", Vassil Panayotov, Guoguo Chen, Daniel Povey and Sanjeev Khudanpur, ICASSP 2015
<http://www.danielpovey.com/files/2015_icassp_librispeech.pdf>`_) for speech translation systems. 

Speech recordings and source texts are originally from `Gutenberg Project
<http://www.gutenberg.org>`_ which is a digital library of public domain books read by volunteers. We gathered open domain ebooks in French and aligned chapters from LibriSpeech project with the chapters of translated e-books. Furthermore, we aligned the transcriptions with their respective translations in order to provide a corpus of speech recordings aligned with their translations. Our corpus is licenced under a `Creative Commons Attribution 4.0 License
<https://creativecommons.org/licenses/by/4.0/legalcode>`_ 


Project Structure
=================

*Folders name convention corresponds to book id's from LibriSpeech and Gutenberg projects. For example folder 11 would correspond to "Alice's Adventures in Wonderland by Lewis Carroll" at these both projects*

This corpus is composed of three sections:
- Audio Files: Resegmented audio files for each book id in the project
- HTML alignment visualisation interface : HTML visualisation for textual alignments with audio files avaliable to listen
- Alignments folder: All of the processing steps: pre-processing, alignment, forced transcriptions, forced alignments, etc.

The repository is organized as follows:

- TA LibriSpeech Corpus(~26GB)

	- **audio_files/** : folder contains ~130.000 audio segments aligned with their translations
		- book id/
			- Chapter id/
				- book_id-chapter_id-sentence_number.wav
				- reader_id-chapter_id-sentence_number.wav ** if the corpus comes from the dev/test pool of LibriSpeech

	- **Alignments/** : Folder contains processing steps used in different alignment stages
		- chapter_id/
			- stem_ls,stem_lc *Chapters to be aligned in their stemmed forms*
			- raw*.txt *hunAlign alignment files*
			- diff_ls,diff_lc.html *Google's Diff Patch Match output between original NLTK sentence split and stemmed files*
			- reversed_stem*.txt *Chapters aligned with tags and in their original sentence forms*
			- hyp,ref.txt *Hypothesis and reference files used with mwerAlign*
			- forcedAlignment*.txt *Fix of the resegmentation with speech transcriptions and sentence splits with mwerAlign*
			- original.transcpt *Transcription file from LibriSpeech Project*
			- transcriptions_aligned.txt **File to be used in forced Alignment**
			- final.txt *Contains final alignments to be uploaded to the database in tabulated text form*
			- scores.txt *hunAlign sentence match confidence values for each sentence*

	- **en/** : Folder contains preProcessing steps for english chapters used before alignment
			
		-chapter_id/ *Contains an individual chapter*
			- raw.txt *Raw text file of a chapter*
			- raw.para *p tags added to raw text files*
			- raw.sent *NLTK sentence split files, 1 sentence per line*
			- raw.stem *NLTK stemmer applied to sentence split file*
			- en.tokens *File contains tokens of the chapter*

	- **fr/** Folder contains preProcessing steps for french chapters used before alignment
	
	- **db/** Folder contains the database containing alignments, metadata and other information
		-TA-LibriSpeechCorpus.sqlite3

	- ls_book_id.txt (Gutenberg original text)
	- lc_book_id.format (pdf,epub,txt,...)
	- lc_book_id.htmlz

Database Structure
==================

Corpus is provided with diffrent tables containing useful information provided with the corpus. Database structure is organized as follows:

** Alignments **
========== =========== =========== =========== =========== =========== =========== =========== =========== =========== ===========
**Voices**     Amanda     Bronwen     Bruce     Elizabeth     Jenny      Judith      Paul         Phil       William      gTTS 
---------- ----------- ----------- ----------- ----------- ----------- ----------- ----------- ----------- ----------- -----------
Amanda        38,28       60,80       66,10       62,00       53,30       61,67       69,43       68,93       70,41       69,67
Bronwen       60,80       37,39       61,75       52,89       52,84       57,34       57,06       62,23       72,19       63,77
Bruce         66,10       61,75       38,35       59,34       54,68       64,65       57,23       54,83       77,02       69,71
Elizabeth     62,00       52,89       59,34       34,04       53,17       56,13       58,87       62,44       71,83       65,27
Jenny         53,30       52,84       54,68       53,17       38,30       56,00       61,02       60,05       69,21       62,28
Judith        61,67       57,34       64,65       56,13       56,00       47,49       64,94       67,59       72,08       64,16
Paul          69,43       57,06       57,23       58,87       61,02       64,94       40,54       60,37       73,73       68,41
Phil          68,93       62,23       54,83       62,44       60,05       67,59       60,37       45,57       79,60       75,38
William       70,41       72,19       77,02       71,83       69,21       72,08       73,73       79,60       46,47       76,74
gTTS          69,67       63,77       69,71       65,27       62,28       64,16       68,41       75,38       76,74       45,77
========== =========== =========== =========== =========== =========== =========== =========== =========== =========== ===========
