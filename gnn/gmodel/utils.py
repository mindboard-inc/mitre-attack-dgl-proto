import csv
import gmodel as gm

# io utils
# csv node dump
def write2Csv(objectdict, header, path):
    objdata=[] 
    with open(path, 'w', encoding='UTF8', newline='') as f:
        for obj in objectdict.values():
            objdata.append(obj.getFeatureData())
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(objdata)

# csv full model dump

def writeModel2Csv(graph, path):
    nodes=graph.getNodes()
    edges=graph.getEdges()
    # print( nodes.keys())
    for nkey in nodes.keys():
        node=nodes[nkey]
        # print("Writing " + nkey + " count:" + str(len(node.keys())))
        write2Csv(node, gm.Node.getFeatureHeader(), path  + '/node/' + nkey + '.csv')
    for ekey in edges.keys():
        edge=edges[ekey]
        # print("Writing " + nkey + " count:" + str(len(edge.keys())))
        write2Csv(edge, gm.Edge.getFeatureHeader(), path  + '/edge/' + ekey + '.csv')
    return
    



# other
def textNormalize(intext):
    outtext= intext.replace('\n', ' ').replace('\r', '').replace('"', '')
    return outtext
