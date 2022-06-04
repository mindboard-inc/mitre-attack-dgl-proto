import config as cfg
import gnndgl as ddm
import json
import argparse
import numpy as np

def build_train_save(config):
    ddsgraph = ddm.GModelDataSet(config)
    ddsgraph.process()
    print("\nInitial Build\n-------------------------\n")
    ddsgraph.dump()
    print("\n\nStarting Training\n-------------------------\n")
    ddm.train(ddsgraph.graph, ddsgraph.modelpath)
    print("\n\nOut!\n-------------------------\n")

def load_and_infer(config, demo):
    ddsgraph = ddm.GModelDataSet(config)
    ddsgraph.process()
    
    # Test JSON file
    f=None
    mode=""
    if (demo <0):
        f = open('test/off.json')
        mode="OFF"
    elif (demo < 1):
        f = open('test/safe.json')
        mode="ON-SAFE"
    else:
        f = open('test/predict.json')
        mode="ON-PREDICT"
    
    data = json.load(f)
    f.close()
    input_graph=ddm.KDetectDataset(data["payload"]["input_graph"],ddsgraph)
    
    print("Starting Inference Call\nDemo Mode: ", mode, "\n-------------------------\n")
    res=ddm.infer(ddsgraph, input_graph[0], ddsgraph.modelpath, demo)
    print(res, "\nmatch count: ", len(res.keys()))

if __name__ == '__main__':
    config = cfg.load_config_full('./config/dgl.config.ini')
    parser = argparse.ArgumentParser(prog='DGLRUN', usage='%(prog)s [options]',description='KDetectTester')
    parser.add_argument("--build", type=int, default=0,
            help="build mode")
    parser.add_argument("--infer", type=int, default=0,
            help="infer mode [default]")
    parser.add_argument("--demo", type=int, default=-1,
            help="demo mode [default -1=off 0=safe 1=predict]")
    args = parser.parse_args()

    if (len( vars(args) ) < 1):
        print("Specify build mode (--build) vs infer mode (--infer)")
        exit(0)
    if (args.build > 0):
        build_train_save(config)
        if (args.infer > 0):
            load_and_infer(config, args.demo)
    else:
        load_and_infer(config, args.demo)


    

