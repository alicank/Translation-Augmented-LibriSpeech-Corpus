Translation-Augmented-LibriSpeech-Corpus
========================================

This project is an extension of LibriSpeech ASR Corpus which is a corpus of approximatively 1000 hours of speech alignment with their transcriptions [LibriSpeech: an ASR corpus based on public domain audio books, Vassil Panayotov, Guoguo Chen, Daniel Povey and Sanjeev Khudanpur, ICASSP 2015](http://www.danielpovey.com/files/2015_icassp_librispeech.pdf) for speech translation systems.


Speech recordings and source texts are originally from [Gutenberg Project](https://www.http://www.gutenberg.org) which is a digital library of public domain books read by volunteers.  In this project we gathered open domain e-books in French and extracted chapters that are avaliable in LibriSpeech Project. Furthermore, we aligned english transcriptions with their respective french translations in order to provide a corpus of speech recordings aligned with their respective translations. Our corpus is licenced under a [Creative Commons Attribution 4.0 License](https://creativecommons.org/licenses/by/4.0/legalcode)

Project Structure
=================

*Folders name convention corresponds to book id's from LibriSpeech and Gutenberg projects. For example id **11** corresponds to "Alice's Adventures in Wonderland by Lewis Carroll" at both Gutenberg and LibriSpeech Projects*

This corpus is composed of **three sections**:
- Audio Files: Resegmented audio files for each book id in the project. There are in total 247 e-books (1408 chapters) and 131.395 speech segments.
- HTML visualisation interface : We provide an html interface to visualize alignments and to listen to speech segments
- Alignments folder: Additional files created in the alignment and processing steps for each book

**The repository is organized as follows**:

```
.
├── Alignments      //Folder contains additional files and metadata of alignment and processing steps
│   ├── chapter_id
│   │   ├── alignments
│   │   ├── en
│   │   └── fr
│   ├── lc_book_id.txt|pdf|epub      // Raw french e-book 
│   └── ls_book_id.txt              // Raw english e-book (Gutenberg Project)
├── audio_files         //Folder contains audio segments for each book in project
│   ├── 11                  //For example for book id 11
│   │   ├── 123440              //Chapter from dev/test pool of LibriSpeech
│   │   │   ├── 260-123440-0000.wav  //reader_id-chapter_id-sentence_id.wav
│   │   │   ├── 260-123440-0001.wav
│   │   │   └── 260-123440-0002.wav
│   │   └── 123441          //Chapter from clean-other pool of LibriSpeech
│   │       ├── 11-123441-0000.wav  //book_id-chapter_id-sentence_id.wav
│   │       └── 11-123441-0001.wav
│   └── book_id
│       └── chapter_id
│           ├── book_id-chapter_id-sentence_id.txt
│           └── **reader_id-chapter_id-sentence_id**.txt
├── index.html          //Index page of html visualisation interface built on boostrap 
└── TA-LibriSpeechCorpus.db.sqlite3     //Sqlite database containing alignments and additional information

```


Database
========

Corpus is provided with diffrent tables containing useful information provided with the corpus. Database structure is organized as follows:

** Alignment Tables **
- Table ** Alignments **: Table containing transcriptions, textual alignments and name of the audio file associated with a given alignment. Each row corresponds to a sentence which is aligned
- Table audio: Table that contains duration of each speech segment(seconds)
- Table alignments_evaluations: Manually annotated 200 sentences from the corpus
- Table alignments_excluded: Table used to mark sentences to be excluded in the corpus.
- Table alignments_gTranslate: automatic translation output from Google translate for each segment (transcriptions)
- Table alignments_scores: different score calculations provided with the corpus which could be used to sort the corpus from highest scores to the lowest

** Metadata Tables **
- Table **librispeech**: This table contains all of the book from LibriSpeech project for which a downloadable link could be found (might be a dead/wrong link eventually)
- Table csv,clean100,other: Metadata completion for books provided with LibriSpeech project.
- Table nosLivres: some french ebook links gathered from nosLivres.net

Following SQL query could be used to gather most of the useful alignment information:
.. code:: sql
    SELECT * FROM alignments
    JOIN (alignments_excluded JOIN alignments_scores USING(audio_filename) )
    USING ( audio_filename ) WHERE excluded != "True"
    ORDER BY alignment_score DESC



