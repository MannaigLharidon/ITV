# -*- coding: utf-8 -*-
# auteur : Mannaïg L'Haridon
# date : 28/10/2021
"""
Contrôle des ITV rendus

Vérification du contenu des fichiers XML des ITV
Objectif du script : vérifier l'existance et la cohérence des regards et 
            tronçons de collecteurs contenus dans les fichiers XML des ITV, 
            avec ceux de la base patrimoine.
"""

import os
import xml.etree.ElementTree as ET 
import numpy as np
import pandas as pd


def getInfos(path):
    """
    Récupération des informations principales de l'ITV'
    """
    # Trouve le fichier XML de l'ITV à analyser, dans le dossier fourni
    for filename in os.listdir(path):
        if not filename.endswith('.xml'):
            continue
        xmlfile = os.path.join(path,filename)
        tree = ET.parse(xmlfile)
        root = tree.getroot()   ## niveau 1 de l'arbre XML
               
        # Rues inspectées <AAJ>
        liste_rues = []
        for rue in root.iter('AAJ'):
            liste_rues.append(rue.text)
        liste_rues = np.unique(np.array(liste_rues))

        # Maitre d'oeuvre <AAM>
        liste_moe = []
        for moe in root.iter('AAM'):
            liste_moe.append(moe.text)
        liste_moe = np.unique(np.array(liste_moe))
            
        # Commune <AAN>
        liste_communes = []
        for commune in root.iter('AAN'):
            liste_communes.append(commune.text)
        liste_communes = np.unique(np.array(liste_communes))

        # Quartier <AAO>
        liste_quartier = []
        for quartier in root.iter('AAO'):
            liste_quartier.append(quartier.text)
        liste_quartier = pd.unique(liste_quartier)
        
        # Date de l'inspection <ABF>
        liste_date = []
        for date_itv in root.iter('ABF'):
            liste_date.append(date_itv.text)
        liste_date = np.unique(np.array(liste_date))
        
    return liste_rues, liste_moe, liste_communes, liste_quartier, liste_date

    
def getRegards(path) :
    """
    Fonction qui récupère les noms des regards amont / aval de chaque tronçon inspecté dans une ITV,
    à partir d'un dossier d'une ITV fourni
    """
    # Trouve le fichier XML de l'ITV à analyser, dans le dossier fourni
    for filename in os.listdir(path):
        if not filename.endswith('.xml'):
            continue
        xmlfile = os.path.join(path,filename)
        tree = ET.parse(xmlfile)
        root = tree.getroot()   ## niveau 1 de l'arbre XML
        
        # Récupère le nombre de tronçons inspectés dans l'ITV
        nb_troncons = 0
        for child in root :     ## niveau 2 de l'arbre XML
            if child.tag == 'ZB': # trouve tous les tronçons <ZB> inspectés
                nb_troncons += 1

        # Liste de récupération des noms des regards amont, regards aval, et des collecteurs
            # Note : convertir en dictionnaire, au lieu de faire une matrice numpy ? Faire une map avec le nopm de l'ITV ?
        synthese = np.zeros((nb_troncons,5)).astype(str)
        
        # Récupération du premier regard du tronçon inspecté
        temp_nb = 0
        for regard_1 in root.iter('AAD'):
            if temp_nb < nb_troncons :
                synthese[temp_nb][0] = regard_1.text
                temp_nb += 1
            
        # Récupération du deuxième regard du tronçon inspecté
        temp_nb = 0
        for regard_2 in root.iter('AAF'):
            if temp_nb < nb_troncons :
                synthese[temp_nb][1] = regard_2.text
                temp_nb += 1
                
    return synthese
    
def checkRegards(base_regard, synthese, colonne):
    """
    Vérification de l'existence du regard dans la base patrimoniale
    """
    for i in range(synthese.shape[0]):
        try :
            base_regard[base_regard['identifiant'] == synthese[i,colonne]].index[0]
            synthese[i,colonne+2] = True
        except IndexError:
            synthese[i,colonne+2] = False
            
    return synthese


