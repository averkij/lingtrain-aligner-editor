import logging
import os
import pickle
import sys
from typing import List

import matplotlib
import numpy as np
import seaborn as sns
#https://stackoverflow.com/questions/49921721/runtimeerror-main-thread-is-not-in-main-loop-with-matplotlib-and-flask
matplotlib.use('Agg')
from matplotlib import pyplot as plt

import constants as con
import helper

import pdgraphs as pg
import pandas as pd
import re


def calculate_graphs(lines_from, processing_from_to, res_img, res_img_path, res_path, lang_name_from, lang_name_to):
    print("calculating...")
    # print(lines_from)
    pd.set_option('display.float_format', lambda x: '%.0f' % x)

    graph = txtfile2pgr(lines_from)

    #1
    df_edges = graph.edges()
    conn_html = df_edges[df_edges['from'] != df_edges['to']].sort_values(by = 'weight', ascending=False).iloc[:10].to_html(table_id="edges", index=False)

    #2
    df_deg = pd.DataFrame({'frame': graph.degrees})
    deg_html = df_deg.sort_values(by='frame', ascending=False).T.to_html(index=False)

    #3
    df_centr = pd.DataFrame({'frame': graph.cn})
    centr_html = df_centr.sort_values(by='frame', ascending=False).T.to_html(index=False)

    #4
    density = round(graph.density,5)
    sparsity = round(1/density,5)

    #5
    pd.set_option('display.float_format', lambda x: '%.2f' % x)
    spectr = graph.lapSpectr()
    spectr_html = spectr.dfSpectr().to_html(table_id="spectr")
    
    #6
    SaveLayers2plot(spectr, res_img_path)

    #7
    letter_clusters = quadro_clusters(spectr)

    res = {
        "items": 
            {
                "conn_html": conn_html,
                "deg_html": deg_html,
                "centr_html": centr_html,
                "density": density,
                "sparsity": sparsity,
                "spectr_html": spectr_html,
                "spectr_img": res_img,
                "clusters": letter_clusters
            }
    }

    print("saving result to", res_path)
    pickle.dump(res, open(res_path, "wb"))

pd.set_option('display.float_format', lambda x: '%.3f' % x)

def d_clusters(spectr, ind1, ind2):
    d_clusters = []
    dfClusters = pd.DataFrame({'1': spectr.vectors.iloc[ind1], '2': spectr.vectors.iloc[ind2]})
    d_clusters.append(list((dfClusters[(dfClusters['1'] > 0) & (dfClusters['2'] > 0)]).index))
    d_clusters.append(list((dfClusters[(dfClusters['1'] > 0) & (dfClusters['2'] <= 0)]).index))
    d_clusters.append(list((dfClusters[(dfClusters['1'] <= 0) & (dfClusters['2'] <= 0)]).index))
    d_clusters.append(list((dfClusters[(dfClusters['1'] <= 0) & (dfClusters['2'] > 0)]).index))
    return d_clusters

def quadro_clusters(spectr):
    ind1, ind2 = maxPolarizationIndex(spectr)
    return d_clusters(spectr, ind1, ind2)

def dClusters(spectr, ind1, ind2):
    dclusters = {}
    dfClusters = pd.DataFrame({'1': spectr.vectors.iloc[ind1], '2': spectr.vectors.iloc[ind2]})
    dclusters['++'] = list((dfClusters[(dfClusters['1'] > 0) & (dfClusters['2'] > 0)]).index)
    dclusters['+-'] = list((dfClusters[(dfClusters['1'] > 0) & (dfClusters['2'] <= 0)]).index)
    dclusters['-+'] = list((dfClusters[(dfClusters['1'] <= 0) & (dfClusters['2'] > 0)]).index)
    dclusters['--'] = list((dfClusters[(dfClusters['1'] <= 0) & (dfClusters['2'] <= 0)]).index)
    return dclusters

def quadroClusters(spectr):
    ind1, ind2 = maxPolarizationIndex(spectr)
    return dClusters(spectr, ind1, ind2)

def maxPolarizationIndex(spectr):
    ind = spectr.vectors.apply(abs).apply(sum, axis=1).sort_values(ascending=False)[:2] # two rows with max polarization
    return (ind.index[0], ind.index[1])

def SaveLayers2plot(spectr, res_img):
    customPalette = ['#630C3A', '#39C8C6', '#D3500C', '#FFB139']
    sns.set_style('whitegrid')
    sns.set_palette(customPalette)

    sym_clusters = quadroClusters(spectr)

    ind1, ind2 = maxPolarizationIndex(spectr)
    fig, ax = plt.subplots(figsize=(10,10))
    crd1 = 1000*spectr.vectors.iloc[ind1]/spectr.values[ind1]
    crd2 = 1000*spectr.vectors.iloc[ind2]/spectr.values[ind2]
    ax.scatter(crd1, crd2, alpha=0.0)
    ax.grid(True)

    crd1 = spectr.vectors.iloc[ind1]/spectr.values[ind1]
    crd2 = spectr.vectors.iloc[ind2]/spectr.values[ind2]
    max_val = max(abs(min(crd1)), abs(max(crd1)), abs(min(crd2)), abs(max(crd2)))
    crd1 /= max_val
    crd2 /= max_val

    ax.set_xlim(-1, 1)
    ax.set_ylim(-1, 1)

    for i, key in enumerate(sym_clusters):
      for sym in sym_clusters[key]:
        ax.text(crd1[sym], crd2[sym], sym, fontsize=20, color=customPalette[i])

    fig.tight_layout()
    plt.savefig(res_img, bbox_inches="tight")

def txtfile2pgr(text):
    lWords = text2words(text)
    dfAdj = lol2adj(lWords)
    return pg.pdGraph(dfAdj)

def lol2adj(lol): # list of lists (tuples, sets, words) of elements to adj matrix
    # slow
    dfEls, dfElsNorm = pd.DataFrame(), pd.DataFrame()
    for i, els in enumerate(lol):
        for el in els: # prepare for sum
            dfEls.at[i, el] = 0
            dfElsNorm.at[i, el] = 0
    for i, els in enumerate(lol):
        weight = 1/len(els)
        for el in els:
            dfEls.at[i, el] += 1
            dfElsNorm.at[i, el] += weight
    return (dfElsNorm.fillna(0).T @ dfEls.fillna(0)).sort_index(axis=0).sort_index(axis=1)

def text2words(txt):
    lWords = re.split('[^а-яё]+', txt.lower(), flags=re.IGNORECASE) #'[^a-zа-яё]+'
    return [word for word in lWords if len(word) > 1]
