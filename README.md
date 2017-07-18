Translation-Augmented-LibriSpeech-Corpus
========================================

This project is an extension of LibriSpeech ASR Corpus which is a corpus of approximatively 1000 hours of speech alignment with their transcriptions [LibriSpeech: an ASR corpus based on public domain audio books, Vassil Panayotov, Guoguo Chen, Daniel Povey and Sanjeev Khudanpur, ICASSP 2015](http://www.danielpovey.com/files/2015_icassp_librispeech.pdf) for speech translation systems.


Speech recordings and source texts are originally from [Gutenberg Project](https://www.http://www.gutenberg.org) which is a digital library of public domain books read by volunteers.  In this project we gathered open domain e-books in French and extracted chapters that are avaliable in LibriSpeech Project. Furthermore, we aligned english transcriptions with their respective french translations in order to provide a corpus of speech recordings aligned with their respective translations. Our corpus is licenced under a [Creative Commons Attribution 4.0 License](https://creativecommons.org/licenses/by/4.0/legalcode)

Project Structure
=================

*Folder name conventions corresponds to book id's from LibriSpeech and Gutenberg projects. For example id **11** corresponds to "Alice's Adventures in Wonderland by Lewis Carroll" at both Gutenberg and LibriSpeech Projects*

This corpus is composed of **three sections**:
- Audio Files: Resegmented audio files for each book id in the project. There are in total 247 e-books (1408 chapters) and 131.395 speech segments.
- HTML visualisation interface : We provide an html interface to visualize alignments and to listen to speech segments
- Alignments folder: Additional files created in the alignment and processing steps for each book

**The repository is organized as follows**:

```
.
├── Alignments           //Folder contains additional files and metadata of alignment and processing steps
│   ├── chapter_id
│   │   ├── alignments
│   │   ├── en
│   │   └── fr
│   ├── lc_book_id.txt|pdf|epub                                                        //Raw french e-book 
│   └── ls_book_id.txt                                            //Raw english e-book (Gutenberg Project)
├── audio_files                                  //Folder contains audio segments for each book in project
│   ├── 11                                                                    //For example for book id 11
│   │   ├── 123440                                             //Chapter from dev/test pool of LibriSpeech
│   │   │   ├── 260-123440-0000.wav                                 //reader_id-chapter_id-sentence_id.wav
│   │   │   ├── 260-123440-0001.wav
│   │   │   └── 260-123440-0002.wav
│   │   └── 123441                                          //Chapter from clean/other pool of LibriSpeech
│   │       ├── 11-123441-0000.wav                                    //book_id-chapter_id-sentence_id.wav
│   │       └── 11-123441-0001.wav
│   └── book_id
│       └── chapter_id
│           ├── book_id-chapter_id-sentence_id.txt
│           └── **reader_id-chapter_id-sentence_id**.txt                    **dev/test pool of LibriSpeech
├── index.html                              //Index page of html visualisation interface built on bootsrap 
└── TA-LibriSpeechCorpus.db.sqlite3     //Sqlite database containing alignments and additional information

```

Database
========

Corpus is provided with diffrent tables containing useful information provided with the corpus. Database structure is organized as follows:


![Database Structure][img]
  
[img]: https://github.com/alicank/Translation-Augmented-LibriSpeech-Corpus/raw/master/img/db_structure.png "Database Structure"


### Database Structure


| Aligment Tables | Explication |
| ------ | ------ |
| Alignments | Table containing transcriptions, textual alignments and name of the audio file associated with a given alignment. Each row corresponds to an aligned sentence|
| alignments_audio | Table that contains duration of each speech segment (seconds) |
|  alignments_evaluations | Manually evaluated 200 sentences from the corpus|
| alignments_excluded |  automatic translation output from Google translate for each segment |
| alignments_scores |  different score calculations provided with the corpus which could be used to sort the corpus |



|Metadata Tables | Explication |
| ------ | ------ |
| librispeech |  This table contains all of the book from LibriSpeech project for which a downloadable link could be found (might be  dead/wrong links eventually) |
| csv,clean100,other |  Metadata completion for books provided with LibriSpeech project |
| alignments_excluded |  Some french ebook links gathered from http://www.noslivres.net |


Following SQL query could be used to gather most of the useful alignment information:
```
	SELECT * FROM alignments
    JOIN (alignments_excluded JOIN alignments_scores USING(audio_filename) )
    USING ( audio_filename ) WHERE excluded != "True"
    ORDER BY alignment_score DESC

```

Script
======

We developed a script that could be used to interact with the database for extracting train,dev and test data to an output folder.


**TA-LibriSpeech.py** Module Description:
```

	usage: TA-LibriSpeech.py [-h] [--size SIZE] [--listTrain LISTTRAIN]
                         [--useEvaluated USEEVALUATED]
                         [--sort {None,hunAlign,CNG}] [-v]
                         [--maxSegDuration MAXSEGDURATION]
                         [--minSegDuration MINSEGDURATION] [--extract]
                         action output

```

### Example use:

```python
python3 TA-LibriSpeech.py train ./folder_output_train --size 1200 --verbose sort CNG --maxSegDuration 35.0 --minSegDuration 3.0 --extract
```

### Arguments

- Positional Arguments
	- action: train/dev/test (For dev/test manually evaluated sentences are extracted to the output folder)
	- output_folder: Path to the output folder
	**Output**: Writes to output folder paths of audio files to be extracted, their transcriptions and translations

- Optional Arguments
	- **size**: (minutes) maximum limit to be extracted
	- sort {None,hunAlign,CNG,LM,CNGLM}: Sorts the corpus before extracting using the selected score. Default is CNG
	- v: Verbose mode
	- maxSegDuration : Maximum duration of a speech segments
	- minSegDuration: Minimum duration of a speech segments
	- extract: Copies speech segments along with

	


