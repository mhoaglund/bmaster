import os
import csv
import json
import collections, operator

confidence = 1
threshold = 0.08

def intTryParse(value):
    try:
        return int(value), True
    except ValueError:
        return value, False

#Smooth and normalize, averaging out missing data and normalizing to sum of 1.
def normalize(arr, exc):
    base = [x for x in arr if x != exc]
    #TODO: replace with hereditary average of player instead of local avg
    if len(base) == 0:
        return False, None
    for x in range(0, len(arr)):
        if arr[x] == exc:
            arr[x] = sum(base)/len(base)
    norm = [float(y)/sum(arr) for y in arr]
    return True, norm

def addUpByName(cols):
    #Input is normalized columns of gap-corrected score data, by name.
    local_avg = []
    for x in range(0, len(cols[0])):
        normalized_ind_scores = [n[x] for n in cols] #name and scores
        just_scores = normalized_ind_scores[1:]
        #For now, a handicap is basically a %. A player who has never scored any points but has played every game has a 100% handicap.
        avg_points_portion = (sum(just_scores)/len(just_scores))
        percent_mod = 0
        if avg_points_portion < threshold:
            percent_mod = 1 + avg_points_portion
        else:
            percent_mod = 1 - avg_points_portion
        hydrated_scores.update({
            normalized_ind_scores[0]:percent_mod ** confidence
        })
        local_avg.append(percent_mod)
    hydrated_scores.update({'default':sum(local_avg)/len(local_avg)})


rows = []
normcolumns = []
columns = []
people = []
hydrated_scores = {}

with open('bmasterscorehistory.csv', 'rb') as csvfile:
    piecereader = csv.reader(csvfile, delimiter=',', quotechar='|')
    for row in piecereader:
        if len(columns) < 1:
            for x in range(1, len(row)):
                columns.append([])
        if row[0] != 'Name':
            if row[0] not in people:
                people.append(row[0])
            for x in range(1, len(row)):
                val, isint = intTryParse(row[x])
                if isint:
                    row[x] = val
                    columns[x-1].append(val)
                else:
                    row[x] = -1
                    columns[x-1].append(-1)
            rows.append(row)
    normcolumns.append(people)
    if len(columns) > 0:
        for c in range(1, len(columns)):
            thiscol = [x[c] for x in rows]
            flag, data = normalize(thiscol, -1)
            if flag:
                normcolumns.append(data)

    addUpByName(normcolumns)

with open('jsonhandicaps.txt', 'w') as outfile:  
    json.dump(hydrated_scores, outfile)


with open('bmastercurrent.csv', 'rb') as csvfile:
    adjusted_all = {}
    piecereader = csv.reader(csvfile, delimiter=',', quotechar='|')
    for row in piecereader:
        handicap = 0
        if row[0] != 'Name':
            if row[0] in hydrated_scores: #if we have a handicap, apply it.
                handicap = hydrated_scores[row[0]]
                # if handicap > threshold:
                #     handicap = 1
            else:
                handicap = hydrated_scores["default"]
            if len(row) > 1:
                this_sum = sum([intTryParse(c)[0] for c in row[1:]])
                adjusted_sum = this_sum * handicap
                adjusted_all.update({
                    row[0]:{
                        'Total Points': this_sum,
                        'Adjusted Score': int(round(adjusted_sum)),
                        'Handicap': "{0:.0f}%".format(handicap * 100)
                    }
                })

    def returnAdjusted(obj):
        return obj['Adjusted Score']

    with open('all_current.txt', 'w') as outfile: 
        temp = []
        my_list = list(adjusted_all)
        all_sorted = sorted(my_list, key=lambda x: (adjusted_all[x]['Adjusted Score']), reverse=True)
        for x in range(0, len(all_sorted)):
            temp.append({all_sorted[x] : adjusted_all[all_sorted[x]]}) #jesus, really?
        json.dump(temp, outfile)
