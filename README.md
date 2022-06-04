
# README for GNN Model, Training and Inference

## Project Structure
```

root /
    ->  gnn 
    
        ->  gmodel      - Mitre Att&ck Graph Model utilities
        ->  dgen        - Sythetic K8S state and feature generator utility as a baseline for the DGLData Set
        ->  gnndgl      - DGL graph build processing, model training, testing, inference and serialization
        
    -> gnninfer         - Link prediction inference service embedding with serialized DGL graph model. 
                          Expects a (observed state) kobs_state and associated kmeasure graph for scoring attack technique detection
    -> notifyadapter    - Issues PromQL to pull kmeasure features from TimescaleDB, builds a graph object with kobs_state for scoring inference, calls gnninfer service

```

## Model Structure

Graph model based on:

 - [Att&] Mitre Att&ck 
 - [AzM] MS Azure Security Kubernetes attack matrix 

Features a baseline selection of:

  - Tactic: Tactics
  - Mk-Tech-K8s: Kubernetes scoped Techniques from [Att&] Techniques
  - K-Tech: [AzM] Kubernetes Techniques overloading/specializing Mk-Tech-K8s
  - Mappings between Mk-Tech-K8s and K-Tech
  - Mappings between Tactics and Techniques

The model provides new graph nodes and relations as an extention of technique detection with:

 - K-Obs-State: Kubernetes observed state 
 - K-Measure: Kubernetes measures aggregating a set of key metrics 
 - Relations linking observed state and its featured measures
 - Relations linking observed states as detectors of specialized kubernetes techniques

## DGL GNN Threat Detection Inference (gnn/gnndgl)

Detection of a modeled attack technique in effect through link prediction given:

 - Graph with observed State node, along with,
 - Featured measures aggregated from run-time open-metrics

<img src="./img\neo4j.png" alt="neo4j" style="zoom:95%;" />



DGL Hetergenous graph link predition baseline implementation providing capabilities to:

- Build training and online inference testing datasets (gnn/gnndgl/dataset.py)
- DGL - PyTorch model definitions (`gnn/gnndgl/model.py`)
- Training (`gnn/gnndgl/train.py`)
- Inference (`gnn/gnndgl/infer.py`)

Refer to `gnn/config/dgl.config.ini` for dataset contruction, training and inference settings. 

Script for testing/debugging: `[ROOT]/gnn/dglrun.py`

**<u>Building DGL Threat Detection Dataset and Training</u>** 

```
(venv) gnn$ python dglrun.py --build 1
Done loading data from cached files.
Done loading data from cached files.

Initial Build
-------------------------

Graph(num_nodes={'kmeasure': 3139, 'kobs_state': 3700, 'ktechnique': 35},
      num_edges={('kmeasure', 'featured_by', 'kobs_state'): 57650, ('kobs_state', 'features', 'kmeasure'): 57650, ('kobs_state', 'kdetects', 'ktechnique'): 350, ('ktechnique', 'kdetected_by', 'kobs_state'): 350},
      metagraph=[('kmeasure', 'kobs_state', 'featured_by'), ('kobs_state', 'kmeasure', 'features'), ('kobs_state', 'ktechnique', 'kdetects'), ('ktechnique', 'kobs_state', 'kdetected_by')])     
Starting Training
-------------------------
POS Score:  350  NEG Score:  3500
/mnt/c/workspace/aiops/sec-inference/venv/lib/python3.9/site-packages/torch/autocast_mode.py:162: UserWarning: User provided device_type of 'cuda', but CUDA is not available. Disabling
  warnings.warn('User provided device_type of \'cuda\', but CUDA is not available. Disabling')
Loss:  0.9986863136291504  AUC:  0.5069040816326531

....

POS Score:  350  NEG Score:  3500
/mnt/c/workspace/aiops/sec-inference/venv/lib/python3.9/site-packages/torch/autocast_mode.py:162: UserWarning: User provided device_type of 'cuda', but CUDA is not available. Disabling
  warnings.warn('User provided device_type of \'cuda\', but CUDA is not available. Disabling')
Loss:  1.000283122062683  AUC:  0.5033383673469387

POS Score:  350  NEG Score:  3500
/mnt/c/workspace/aiops/sec-inference/venv/lib/python3.9/site-packages/torch/autocast_mode.py:162: UserWarning: User provided device_type of 'cuda', but CUDA is not available. Disabling
  warnings.warn('User provided device_type of \'cuda\', but CUDA is not available. Disabling')
Loss:  0.9985541701316833  AUC:  0.5101726530612245
```

