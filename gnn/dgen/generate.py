from array import array
from curses import has_key
from operator import length_hint

import random as rd

from random import sample, seed
from random import random
from random import choice

from math import log10


import uuid
import pandas as pd
import csv
class DGenerator(object):
    # Constructor
    def __init__(self, config):
        self.config = config
        self.genmodel= dict()

    def generate(self): 
        self.genmodel = dict()

        nodes = self.config['supervisor']['gennodes'].split(",")
        edges = self.config['supervisor']['genedges'].split(",")

        # 1 - Generate Nodes in Order
        self.genmodel['nodes'] = dict()
        print(self.config)
        print("Nodes: ", nodes)
        for node in nodes: 
            self.genmodel['nodes'][node] = self.generateNode(node)

        # 2 Generate Edges in Order
        print("Edges: ", edges)
        self.genmodel['edges'] = dict()
        for edge in edges: 
            directassoc=int(self.config[edge]['directassoc'])
            if (directassoc == 0):
                self.genmodel['edges'][edge] = self.generateEdge(edge)
            else:
                self.genmodel['edges'][edge] = self.connectEdge(edge)
            #print(edge, " count: ", len(self.genmodel['edges'][edge]['base']))

        # 5 Cleanup scattered nodes(un-featured k-measures)
        if len(self.config['supervisor']['compact'].split(',')) > 0:
            self.compactModel(self.config['supervisor']['compact'].split(','))
        
    def compactModel(self, edgelist):
        for el in edgelist:
            edges=self.genmodel['edges'][el]
            useddict = edges['used']
            basearr=self.genmodel['nodes'][self.config[el]['to_node']]['base']
            cleanarr=[]

            print("Edge used: ", el, len(useddict.keys()))
            print("Node base: ", el, len(basearr))
            for item in basearr:
                #print("id: ", item['id'])
                if(item[0] in useddict):
                    cleanarr.append(item)
            print("Node clean: ", el, len(cleanarr))
            self.genmodel['nodes'][self.config[el]['to_node']]['base']=cleanarr
        

    def dumpGenModel(self): 

        # Dump Nodes
        nodes=self.genmodel['nodes']
        print( nodes.keys())
        for node in nodes.keys():
            dataarr = nodes[node]['base']
            print(node, " - Count: ", len(dataarr))

            path = self.config['outspec']['path'] + '/node_' + node + ".csv"
            with open(path, 'w', encoding='UTF8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(self.config[node]['header'].split(","))
                writer.writerows(dataarr)

        edges=self.genmodel['edges']
        for edge in edges.keys():
            dataarr = edges[edge]['base']
            print(edge, " - Count: ", len(dataarr))

            path = self.config['outspec']['path'] + '/edge_' + edge + ".csv"
            with open(path, 'w', encoding='UTF8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(self.config[edge]['header'].split(","))
                writer.writerows(dataarr)

    def pickIDFromNodeCategory(self,node,cat,crit):
        pick=rd.choice(list(self.genmodel['nodes'][node][crit][cat]))
        return pick

    def pickNonCritSamples(self,node,samplesize, exclude):
        #print("exclude: ", exclude)
        sample_cat=rd.sample(list(self.genmodel['nodes'][node]['non-crit']), int(samplesize))
        for exc in exclude:
            try:
                sample_cat.remove(exc)
            except ValueError:
                pass
        picks=dict()

        for cat in sample_cat:
            pick=self.pickIDFromNodeCategory(node,cat,'non-crit')
            picks[cat]=pick
        return picks


    def connectEdge(self, gtype):
        gendata = dict()
        gendata['base']=[]
        gendata['used']=dict()

        df = pd.read_csv(self.config['supervisor']['path'] + '/edge_' + gtype + ".csv", usecols=self.config[gtype]['header'].split(","))        
        print(len(df.index))
        print(df.columns)

        # for all critical from_node
        #   find collection of supervised 'labeled' mappings for detected attack patterns 
        # from_id,from_cat,to_id,to_cat
        from_obj=self.genmodel['nodes'][self.config[gtype]['from_node']]

        for from_cat in from_obj['crit'].keys():
            for from_id in from_obj['crit'][from_cat].keys():
                # add detected technologies 
                crit_to = df.loc[df['from_cat'] == from_cat]
                crit_to = crit_to.reset_index()  
                for index, row in crit_to.iterrows():
                    print(row['to_cat'], row['to_id'])
                    rec=[from_id,from_cat,row['to_id'], row['to_cat']]
                    gendata['base'].append(rec)
                    index=len(gendata['base'])-1
                    gendata['used'][from_id]=1
        return gendata

    def generateEdge(self, gtype):
        gendata = dict()
        gendata['crit']= dict()
        gendata['non-crit']= dict()
        gendata['base']=[]
        gendata['used']=dict()

        df = pd.read_csv(self.config['supervisor']['path'] + '/edge_' + gtype + ".csv", usecols=self.config[gtype]['header'].split(","))        
        print(len(df.index))
        print(df.columns)

        # for all critical from_node
        #   find collection of supervised 'labeled' mappings for available critical to_categories 
        #       pick with no repeats available to category instances
        # from_id,from_cat,to_id,to_cat
        from_obj=self.genmodel['nodes'][self.config[gtype]['from_node']]
        #print(self.genmodel.keys())
        for from_cat in from_obj['crit'].keys():
            for from_id in from_obj['crit'][from_cat].keys():
                # add critical features
                crit_to = df.loc[df['from_cat'] == from_cat]['to_cat'].values
                for to_cat in crit_to:
                    to_id=self.pickIDFromNodeCategory(self.config[gtype]['to_node'],to_cat, 'crit')
                    rec=[from_id,from_cat,to_id, to_cat]
                    gendata['base'].append(rec)
                    index=len(gendata['base'])-1
                    gendata['crit']=index
                    gendata['used'][to_id]=1
                # add some random sampled non-critical features
                non_crit_to = self.pickNonCritSamples(self.config[gtype]['to_node'],len(crit_to)*int(self.config[gtype]['non_crit_factor']), crit_to)
                for to_cat in non_crit_to.keys():
                    rec=[from_id,from_cat,non_crit_to[to_cat], to_cat]
                    gendata['base'].append(rec)
                    index=len(gendata['base'])-1
                    gendata['non-crit']=index
                    gendata['used'][non_crit_to[to_cat]]=1
        
        for from_cat in from_obj['non-crit'].keys():
            for from_id in from_obj['non-crit'][from_cat].keys():
                # add non-critical features
                crit_to = df.loc[df['from_cat'] == from_cat]['to_cat'].values
                for to_cat in crit_to:
                    to_id=self.pickIDFromNodeCategory(self.config[gtype]['to_node'],to_cat, 'non-crit')
                    rec=[from_id,from_cat,to_id, to_cat]
                    gendata['base'].append(rec)
                    index=len(gendata['base'])-1
                    gendata['non-crit']=index
                    gendata['used'][to_id]=1
                # add some random sampled non-critical features
                non_crit_to = self.pickNonCritSamples(self.config[gtype]['to_node'],len(crit_to)*int(self.config[gtype]['non_crit_factor']), crit_to)
                for to_cat in non_crit_to.keys():
                    rec=[from_id,from_cat,non_crit_to[to_cat], to_cat]
                    gendata['base'].append(rec)
                    index=len(gendata['base'])-1
                    gendata['non-crit']=index
                    gendata['used'][non_crit_to[to_cat]]=1
        return gendata

    def generateNode(self, gtype):
        gendata = dict()
        gendata['crit']= dict()
        gendata['non-crit']= dict()
        gendata['base']=[]

        groupnode = int(self.config[gtype]['groupnode'])
        #if (groupnode == 1):
        #    return gendata

        df = pd.read_csv(self.config['supervisor']['path'] + '/node_' + gtype + ".csv", usecols=self.config[gtype]['header'].split(","))        
        print(len(df.index))

        groupby_cat = {}
        for level in list(set(df[self.config[gtype]['cat']])):
            groupby_cat[level] = df.loc[df[self.config[gtype]['cat']] == level]

        critsize = int(float(self.config[gtype]['critprct'])*int(self.config[gtype]['catsize']))
        samplesize=int(self.config[gtype]['catsize'])
        senslow=float(self.config[gtype]['senslow'])
        sensup=float(self.config[gtype]['sensup'])

        for cat in groupby_cat:
            name=groupby_cat[cat]['name'].values[0]
            #print(name)
            
            # "labeled critical" nodes for supervised training

            gendata['crit'][name]=dict()

            for i in range(critsize):
                id = gtype + "-" + str(uuid.uuid1())
                if (groupnode == 0):
                    val=float(groupby_cat[cat]['kmval'].values[0])
                    minval=val - (val*senslow)
                    maxval=val + (val*sensup)
                    if val >= 1.0:
                        maxval = 0
                    genval = generate_in_range_float(minval, maxval)
                    rec=[id, name, genval]
                    # print("Crit: ", id, val, genval, minval, maxval)
                else:
                    rec=[id, name]
                    # print("Crit: ", id, name)
                gendata['base'].append(rec)
                index=len(gendata['base'])-1
                gendata['crit'][name][id]=index

            # "labeled non critical" nodes as control set

            gendata['non-crit'][name]=dict()

            for i in range(samplesize-critsize):
                id = gtype + "-" + str(uuid.uuid1())
                if (groupnode == 0):
                    val=float(groupby_cat[cat]['kmval'].values[0])
                    minval=0.0

                    # randomly eliminate rare activities
                    toss = rd.choice([True,False])
                    if log10(val) <= -2 and toss:
                        maxval=0
                    else:
                        maxval=val - (val*sensup)
                        
                    if val >= 1.0:
                        maxval = 0.0
                    genval = generate_in_range_float(minval, maxval)
                    rec=[id, name, genval]
                    # print("Non-Crit: ",id, val, genval, minval, maxval, log10(val), toss)
                else:
                    rec=[id, name]
                    # print("Non-Crit: ", id, name)

                gendata['base'].append(rec)
                index=len(gendata['base'])-1
                gendata['non-crit'][name][id]=index
        return gendata

# generate a random measure/kpi based expected range of values
def generate_in_range_float(min, max):
    value = random()
    if max == min and max == 0.0:
        value = 0.0
    elif max != 0.0:
        value = min + (value * (max - min)) 
    else:
        value= int(value*10)*1.0
    return value