def checkTroncons(base_collecteur, synthese):
    """
    Vérification de l'existence du tronçon inspecté dans la base patrimoniale
    """
    for i in range(synthese.shape[0]) :
        try :
            # recherche de tous les collecteurs définis par le regard d'entrée de l'inspection
            entree_amont = base_collecteur[base_collecteur['id_noeud_amont'] == synthese[i,0]]
            entree_aval = base_collecteur[base_collecteur['id_noeud_aval'] == synthese[i,0]]
            entree = pd.concat([entree_amont, entree_aval])
            
            # Vérification de la présence du regard de sortie dans les combinaisons de collecteurs possibles
            entree[(entree == synthese[i,1]).any(1)].index[0]
            
            # le collecteur a été trouvé
            synthese[i,4] = True
            
        except IndexError :
            # le collecteur n'a pas été trouvé
            synthese[i,4] = False
    return synthese


def analyseITV(synthese,path,sauvegarde):
    """
    Analyse de la cohérence de l'ITV par rapport aux bases patrimoniales
    """
    # Création du fichier d'analyse
    nom_itv = path[len(path)-path[::-1].find('/')::]
    analyse = open(sauvegarde + nom_itv + "_analyse.txt","w+")
    analyse.write("Nom de l'ITV : " + nom_itv + "\n")
    
    # Récupération des informations générales de l'ITV
    rues, moe, commune, quartier, date_itv = getInfos(path)
    analyse.write("\n>>> INFORMATIONS GENERALES DE L'ITV <<<\n")
    analyse.write("Communes : ")
    for c in commune :
        analyse.write(c)
    analyse.write("\nQuartiers : ")
    for q in quartier :
        if q != None :
            analyse.write(q)
    analyse.write("\nRues :")
    for r in rues :
        analyse.write("\n     - " + r)
    analyse.write("\nEntreprise ayant commande l'ITV : ")
    for m in moe : 
        analyse.write(m)
    analyse.write("\nDate d'inspection : ")
    for d in date_itv:
        analyse.write("\n     - " + d)
        
    # Analyse des regards et collecteurs
    analyse.write("\n\n\n >>> ANALYSE PATRIMONIALE DE L'ITV <<<\n\n")
    # Nombre de regards visités
    regard_visite = np.unique(synthese[:,0:2])
    nb_regard = len(regard_visite)
    analyse.write("Nombre regards visites : " + str(nb_regard))
    
    # Nombre de regards non présents dans la base
    reg_entree = [synthese[i,0] for i in range(synthese.shape[0]) if synthese[i,2]=='False']
    reg_sortie = [synthese[i,1] for i in range(synthese.shape[0]) if synthese[i,3]=='False']
    regard_inconnu = np.unique(reg_entree + reg_sortie)
    nb_regard_inconnu = len(regard_inconnu)
    analyse.write("\nNombre regards inconnus dans la base patrimoniale : " + str(nb_regard_inconnu))
    if nb_regard_inconnu > 0 :
        analyse.write("\nListe des regards inconnus : ")
    for r in regard_inconnu:
        analyse.write("\n    - " + r)
    
    # Nombre de collecteurs non trouvés au total
    collecteur_inconnu = [(synthese[i,0],synthese[i,1]) for i in range(synthese.shape[0]) if synthese[i,4]=='False']
    nb_collecteur_inconnu = len(collecteur_inconnu)
    # analyse.write("\n\nNombre de collecteurs non trouve dans la base : " + str(nb_collecteur_inconnu))
    if nb_collecteur_inconnu > 0:
        analyse.write("\n\nNombre de collecteurs non trouve dans la base : " + str(nb_collecteur_inconnu))
        analyse.write("\nListe des collecteurs non trouve : ")
        for c in collecteur_inconnu :
            analyse.write("\n    - " + str(c))
    else:
        analyse.write("\n\nTous les collecteurs ont été trouvés dans la base")
    
    # Nombre de collecteurs non trouvés dans la base, alors que les 2 regards existent
    collecteur_incoherent = [(synthese[i,0],synthese[i,1]) for i in 
                             range(synthese.shape[0]) if synthese[i,4]=='False' 
                             and synthese[i,2] == 'True' and synthese[i,3] == 'True']
    nb_collecteur_incoherent = len(collecteur_incoherent)
    if nb_collecteur_incoherent > 0:
        analyse.write("\n\nNombre de collecteurs 'incohérents' : " + str(nb_collecteur_incoherent))
        analyse.write("\nListe des collecteurs 'incohérents' : ")
        for c in collecteur_incoherent :
            analyse.write("\n    - " + str(c))
        analyse.write("\n\n\n* colecteur 'incohérent' : tronçon de collecteur non trouve dans la base, alors que les 2 regards existent")
    
    if nb_collecteur_inconnu > 0 and nb_collecteur_incoherent == 0 :
        analyse.write("\n\nNombre de collecteurs 'incoherents' : " + str(nb_collecteur_incoherent))
        analyse.write("\n\n* colecteur 'incoherent' : troncon de collecteur non trouve dans la base, alors que les 2 regards existent")
        analyse.write("\n\n=> COLLECTEURS NON TROUVES MAIS COHERENTS : au moins un des regards n'est pas renseigne dans la base patrimoniale Regard")
    
    if nb_collecteur_inconnu > nb_collecteur_incoherent and nb_collecteur_incoherent > 0 :
        analyse.write("\n\n=> COLLECTEURS NON TROUVES ET INCOHERENTS")
        
    if nb_collecteur_inconnu == nb_collecteur_incoherent and nb_collecteur_incoherent > 0 :
        analyse.write("\n\n=> LES COLLECTEURS NON TROUVES SONT UNIQUEMENT INCOHERENTS")
    
    if nb_regard_inconnu == 0 and nb_collecteur_inconnu == 0 :
        analyse.write("\n\n=> ITV VALIDEE (cohérence des regards et des collecteurs)")
        
    if nb_regard_inconnu > 0 and nb_collecteur_inconnu == 0 :
        analyse.write("\n\n=> La base REGARD n'est pas complète et doit être mise à jour par le SICTEUB")
        
    
    analyse.close()
    print("fin sauvegarde")
    

