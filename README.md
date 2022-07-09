LIBRI-TRANS: Translation-Augmented-LibriSpeech-Corpus
=====================================================

Large scale (>200h) and publicly available read audio book corpus. This corpus is an augmentation of [(LibriSpeech ASR corpus](http://www.danielpovey.com/files/2015_icassp_librispeech.pdf)(1000h)[1] and contains English utterances (from audiobooks) automatically aligned with French text. Our dataset offers ~236h of speech aligned to translated text. 

### Dataset Link
https://persyval-platform.univ-grenoble-alpes.fr/DS91/detaildataset
https://zenodo.org/record/6482585#.YsmVBUhBxkg

### Overview of the corpus:

| Chapters | Books | Duration (h) | Total Segments |
|:--------:|:-----:|:------------:|:--------------:|
|   1408   |  247  |     ~236h    |     131395     |


Speech recordings and source texts are originally from [Gutenberg Project](https://www.http://www.gutenberg.org)[2], which is a digital library of public domain books read by volunteers. Our augmentation of LibriSpeech is straightforward: we automatically aligned e-books in a foreign language (French) with English utterances of LibriSpeech. 

We gathered open domain ebooks in french and extracted individual chapters available in LibriSpeech Corpus. Furthermore, we aligned chapters in French with English utterances in order to provide a corpus of speech recordings aligned with their translations. Our corpus is licensed under a [Creative Commons Attribution 4.0 License](https://creativecommons.org/licenses/by/4.0/legalcode).

Further information on how the corpus was obtained can be found in [3].


### Details on the 100h subset:

This 100h subset was specifically designed for direct speech translation training and evaluation.
It was used for the first time in [4] (end-to-end automatic speech recognition of audiobooks).
In this subset, we extracted the best 100h according to cross language alignment scores. Dev and Test sets are composed of clean speech segments only. 
Since English (source) transcriptions are initially available for LibriSpeech, we also translated them using Google Translate. To summarize, for each utterance of our corpus, the following quadruplet is available: English speech signal, English transcription (should not be used for direct speech translation experiments), French text translation 1 (from alignment of e-books) and translation 2 (from MT of English transcripts).

|      Corpus     |   Total  |        | Source(per seg) |       |            | Target(per seg) |
|:---------------:|:--------:|:------:|:---------------:|:-----:|:----------:|:---------------:|
|                 | segments |  hours |      frames     | chars | (sub)words |      chars      |
| train 1 train 2 |   47271  | 100:00 |       762       |  111  |    20.7    |     143 126     |
|       dev       |   1071   |  2:00  |       673       |   93  |    17.9    |       110       |
|       test      |   2048   |  3:44  |       657       |   95  |    18.3    |       112       |

The following archives correspond to the 100h subset used in [4]: 

For audio files:

- train_100h.zip (~8.7GB)
- dev.zip(~180MB)
- test.zip(~330MB)
- train_130h_additional.zip (~10.6GB)

For aligned text files:

- train_100h_txt.zip
- dev_txt.zip
- test_txt.zip
- train130h_additional_txt.zip

### Other archives provided:

Following archives are available to download for other potential use of the corpus: 

- database.zip(~50MB): Database describing the corpus (sqlite3)
- alignments.zip(~1.86GB): All of the intermediate processing files created in the cross-lingual alignment process along with English and French raw ebooks.
- audio_files.zip(~23GB): All of the speech segments organized as books and chapters
- interface.zip(~72MB): Contains static html files for alignment visualisation. With the interface, speech utterances can be listened while visualizing each sentence alignment.

Note: In order to listen to speech segments with the html interface, 'audio_files' folder should be placed inside the 'Interface' folder.
./Interface
 ./audio_files (audio_files.zip)
 ./css (interface.zip)
 ./js (interface.zip)
 (..)



Project Structure
=================

*Folders name convention corresponds to book id's from LibriSpeech and Gutenberg projects. For instance folder name **11** corresponds to the id number of "Alice's Adventures in Wonderland by Lewis Carroll" in both Gutenberg Project and LibriSpeech Project.*

This corpus is composed of **three sections**:
- Audio Files: resegmented audio files for each book id in the project
- HTML alignment visualisation interface : HTML visualisation for textual alignments with audio files avaliable to listen
- Alignments folder: all of the processing steps: pre-processing, alignment, forced transcriptions, forced alignments, etc.

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
├── index.html                              //Index page of html visualisation interface built on bootstrap 
└── TA-LibriSpeechCorpus.db.sqlite3     //Sqlite database containing alignments and additional information

```

Database
========

Corpus is provided with different tables containing useful information. The database structure is organized as follows:


### Database Structure


| Aligment Tables | Details |
| ------ | ------ |
| alignments | Table containing transcriptions, textual alignments and name of the audio file associated with a given alignment. Each row corresponds to an aligned sentence|
| alignments_audio | Table that contains duration of each speech segment (seconds) |
| alignments_evaluations | 200 sentences manually annotated (for alignement evaluation see [3]) |
| alignments_excluded |  Table used to mark sentences to be excluded from the corpus (bad alignments) |
| alignments_gTranslate |  Automatic translation output from Google translate for each segment (transcriptions) |
| alignments_scores |  different cross lingual alignment score calculations provided with the corpus which could be used to sort the corpus from highest scores to the lowest |



|Metadata Tables | Details |
| ------ | ------ |
| librispeech |  This table contains all the books from LibriSpeech project for which a downloadable link could be found (might be a dead/wrong link if it disappeared after our work) |
| csv,clean100,other |  Metadata completion for books provided with LibriSpeech project|
| alignments_excluded |  Some french ebook links gathered from http://www.noslivres.net |

![Database Structure][img]
  
[img]: https://github.com/alicank/Translation-Augmented-LibriSpeech-Corpus/raw/master/img/db_structure.png "Database Structure"



The following SQL query could be used to gather most of the useful alignment information:
```
    SELECT * FROM alignments
    JOIN (alignments_excluded JOIN alignments_scores USING(audio_filename) )
    USING ( audio_filename ) WHERE excluded != "True"
    ORDER BY alignment_score DESC

```

Script
======

We provide a script that could be used to interact with the database for extracting train, dev and test data to an output folder.


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

```
python3 TA-LibriSpeech.py train ./folder_output_train --size 1200 --verbose --sort CNG --maxSegDuration 35.0 --minSegDuration 3.0 --extract
```

### Arguments

- Positional Arguments
	- action: train/dev/test (For dev/test manually evaluated sentences are extracted to the output folder)
	- output_folder: Path to the output folder
	- **Output**: Writes paths of audio files to be extracted, their transcriptions and translations to the output folder

- Optional Arguments
	- **size**: (minutes) maximum limit to be extracted
	- sort {None,hunAlign,CNG,LM}: Sorts the corpus before extracting using the selected score. Default is CNG
	- v: Verbose mode
	- maxSegDuration : Maximum duration of a speech segment
	- minSegDuration: Minimum duration of a speech segment
	- extract: Copies speech segments along with transcription and translation files

	
References
==========
\[1\] [Librispeech: an ASR corpus based on public domain audio books.](http://www.danielpovey.com/files/2015_icassp_librispeech.pdf), Vassil Panayotov, Guoguo Chen, Daniel Povey and Sanjeev Khudanpur, ICASSP 2015.

\[2\] [Gutenberg Project](https://www.gutenberg.org/)

\[3\] Ali Can Kocabiyikoglu, Laurent Besacier and Olivier Kraif, ["Augmenting LibriSpeech with French Translations : A Multimodal Corpus for Direct Speech Translation Evaluation"](https://arxiv.org/abs/1802.03142), LREC 2018.

\[4\] Aléxandre Bérard, Laurent Besacier, Ali Can Kocabiyikoglu and Olivier Pietquin, ["End-to-End Automatic Speech Translation of Audiobooks"](https://arxiv.org/abs/1802.04200), ICASSP 2018.
