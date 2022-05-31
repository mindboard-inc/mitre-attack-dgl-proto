import gnndgl
import dgl
from dgl.data import CSVDataset
from dgl.data import DGLDataset
import torch
import numpy as np
import pprint
import csv


class GModelDataSet(DGLDataset):
    def __init__(self, config):
        self.config=config
        self.modelpath=config['iospec']['path'] + "/gmodel.pt"
        self.labelpath=config['iospec']['path'] + "/labels"
        super().__init__(name=self.config['iospec']['modelname'])
        
        
    def process(self):
        dataset = CSVDataset(self.config['iospec']['path'])
        
        self.graph = dataset[0] 
        n_kobs_state=self.graph.nodes['kobs_state'].data['feat'].shape[0]
        n_kdetects=len(self.graph.edges(etype='kdetects')[0])
        #print("\nn_kobs_state: ", n_kobs_state, "\nkdetects: ", n_kdetects)
        #self.graph.nodes['kobs_state'].data['train_mask'] = torch.zeros(n_kobs_state, dtype=torch.bool).bernoulli(0.6)
        #self.graph.edges['kdetects'].data['train_mask'] = torch.zeros(n_kdetects, dtype=torch.bool).bernoulli(0.6)

    
    def dump(self):
        pprint.pprint(self.graph)

    def loadGraph(self,path):
        (g,), _ = dgl.load_graphs(path)
        self.graph = g
        return 
    
    def saveGraph(self):
        dgl.save_graphs(self.config['iospec']['path'] + "/ggraph.dgl", self.graph)
        return 
        
    def __getitem__(self, i):
        return self.graph
    
    def __len__(self):
        return 1

class KDetectDataset(DGLDataset):
    def __init__(self, graphdef):
        super().__init__('kdetect_temp')
        # kobs_state source mapping
        features_src=[]
        src_idx={}
        for i in range(len(graphdef["nodes"]["kobs_state"])) :
            src_idx[graphdef["nodes"]["kobs_state"][i]["node_id"]]=i
        for edge in graphdef["edges"]["features"] :
            features_src.append(src_idx[edge['src_id']])

        # kobs_measure dest mapping
        features_dst=[]
        dst_idx={}
        for i in range(len(graphdef["nodes"]["kmeasure"])) :
            dst_idx[graphdef["nodes"]["kmeasure"][i]["node_id"]]=i
        for edge in graphdef["edges"]["features"] :
            features_dst.append(dst_idx[edge['dst_id']])

        src_feat = []
        for node in graphdef["nodes"]["kobs_state"] :
            src_feat.append(node['feat'])

        dst_feat = []
        for node in graphdef["nodes"]["kmeasure"] :
            dst_feat.append(node['feat'])

        src_label =[]
        for node in graphdef["nodes"]["kobs_state"] :
            src_label.append(node['label'])
        dst_label =[]
        for node in graphdef["nodes"]["kmeasure"] :
            dst_label.append(node['label'])

        #print(features_src, "\n", features_dst)
        g = dgl.heterograph({
            ('kobs_state', 'features', 'kmeasure'): (features_src, features_dst),
            ('kmeasure', 'featured_by', 'kobs_state'): (features_dst, features_src)
        }, num_nodes_dict={'kobs_state': len(src_feat), 'kmeasure': len(dst_feat)})

        g.nodes['kobs_state'].data['feat'] = torch.as_tensor(src_feat)
        g.nodes['kmeasure'].data['feat'] = torch.as_tensor(dst_feat)
        g.nodes['kobs_state'].data['label'] = torch.as_tensor(src_label)
        g.nodes['kmeasure'].data['label'] = torch.as_tensor(dst_label)

        self.g = g

    def process(self):
        pass

    def __getitem__(self, idx):
        if idx != 0:
            raise IndexError('This dataset has only one graph')
        return self.g

    def __len__(self):
        return 1