if __name__ == '__main__':
    
    # Table de référence des collecteurs
    collecteur_file = '//10.9.7.150/data/Partage/SICTEUB/SIG/Script/Analyse ITV/Base_Patrimoine_ref/Collecteur_28102021.csv'
    base_collecteur = pd.read_csv(collecteur_file,sep=';',encoding='latin_1',low_memory=False).loc[:,lambda df : ['id_noeud_amont', 'id_noeud_aval']]
    
    # Table de référence des regards
    regard_file = '//10.9.7.150/data/Partage/SICTEUB/SIG/Script/Analyse ITV/Base_Patrimoine_ref/Regard_28102021.csv'
    base_regard = pd.read_csv(regard_file,sep=';',encoding='latin_1').loc[:, lambda df : ['identifiant']]
    
    # ITV à analyser
    # path = '//10.9.7.150/data/Partage/SICTEUB/SIG/Script/Analyse ITV/Jeu_test/VOL - ASN1.2021.303 test valid'
    directory = ['VOL - ASN0.2021.303','VOL - ASN1.2021.303','VOL - ASN3.2021.303','VOL - BEL1.2021.303',
                 'VOL - CHA2.2021.303','VOL - CHA3.2021.303','VOL - CHS1.2021.303','VOL - FOS1 et 2.2021.303',
                 'VOL - LUZ1.2021.303','VOL - LUZ2.2021.303','VOL - LUZ3.2021.303','VOL - LUZ4.2021.303',
                 'VOL - MAV1.2021.303','VOL - MAV2.2021.303','VOL - PLA1 et 2.2021-303','VOL - PLL1.2021.303',
                 'VOL - PONT1.2021.303','VOL - SEU1.2021.303','VOL - SUR1.2021.303','VOL - SUR2.2021.303',
                 'VOL - VIA1.2021.303','VOL - VIA2.2021.303','VOL - VIA3.2021.303']

    # Dossier de sauvegarde des analyses
    sauvegarde = "//10.9.7.150/data/partage/SICTEUB/Assainissement EU/AC/Transport/Canalisation-Collecteur/Curage - ITV/Inspection televisees/Analyse_SDA/"
    # sauvegarde = "//10.9.7.150/data/partage/SICTEUB/SIG/ANALYSE_ITV/"
    
    for p in directory :
        path = '//10.9.7.150/itv/' + p
        # Récupération des regards, des tronçons inspectés
        regard_itv = getRegards(path)
        
        # Vérification de l'existance de tous les regards amont et aval, dans la base SICTEUB
        # Pour les regards amont
        regard_itv = checkRegards(base_regard, regard_itv, 0)
        
        # Pour les regards aval
        regard_itv = checkRegards(base_regard, regard_itv, 1)
        
        # Vérification de l'existance du tronçon inspecté, dans la base SICTEUB
        regard_itv = checkTroncons(base_collecteur, regard_itv)
        
        # RESULTATS DE L'ANALYSE
        print("Sauvegarde de l'analyse de l'ITV : ",p)
        analyseITV(regard_itv,path,sauvegarde)

      
        
            
