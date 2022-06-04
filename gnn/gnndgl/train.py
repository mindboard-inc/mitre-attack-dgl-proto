import dgl
import torch
import torch.nn as nn
import torch.optim as optim

from .util import construct_negative_graph
from .model import MarginLoss, GRGCNModel
from sklearn.metrics import roc_auc_score

'''
    The repos below provide full demo implementation for the actual DGL Heterogenous Link Prediction
    documentation and code samples at:
    https://docs.dgl.ai/en/latest/guide/training-link.html#heterogeneous-graphs
    https://github.com/dmlc/dgl
    
    The method borrowed from models and process available as full model training:
    https://github.com/ZZy979/pytorch-tutorial/blob/master/gnn/dgl/model.py
    https://github.com/ZZy979/pytorch-tutorial/blob/master/gnn/dgl/link_pred_hetero.py

    For mini-batch mode which we may need to implement for online training refer to:
    https://github.com/ZZy979/pytorch-tutorial/blob/master/gnn/dgl/link_pred_hetero_mb.py
    
'''
'''
    TO RE-VISIT compute_auc for review, not available in tutorial implementation, patched from 
    various other examples

    https://github.com/dmlc/dgl/tree/master/examples
'''
def compute_auc(pos_score, neg_score):
    scores = torch.cat([pos_score, neg_score]).detach().numpy()
    labels = torch.cat(
        [torch.ones(pos_score.shape[0]), torch.zeros(neg_score.shape[0])]).numpy()
    return roc_auc_score(labels, scores)

'''
TO RE-VISIT the rationale(s) (https://discuss.dgl.ai/t/link-prediction-questions-train-test-accuracy-and-prediction/2177/16)
from the discussion thread (not covered in tutorial) for:

    - training strategy without test, train:
        The link prediction does not need to split for training/test set. 
        In the semi supervised inductive node classification setting, only the label of the test nodes is invisible during the training phase, 
        but the topology and node itself is visible. Topology is the same for the training and test phase, in the inductive setting. 
    - score calculation for evalulation as well as and inference:
        The pos_score is the logits for each edges. To get accuracy compute (pos_score>0.5).mean().
        The inference function is the calculation of the pos_score
    - no to little explanation on chice of parameters e.g. input, output, hidden layer size, coefficient for negative edges
        unstable when the defaults from sample code is changed.
'''
def train(g,savepath=""):
    #print("\n\n-----------------\n", g.ndata)    
    k = 10
    #model = Model(in_feats, 20, 5, g.etypes)
    in_feats = g.nodes['kobs_state'].data['feat'].shape[1]

    # do not change the out_features -- 6 is the embedding dimension driven by in and our features 2 x 2 x 2
    model = GRGCNModel(in_feats, in_feats, 6, g.etypes)
    opt = optim.Adam(model.parameters())
    loss_func = MarginLoss()
    
    for epoch in range(10):
        negative_graph = construct_negative_graph(g, k, ('kobs_state', 'kdetects', 'ktechnique'))
        pos_score, neg_score = model(
            g, negative_graph, g.ndata['feat'], ('kobs_state', 'kdetects', 'ktechnique')
        )
        #pos_idx = 1*(pos_score > 0.5)
        print ("\nPOS Score: ", len(pos_score), " NEG Score: ", len(neg_score))
        #print(pos_idx)
        
        loss = loss_func(pos_score, neg_score)
        auc = compute_auc(pos_score, neg_score)
        opt.zero_grad()
        loss.backward()
        opt.step()
        print("Loss: ", loss.item(), " AUC: ", auc)


    if (savepath != "") :
        torch.save({
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': opt.state_dict(),
            'loss': loss
            }, savepath)
