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

- Table ** Alignments **: Table containing transcriptions, textual alignments and name of the audio file associated with a given alignment. Each row corresponds to a sentence which is aligned
- Table audio: Table that contains duration of each speech segment(seconds)
- Table alignments_evaluations: Manually annotated 200 sentences from the corpus
- Table alignments_excluded: Table used to mark sentences to be excluded in the corpus.
- Table alignments_gTranslate: automatic translation output from Google translate for each segment (transcriptions)
- Table alignments_scores: different score calculations provided with the corpus which could be used to sort the corpus from highest scores to the lowest
