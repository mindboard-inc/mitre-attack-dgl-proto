
import config as cfg
import dgen as gen

def generate_gnn_test_train_data ():
    config = cfg.load_config_full('./config/dgen.config.ini')
    generator = gen.DGenerator(config)
    
    generator.generate()
    generator.dumpGenModel()
    #print(genmodel)

if __name__ == '__main__':
    generate_gnn_test_train_data ()

    

