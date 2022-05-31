
# README for GNN Model, Training and Inference

## Project Structure
```

root /
    ->  gnnmodel 
        ->  gmodel      - Mitre Att&ck Graph Model utilities
        ->  dgen        - Sythetic K8S state and feature generator as a baseline for the DGLData Set
        ->  gnndgl         - DGL graph build processing, model training, testing and serialization
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

## Threat Detection Inference (gnninfer)

Detection of a modeled attack technique in effect through link prediction given:

 - Graph with observed State node(s) with 
 - Featured measures aggregated from run-time open-metrics
 
## Mitre Att&ck -> Nodes x Relations Extraction (gnnmodel/gmodel)

Utility code for extracting baseline Mitre Att&ack Graph data using Stix2 API under gmodel

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
## Test and Training Syntehtic Data Generation (dgen)

Utility code for generating baseline GNN model training and testing data under dgen.
Refer to dge.config.ini for generation/sampling settings.

### Generated / sampled nodes and edges
Nodes: 
 - kmeasure - Generate variation on critical (random value within threshold) and non critical (random value outside threshold) feature measures.
 - kobs_state - Generate critical (detecting a technique) and non-critical observed states.
Edges:
 - features - Generate kmeasure to kobs_state mappings for critical and non-critical kobs_state nodes and their featured kmeasures (supervised based on gmodel kdetects) + add variability by generating mappings for non-critical features from outside of the supervised mappings.
 - kdetects - Generate kobs_state to ktechnique mappings for critical kobs_state nodes (supervised based on gmodel kdetects)

### Referenced / connected knowledge nodes and edges
Nodes:
 - ktechnique - [AzM] Kubernetes Techniques
 - technique_k8s - Kubernetes scoped Techniques from [Att&]
 - tactics - Tactics from from [Att&]
 
Edges:
 - kbelongs_to - Referenced critical ktechnique to tactic mapping (supervised based on gmodel kbelongs_to)
 - overloads - Referenced critical ktechnique to mitre k8s technique mapping (supervised based on gmodel overloads)

