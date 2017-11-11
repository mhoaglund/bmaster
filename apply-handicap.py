import os
import csv
import json

with open('bmastercurrent.csv', 'rb') as csvfile:
    piecereader = csv.reader(csvfile, delimiter=',', quotechar='|')
    for row in piecereader: