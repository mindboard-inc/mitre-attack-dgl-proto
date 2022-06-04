import dgl.function as fn
import torch
import torch.nn as nn
import torch.nn.functional as F
from dgl.nn import GraphConv, SAGEConv, HeteroGraphConv


'''

    The repos below provides full demo implementation for the actual DGL Heterogenous Link Prediction
    documentation and code samples at:
    https://docs.dgl.ai/en/latest/guide/training-link.html#heterogeneous-graphs

    The method borrowed from models and process available as full model training:
    https://github.com/ZZy979/pytorch-tutorial/blob/master/gnn/dgl/model.py
    https://github.com/ZZy979/pytorch-tutorial/blob/master/gnn/dgl/link_pred_hetero.py

    For mini-batch mode which we may need to implement for online training refer to:
    https://github.com/ZZy979/pytorch-tutorial/blob/master/gnn/dgl/link_pred_hetero_mb.py
    
'''

class SAGEFull(nn.Module):

    def __init__(self, in_feats, hid_feats, out_feats):
        super().__init__()
        self.conv1 = SAGEConv(in_feats, hid_feats, 'mean')
        self.conv2 = SAGEConv(hid_feats, out_feats, 'mean')

    def forward(self, g, inputs):
        # inputs are features of nodes
        h = F.relu(self.conv1(g, inputs))
        h = self.conv2(g, h)
        return h


class RGCNFull(nn.Module):

    def __init__(self, in_feats, hid_feats, out_feats, rel_names):
        super().__init__()
        self.conv1 = HeteroGraphConv({
            rel: GraphConv(in_feats, hid_feats) for rel in rel_names
        }, aggregate='sum')
        self.conv2 = HeteroGraphConv({
            rel: GraphConv(hid_feats, out_feats) for rel in rel_names
        }, aggregate='sum')

    def forward(self, g, inputs):
        #print(inputs)
        h = self.conv1(g, inputs)
        h = {k: F.relu(v) for k, v in h.items()}
        h = self.conv2(g, h)
        return h


class RGCN(nn.Module):

    def __init__(self, in_feats, hid_feats, out_feats, rel_names):
        super().__init__()
        self.conv1 = HeteroGraphConv({
            rel: GraphConv(in_feats, hid_feats) for rel in rel_names
        }, aggregate='sum')
        self.conv2 = HeteroGraphConv({
            rel: GraphConv(hid_feats, out_feats) for rel in rel_names
        }, aggregate='sum')

    def forward(self, blocks, inputs):
        h = self.conv1(blocks[0], inputs)
        h = {k: F.relu(v) for k, v in h.items()}
        h = self.conv2(blocks[1], h)
        return h


class HeteroDotProductPredictor(nn.Module):

    def forward(self, graph, h, etype):
        # h contains the node representations for each edge type computed from node_clf_hetero.py
        with graph.local_scope():
            graph.ndata['h'] = h  # assigns 'h' of all node types in one shot
            graph.apply_edges(fn.u_dot_v('h', 'h', 'score'), etype=etype)
            return graph.edges[etype].data['score']

'''
    Carried over for potentail use in inference
    
'''

class HeteroMLPPredictor(nn.Module):

    def __init__(self, in_features, out_classes):
        super().__init__()
        self.W = nn.Linear(in_features * 2, out_classes)

    def apply_edges(self, edges):
        score = self.W(torch.cat([edges.src['h'], edges.dst['h']], dim=1))
        return {'score': score}

    def forward(self, graph, h, etype):
        # h contains the node representations for each edge type computed from node_clf_hetero.py
        with graph.local_scope():
            graph.ndata['h'] = h  # assigns 'h' of all node types in one shot
            graph.apply_edges(self.apply_edges, etype=etype)
            return graph.edges[etype].data['score']

class MarginLoss(nn.Module):

    def forward(self, pos_score, neg_score):
        return (1 - pos_score + neg_score.view(pos_score.shape[0], -1)).clamp(min=0).mean()

'''
    TO VISIT for poor inference performance, perhaps due to the training method/models:
        - exploring using weights on kmeasure feature values through the message passing/embeddings for kobs_state->features->kmeasure 
            somehow the kmeasure value which is the only feature value of interest, does not seem to be carried through effectively through:        
                RGCNFull(in_features, hidden_features, out_features, rel_names)
                HeteroDotProductPredictor()

'''
class GRGCNModel(nn.Module):
    def __init__(self, in_features, hidden_features, out_features, rel_names):
        super().__init__()
        self.rgcn = RGCNFull(in_features, hidden_features, out_features, rel_names)
        self.pred = HeteroDotProductPredictor()

    def forward(self, g, neg_g, x, etype):
        h = self.rgcn(g, x)
        return self.pred(g, h, etype), self.pred(neg_g, h, etype)


'''
    Alternative Model  extended to all edges and not only the predicted one
    per https://discuss.dgl.ai/t/for-link-prediction-inference-how-can-i-score-every-pair-of-nodes-from-new-unseen-graphs-with-no-positive-edges/2312
'''
class MLP(nn.Module):
    def __init__(self, out_feats):
        super().__init__()
        self.layer = nn.Sequential(
                        nn.Linear(out_feats, out_feats),
                        nn.ReLU(),
                        nn.Linear(out_feats, out_feats)
                     )

    def forward(self, x):
        return self.layer(x)

class HeteroDotProductPredictorAlt(nn.Module):
    def __init__(self, graph, h, out_feats, etypes):
        super().__init__()
        self.etype_project[edge]={}
        for edge in etypes:
            self.etype_project[edge] = MLP(out_feats)
    def forward(self, graph, h, etype):
        # h contains the node representations for each node type computed from
        # the GNN defined in the previous section (Section 5.1).
        with graph.local_scope():
            graph.ndata['h'] = self.etype_project[etype](h)
            graph.apply_edges(fn.u_dot_v('h', 'h', 'score'), etype=etype)
            return graph.edges[etype].data['score']

'''
    Alternatives end
'''