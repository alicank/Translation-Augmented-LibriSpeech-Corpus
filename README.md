

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


- CORPUS-MSCOCO (~75GB)

    - **train2014/** : folder contains 413,915 captions
       - json/
       - wav/
       - translations/
              - train_en_ja.txt
              - train_translate.sqlite3       
       - train_2014.sqlite3
       
    - **val2014/** : folder contains 202,520 captions
       - json/
       - wav/
       - translations/
              - train_en_ja.txt
              - train_translate.sqlite3 
       - val_2014.sqlite3

    - **speechcoco_API/**
           - speechcoco/
                  - __init__.py
                  - speechcoco.py
           - setup.py







