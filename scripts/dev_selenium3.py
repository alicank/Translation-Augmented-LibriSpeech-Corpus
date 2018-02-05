# -*- coding: utf-8 -*-
#####################################################################################################
# Groupe d'Étude pour la Traduction/le Traitement Automatique des Langues et de la Parole (GETALP)
# Homepage: http://getalp.imag.fr
# Author: Alican Kocabiyikoglu
#####################################################################################################

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
from selenium.common.exceptions import TimeoutException
import sys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium import webdriver
import dataset
import pickle
import json
import pprint
import re

#For full tutorial see: http://www.marinamele.com/selenium-tutorial-web-scraping-with-selenium-and-python

def init_driver(driver_adress):
	####### Marionette & Binary Files
	geckodriver = driver_adress
	driver = webdriver.Firefox(executable_path=geckodriver)
	return driver


def lookup(driver, query, key):

	# Ouverture du site nouslivres.net
	driver.get("http://www.noslivres.net/")
	try:
		time.sleep(1)
		# Une fois le site est chargé on essai de trouver avec Xpath la barre de recherche
		try:
			barre_recherche = driver.find_element(By.XPATH, '/html/body/div/div[1]/div[1]/label/input')
		except driver.common.exceptions.NoSuchElementException as err:
			print(err + "\n XPATH ne correspond pas!!!")
		# barre_recherche.clear()  # On supprime ce qui est déja écrit (s'il y en a)
		barre_recherche.send_keys(query)  # On lance la requete(le livre) qu'on veut chercher dans la BD

		# 1. On affiche tous les pages pour avoir plus de lien(s)
		try:
			time.sleep(1)
			select = Select(driver.find_element_by_name('catalogue_length'))
		except driver.common.exceptions.NoSuchElementException as err:
			print(err + "\n element recherche ne correspond pas!!!")

		select.select_by_value("100")

		# Finding the books
		try:
			time.sleep(1)
			catalogue = driver.find_element(By.XPATH, '/html/body/div/div[3]/table')
			try:
				books = catalogue.find_elements_by_class_name("sorting_1")
			except driver.NoSuchElementException as err:
				print(err + "Les éléments recherchés n'ont pas pu etre trouvés")

			names = []
			for item in books:
				if item != "":
					names.append(item.text)
				else:
					names.append("NA")
			titles_lenth = len(names)


			authors = []
			sources = []
			links = []

			i = 1
			while i < titles_lenth + 1:
				author = catalogue.find_element_by_xpath(
					"/html/body/div/div[3]/table/tbody/tr[" + str(i) + "]/td[2]")
				xpath_links = catalogue.find_element_by_xpath(
					"/html/body/div/div[3]/table/tbody/tr[" + str(i) + "]/td[5]/a")
				if author.text or xpath_links.text != "":
					authors.append(author.text)
					sources.append(xpath_links.text)
					links.append(xpath_links.get_attribute("href"))
				else:
					authors.append("NA")
					sources.append("NA")
					links.append("NA")
				i += 1



		except driver.common.exceptions.NoSuchElementException as err:
			print(err + "\n XPATH ne correspond pas!!!")

	except TimeoutException as err:
		print("Erreur Connexion/Timing " + err)

	db = dataset.connect('sqlite:///../DB/csv.db')
	#table = db['nosLivres']
	if len(names) == 0:
		data = dict(
			book_name=key,
			author="NA",
			source="NA",
			link="NA"
		)
		#table.insert(data) ########## For debug purposes (uncomment for updating DB)
	for i in range(len(names)):
		data = dict(
			book_name = key,
			author = authors[i],
			source = sources[i],
			link = links[i]
		)
		#table.insert(data)########## For debug purposes (uncomment for updating DB)



def basicDBquery(table, distinct):
	db = dataset.connect('sqlite:///../DB/csv.db')
	if distinct:
		table = db[table].distinct('translated_title')
	else:
		table = db[table]
	return table


def dictionnaire_assoc(liste, path):
	# Pour séparer le traitement des données -> un dictionnaire d'association
	print("Attention!\n\tLe fichier va etre écrasé\n\tVous confirmez?[Y/n]")
	choix = input(":::::")
	if choix == "Y":
		fh = open("./temp.txt", "w", encoding="utf8")
		for row in titres_DB:
			fh.write(row + "\t" + row + "\n")
		fh.close()


def pickleData(path, data):
	fh = open(path, "wb")
	pickle.dump(data, fh)
	return "La structure de donnée sauvegardé avec Pickle!"


def chercherLivres(dict_assoc, savePath):
	"""
	Prend en entrée une dictionnaire d'association pour les livres fait manuellement et recherche
	sur www.noslivres.net pour trouver tous les liens qui existent en source libre
	:param dict: clé: l'entrée dans la BD , valeurs = soit str(recherche simple) soit liste de noms de livres
	a rechercher
	:picklePath : le path pour stocker la structure de donnée avec Pickle + Json
	:return: void
	"""

	# Charger le dictionnaire d'association complété manuellement
	fh = open(dict_assoc, "r", encoding="utf8")
	livres_a_rechercher = {}
	for line in fh:
		data = line.split("\t")
		contextes = data[1].split("/")

		if len(contextes) > 1:
			livres_a_rechercher[data[0]] = contextes
		else:
			livres_a_rechercher[data[0]] = data[1].lower().strip()

	###! Element a chercher peut etre un string ou une liste d'elements
	# Chercher les éléments avec Selenium
	searchElements = {}
	driver = init_driver()



	for key, values in livres_a_rechercher.items():

		if type(values) == str:

			info = lookup(driver, values, key)

			searchElements[key] = info

			time.sleep(1)

		else:
			#Cherche differents titres pour le meme livre recursivement et ajouter
			# dans une liste les liens recuperes par ces differents tentatives afin
			# d'ajouter dans la BD
			def getBooksRecursive(vals,i, sortie):
				#Condition de sortie
				if i == len(vals):
					return sortie
				info = lookup(driver,vals[i].strip().lower(),key)
				sortie.append(info)
				return sortie + getBooksRecursive(vals, i+1, sortie)

			books_recursive = []
			getBooksRecursive(values, 0, books_recursive)


	driver.quit()

	pickleData(savePath + "searchElements.p", searchElements)

	with open(savePath + 'searchElements.json', 'w') as outfile:
		json.dump(searchElements, outfile)

	return "La structure de donnée est sauvegardé dans le dossier data"

def depickle(path):
	try:
		fh = open(path, "rb")
		return pickle.Unpickler(fh).load()
	except pickle.PickleError as err:
		return err

if __name__ == "__main__":

	# Recupération des données a partir de
	table = basicDBquery("csv", "translated_title")
	
	# Liste des titres traduits
	titres_DB = []
	for rows in table:
		titres_DB.append(rows['translated_title'])


	chercherLivres("./temp/livres_a_rechercher.txt", "../data/searchElements.p")











# driver = init_driver()
# lookup(driver, "Voyage au centre de la terre")
# time.sleep(5)
# driver.quit()
