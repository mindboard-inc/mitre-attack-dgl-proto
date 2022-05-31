import csv
import config as cfg
import gnndgl as ddm
import json
import pprint

def build_train_save():
    config = cfg.load_config_full('./config/dgl.config.ini')
    ddsgraph = ddm.GModelDataSet(config)
    ddsgraph.process()
    print("\nInitial Build\n-------------------------\n")
    ddsgraph.dump()
    #ddsgraph.saveGraph()
    # print("\n\nLoaded Build\n-------------------------\n")
    #ddsgraph.dump()

    print("\n\nStarting training Build\n-------------------------\n")
    ddm.train(ddsgraph.graph, ddsgraph.modelpath)
    print("\n\nOut!\n-------------------------\n")

def load_and_infer():
    config = cfg.load_config_full('./config/dgl.config.ini')
    ddsgraph = ddm.GModelDataSet(config)
    ddsgraph.process()
    #ddsgraph.dump()

    # Test JSON file
    f = open('test/predict.json')
    data = json.load(f)
    #pprint.pprint(data["payload"]["input_graph"])
    f.close()
    if (data["payload"]["demo"] == "off"):
        input_graph=ddm.KDetectDataset(data["payload"]["input_graph"])
        print("\n\nStarting Inference Call\n-------------------------\n")
        res=ddm.infer(ddsgraph.graph, input_graph[0], ddsgraph.modelpath, ddsgraph.labelpath)
    elif (data["payload"]["demo"] == "detect"):
        print("\n\nStarting Demo Inference Call: Threat Detected Status\n-------------------------\n")
    else:
        print("\n\nStarting Demo Inference Call: Safe Status\n-------------------------\n")

    print("\n\n---------------------", res, "\nmatch count: ", len(res.keys()))

if __name__ == '__main__':
    #build_train_save()
    load_and_infer()
    
    

