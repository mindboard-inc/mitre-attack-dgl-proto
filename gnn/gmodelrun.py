
import gmodel as gm
import config as cfg

def extract_k8s_mitre_graph ():

    config = cfg.load_config('./config/gmodel.config.ini')
    cti_config = cfg.get_config(config,'cti')
    outspec = cfg.get_config(config,'outspec')
    src = gm.pull_cti_data("enterprise-attack")

    graph = gm.build_graph_model (src, 'mitre-enterprise-attack', outspec["nodeexport"], outspec["edgeexport"], cti_config["scope"])
    gm.writeModel2Csv(graph,  outspec["path"])

if __name__ == '__main__':
    extract_k8s_mitre_graph()
    

