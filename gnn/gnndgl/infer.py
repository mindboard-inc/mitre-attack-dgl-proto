import dgl
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import pprint


from .model import MarginLoss, GRGCNModel
from .util import construct_negative_graph
from dgl.dataloading import MultiLayerFullNeighborSampler, NodeDataLoader

'''
TO VISIT the rationale(s) (https://discuss.dgl.ai/t/link-prediction-questions-train-test-accuracy-and-prediction/2177/16)
from the discussion thread (not covered in tutorial) for:
    - score calculation for inference:
        The pos_score is the logits for each edges. To get accuracy compute (pos_score>0.5).mean().
        The inference function is the calculation of the pos_score
    - no to little explanation on chice of parameters e.g. input, output, hidden layer size, coefficient for negative edges
        unstable when the defaults from sample code is changed.

    - very poor inference performance, somehow either due to the dgen generated training set:
        - 'detecting' kmeasure feature values with very small variation e.g. compare 0 for safe to 0.01 for detect (maybe just mark them as 1 or 0 -- and not an actual measure, or use logn instead)
        - far fewer detecting features and associated thread states than safe ones 
        - perhaps using weights on kmeasure feature values through the message passing/embeddings for kobs_state->features->kmeasure 
       or due to the training method/models:
        - perhaps using weights on kmeasure feature values through the message passing/embeddings for kobs_state->features->kmeasure 
            somehow the kmeasure value which is the only feature value of interest, does not seem to be carried through effectively through:        
                RGCNFull(in_features, hidden_features, out_features, rel_names)
                HeteroDotProductPredictor()

'''

def _infer_stub (model, g, input_g, dst_dict):
    in_label=input_g.nodes['kobs_state'].data['label'][0]
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
        '''
        print("\n ------ Source id:", src_id, ", Source label: ", src_node_lbl, ", i= ",i)
        print("\n ------ Dest id:", dst_id, ", Dest label: ", dst_node_lbl, ", i= ",i)
        print("\n PosScore ------", score)
        '''
        if (abs(ps) > 0.5 and in_label == src_node_lbl):
            if dst_node_lbl in res:
                score=max(score, res[dst_node_lbl]['score'])
            res[str(dst_node_lbl)]={'label':dst_dict[str(dst_node_lbl)], 'score': score}

    return res

def infer(dds, input_g,statepath, stub=0):    
    g = dds.graph
    dst_dict= dds.get_techniques() 
    in_feats = g.nodes['kobs_state'].data['feat'].shape[1]
    model = GRGCNModel(in_feats, in_feats, 6, g.etypes)
    optimizer = optim.Adam(model.parameters())
    loss_func = MarginLoss()
    checkpoint = torch.load(statepath)
    model.load_state_dict(checkpoint['model_state_dict'])
    optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    epoch = checkpoint['epoch']
    loss = checkpoint['loss']
    model.eval()
    if (stub >= 0): 
       return _infer_stub(model, g, input_g, dst_dict)
    
    #pprint.pprint(input_g)
    negative_graph = construct_negative_graph(input_g, 5, ('kobs_state', 'kdetects', 'ktechnique'))
    pos_score, neg_score = model(input_g, negative_graph, input_g.ndata['feat'], ('kobs_state', 'kdetects', 'ktechnique'))
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
        '''
        print("\n ------ Source id:", src_id, ", Source label: ", src_node_lbl, ", i= ",i)
        print("\n ------ Dest id:", dst_id, ", Dest label: ", dst_node_lbl, ", i= ",i)
        print("\n PosScore ------", score)
        '''
        if (abs(ps) > 0.5):
            if dst_node_lbl in res:
                score=max(score, res[dst_node_lbl]['score'])
            res[str(dst_node_lbl)]={'label':dst_dict[str(dst_node_lbl)], 'score': score}
    return res
    
