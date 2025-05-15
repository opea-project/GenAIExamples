# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import pandas as pd

symptoms = pd.read_csv(
    "https://raw.githubusercontent.com/611noorsaeed/Medicine-Recommendation-System-Personalized-Medical-Recommendation-System-with-Machine-Learning/main/Symptom-severity.csv"
)
description = pd.read_csv(
    "https://raw.githubusercontent.com/611noorsaeed/Medicine-Recommendation-System-Personalized-Medical-Recommendation-System-with-Machine-Learning/main/description.csv"
)
diet = pd.read_csv(
    "https://raw.githubusercontent.com/611noorsaeed/Medicine-Recommendation-System-Personalized-Medical-Recommendation-System-with-Machine-Learning/main/diets.csv"
)
medication = pd.read_csv(
    "https://raw.githubusercontent.com/611noorsaeed/Medicine-Recommendation-System-Personalized-Medical-Recommendation-System-with-Machine-Learning/main/medications.csv"
)
precautions = pd.read_csv(
    "https://raw.githubusercontent.com/611noorsaeed/Medicine-Recommendation-System-Personalized-Medical-Recommendation-System-with-Machine-Learning/main/precautions_df.csv"
)


import re

import wikipedia


def get_wiki_content(disease):
    article = wikipedia.page(disease)
    final1 = re.sub("[\n]", "", article.content)
    final2 = re.sub("[=]", " ", final1)
    final3 = re.sub("[\t]", "", final2)
    final = final3
    return final


list_of_disease = description["Disease"].unique()

for i in range(len(list_of_disease)):
    if list_of_disease[i] == "GERD":
        disease_name = "Gastroesophageal reflux disease"
    elif list_of_disease[i] == "Bronchial Asthma":
        disease_name = "Asthma"
    elif list_of_disease[i] == "Chicken pox":
        disease_name = "Chickenpox"
    elif list_of_disease[i] == "Common Cold":
        disease_name = "CommonCold"
    elif list_of_disease[i] == "Dimorphic hemmorhoids(piles)":
        disease_name = "Hemorrhoid"
    elif list_of_disease[i] == "(vertigo) Paroymsal Positional Vertigo":
        disease_name = "Benign paroxysmal positional vertigo"
    elif list_of_disease[i] == "Acne":
        disease_name = "Acne Vulgaris"
    else:
        disease_name = list_of_disease[i]

    print(f"looking for ({disease_name}")
    content = get_wiki_content(disease_name)
    disease_name = disease_name.replace(" ", "_")
    file1 = open(disease_name + ".txt", "w")
    file1.write(content)
    file1.close()
    print(f" created context for {i} :  {disease_name}")
