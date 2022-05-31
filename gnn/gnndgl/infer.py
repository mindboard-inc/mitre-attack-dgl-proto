import dgl
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import pprint


from .model import MarginLoss, GRGCNModel
from .util import construct_negative_graph, build_label_dict
from dgl.dataloading import MultiLayerFullNeighborSampler, NodeDataLoader


def infer(g, input_g,statepath, labelpath):
    dst_dict= build_label_dict(labelpath + "/ktechnique.csv")
    in_feats = g.nodes['kobs_state'].data['feat'].shape[1]
    # this is a temporary placeholder match on obs_state label, treating the model as offline inference -- 
    # it needs to change to an online inference, with model being trained as new
    # observed states  and k-measures are accumulated.

    in_label=input_g.nodes['kobs_state'].data['label'][0]
    model = GRGCNModel(in_feats, in_feats, 6, g.etypes)
    optimizer = optim.Adam(model.parameters())
    loss_func = MarginLoss()
    checkpoint = torch.load(statepath)
    model.load_state_dict(checkpoint['model_state_dict'])
    optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    epoch = checkpoint['epoch']
    loss = checkpoint['loss']

    model.eval()
    #pprint.pprint(input_g)
    negative_graph = construct_negative_graph(g, 5, ('kobs_state', 'kdetects', 'ktechnique'))
    pos_score, neg_score = model(g, negative_graph, g.ndata['feat'], ('kobs_state', 'kdetects', 'ktechnique'))
    #pos_idx = 1*(pos_score > 0.5)
    res={}
    for i in range(len(pos_score)):
        ps = pos_score[i]
        dstdata=g.find_edges(torch.tensor([i]), 'kdetects')[1].tolist()
        srcdata=g.find_edges(torch.tensor([i]), 'kdetects')[0].tolist()
        src_id=srcdata[0]
        dst_id=dstdata[0]
        src_node_lbl=g.nodes['kobs_state'].data['label'][src_id].tolist()
        dst_node_lbl=g.nodes['ktechnique'].data['label'][dst_id].tolist()
        score=ps[0].tolist()
        #print("\n ------ Source id:", src_id, ", Source label: ", src_node_lbl, ", i= ",i)
        #print("\n ------ Dest id:", dst_id, ", Dest label: ", dst_node_lbl, ", i= ",i)
        #print("\n PosScore ------", score)
        if (abs(ps) > 0.5 and in_label == src_node_lbl):
            if dst_node_lbl in res:
                score=max(score, res[dst_node_lbl]['score'])
            res[str(dst_node_lbl)]={'label':dst_dict[str(dst_node_lbl)], 'score': score}
    return res
    