**<u>Loading Trained DGL Threat Detection Dataset and Model for Inference</u>** 

```
(venv) gnn$ python dglrun.py --infer 1 --demo 1
Done loading data from cached files.
Done loading data from cached files.
Starting Inference Call

Demo Mode:  ON-PREDICT
-------------------------

{'121': {'label': 'List Kubernetes secrets - TA0006', 'score': 0.5112453103065491}}
match count:  1

(venv) gnn$ python dglrun.py --infer 1 --demo 0
Done loading data from cached files.
Done loading data from cached files.
Starting Inference Call

Demo Mode:  ON-SAFE
-------------------------

{}
match count:  0
(venv) zdodd@LAPTOP-QM6CVUOB:/mnt/c/workspace/aiops/sec-inference/gnn$ python dglrun.py --infer 1 demo -1
Done loading data from cached files.
Done loading data from cached files.
Starting Inference Call

Demo Mode:  OFF
-------------------------

{}
match count:  0

```



## Mitre Att&ck -> Nodes x Relations Extraction (gnn/gmodel)

Utility code for extracting reference edges and nodes from the latest MITRE Att&ck release Graph data using Stix2 API.
Refer to `gnn/config/gmodel.config.ini` for settings. Script for testing/debugging:

`[ROOT]/gnn/gmodelrun.py`

### Extracted baseline Att&ck data

    (1) intrusion-set - [uses] -> attack-pattern 
    (2) malware - [uses] -> attack-pattern
    (3) course-of-action - [mitigates] -> attack-pattern  
    (4) x-mitre-data-component - [detects] -> attack-pattern  
    (5) attack-pattern  - [subtechnique-of] -> attack-pattern 
    (6) x-mitre-data-component - [relates-to] -> x_mitre_data_source

### Container/Kubernetes scoping and node/edge extraction
```
for all attack patterns get sources (malware, intrusion-set) for uses
    populate malware
    populate intrusion-set
    populate relation-uses

for all attack patterns get source  x-mitre-data-component for detects
    for all x-mitre-data-component x_mitre_data_source_ref 
        populate data-source
        populate relation-detects

for all attack patterns get source course-of-action for mitigates
    populate course-of-action
    populate relation-mitigates

for all attack patterns get target attack patterns for subtechnique-of
    update attack pattern
    populate subtechnique-of
```
## Test and Training Syntehtic Data Generation (gnn/dgen)

Utility code for generating baseline GNN model training and testing data under dgen.
Refer to `gnn/config/dge.config.ini` for generation/sampling settings.

`[ROOT]/gnn/gmodelrun.py`

### Generated / sampled nodes and edges
Nodes: 
 - kmeasure - Generate variation on critical (random value within threshold) and non critical (random value outside threshold) feature measures.
 - kobs_state - Generate critical (detecting a technique) and non-critical observed states.
Edges:
 - features - Generate kmeasure to kobs_state mappings for critical and non-critical kobs_state nodes and their featured kmeasures (supervised based on gmodel kdetects) + add variability by generating mappings for non-critical features from outside of the supervised mappings.
 - kdetects - Generate kobs_state to ktechnique mappings for critical kobs_state nodes (supervised based on gmodel kdetects)

### Referenced / connected knowledge nodes and edges
*Nodes:*

 - ktechnique - [AzM] Kubernetes Techniques
 - technique_k8s - Kubernetes scoped Techniques from [Att&]
 - tactics - Tactics from from [Att&]

*Edges:*

 - kbelongs_to - Referenced critical ktechnique to tactic mapping (supervised based on gmodel kbelongs_to)
 - overloads - Referenced critical ktechnique to mitre k8s technique mapping (supervised based on gmodel overloads)

