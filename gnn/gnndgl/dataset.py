import dgl
from dgl.data import CSVDataset
from dgl.data import DGLDataset
import torch
import pprint
import numpy as np

from .util import build_label_dict

'''
    dgl.data CSVDataset read of the core model
    
    TO BE REPLACED with a custom loader -- 
    CSVDataset loader breaks if nodes have less then 2 features (generates an value array instead of tensor array)

'''
class GModelDataSet(DGLDataset):
    def __init__(self, config):
        self.config=config
        self.modelpath=config['iospec']['path'] + "/gmodel.pt"
        self.labelpath=config['iospec']['path'] + "/labels"
        # Load informative ktechnique labels
        self.ktechnique_dict= build_label_dict(self.labelpath + "/ktechnique.csv")
        super().__init__(name=self.config['iospec']['modelname'])
        
        
    def process(self):
        dataset = CSVDataset(self.config['iospec']['path'])
        self.graph = dataset[0] 
        
        '''
        DGB
        n_kobs_state=self.graph.nodes['kobs_state'].data['feat'].shape[0]
        n_kdetects=len(self.graph.edges(etype='kdetects')[0])
        print("\nn_kobs_state: ", n_kobs_state, "\nkdetects: ", n_kdetects)
        '''
        # COMMENTING OUT below:
        #   Not sure why do the train mask in sample code, when they never use it, they train the graph in its entirety

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

    def get_techniques(self):
        return self.ktechnique_dict
        
    def __getitem__(self, i):
        return self.graph
    
    def __len__(self):
        return 1

'''
    Inference test graph builder
        * single kobs_state node (source node)
        * sampled kmeasures x features edges
        * 35 destination ktechniques nodes checked against for detection

'''
class KDetectDataset(DGLDataset):
    def __init__(self, graphdef, model_g):
        
        super().__init__('kdetect_temp')
        # kobs_state source mapping
        features_src=[]
        src_idx={}
        for i in range(len(graphdef["nodes"]["kobs_state"])) :
            src_idx[graphdef["nodes"]["kobs_state"][i]["node_id"]]=i
        for edge in graphdef["edges"]["features"] :
            features_src.append(src_idx[edge['src_id']])

        # kobs to measure dest mapping
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

       # kobs to technique dest mapping
        kdetects_dst=np.arange(model_g.graph.nodes['ktechnique'].data['feat'].shape[0])
        kdetects_src=np.zeros((len(kdetects_dst),), dtype=int)

        kdst_feat = []
        kdst_lbl = []
        for idx in kdetects_dst:
            kdst_feat.append(model_g.graph.nodes['ktechnique'].data['feat'][idx].tolist())
            kdst_lbl.append(model_g.graph.nodes['ktechnique'].data['label'][idx].item())

        '''
        DBG
        print("\nktechniques:", kdetects_dst, "\nkmeasures:", features_dst, "\nkobs_state:", features_src)
        print("\n--------\nkobs features:", src_feat, "\n kobs labels:", src_label, "\nlabels:", kdst_lbl, "\nfeatures:", kdst_feat)
        '''
        g = dgl.heterograph({

            ('kobs_state', 'features', 'kmeasure'): (features_src, features_dst),
            ('kmeasure', 'featured_by', 'kobs_state'): (features_dst, features_src),
            ('kobs_state', 'kdetects', 'ktechnique'): (kdetects_src, kdetects_dst),
            ('ktechnique', 'kdetected_by', 'kobs_state'): (kdetects_dst, kdetects_src)
        }, num_nodes_dict={'kobs_state': len(src_feat), 'kmeasure': len(dst_feat), 'ktechnique': len(kdetects_dst)})

        g.nodes['kobs_state'].data['feat'] = torch.as_tensor(src_feat)
        g.nodes['kmeasure'].data['feat'] = torch.as_tensor(dst_feat)
        g.nodes['kobs_state'].data['label'] = torch.as_tensor(src_label)
        g.nodes['kmeasure'].data['label'] = torch.as_tensor(dst_label)

        g.nodes['ktechnique'].data['label'] = torch.as_tensor(kdst_lbl)
        g.nodes['ktechnique'].data['feat'] = torch.as_tensor(kdst_feat)

        self.g = g



    def process(self):
        pass

    def __getitem__(self, idx):
        if idx != 0:
            raise IndexError('This dataset has only one graph')
        return self.g
    

    def __len__(self):
        return 1

