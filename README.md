
========================================
Translation-Augmented-LibriSpeech-Corpus
========================================

This project is an extension of LibriSpeech ASR Corpus which is a corpus of approximatively 1000 hours of speech aligned with their transcriptions (`LibriSpeech: an ASR corpus based on public domain audio books", Vassil Panayotov, Guoguo Chen, Daniel Povey and Sanjeev Khudanpur, ICASSP 2015`_) for speech translation systems. 

Speech recordings and source texts are originally from `Gutenberg Project`_ which is a digital library of public domain books read by volunteers. We gathered open domain ebooks in French and aligned chapters from LibriSpeech project with the chapters of translated e-books. Furthermore, we aligned the transcriptions with their respective translations in order to provide a corpus of speech recordings aligned with their translations. Our corpus is licenced under a `Creative Commons Attribution 4.0 License`_ 

.. _2015: http://www.danielpovey.com/files/2015_icassp_librispeech.pdf
.. _Project: http://www.gutenberg.org
.. _License: https://creativecommons.org/licenses/by/4.0/legalcode

Project Structure
=================
*Folder name convention corresponds to book id's from LibriSpeech Project and Gutenberg Project. For example: folder 11 would correspond
to "Alice's Adventures in Wonderland by Lewis Carroll" at both Gutenberg and LibriSpeech Projects. *

This corpus is composed of three sections:
- Audio Files: Resegmented audio files for each book id in the project
- HTML alignment visualisation interface : HTML visualisation for textual alignments with audio files avaliable to listen
- Alignments folder: All of the processing steps: pre-processing, alignment, forced transcriptions, forced alignments, etc.








