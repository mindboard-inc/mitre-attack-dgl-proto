from re import A
import requests

from stix2 import MemoryStore
from stix2 import Filter

import gmodel as gm



# This pulls the data (JSON) version of interest from GitHub
# for containerized deployment we may use the local copy load

def pull_cti_data(domain, branch="master"):
    """get the ATT&CK STIX data from MITRE/CTI. Domain should be 'enterprise-attack', 'mobile-attack' or 'ics-attack'. Branch should typically be master."""
    stix_json = requests.get(f"https://raw.githubusercontent.com/mitre/cti/{branch}/{domain}/{domain}.json").json()
    return MemoryStore(stix_data=stix_json["objects"])

# Generic relation query to return source objects for a relation with optional target id reference(s) as filter
def get_source_by_target(src, reltype, srctype, target=[]):
    filters = [Filter('type', '=', 'relationship'),Filter('relationship_type', '=', reltype)]
    if (len(target)) > 0:
        filters.append(Filter('target_ref', 'in', target))
    rels = src.query(filters)
    sources = dict()
    print(str(len(rels)) + " relations fetched for " + reltype + ", referencing " + str(len(target)) + " targets")
    for rel in rels:
        refobj = src.get(rel.source_ref)
        if refobj['type'] == srctype:
            sources[rel.source_ref]= refobj
    print(str(len(sources.keys())) + " sources fetched for " + reltype + ", referencing " + str(len(target)) + " targets -- looking for: " + srctype)
    
    return sources

# Generic relation query to return target objects for a relation with optional source id reference(s) as filter
def get_target_by_source(src, reltype, tgttype, source=[]):
    filters = [Filter('type', '=', 'relationship'),Filter('relationship_type', '=', reltype)]
    if (len(source)) > 0:
        filters.append(Filter('target_ref', 'in', source))
    rels = src.query(filters)
    targets = dict()
    for rel in rels:
        refobj = src.get(rel.target_ref)
        if refobj['type'] == tgttype:
            targets[rel.target_ref]= refobj
    return targets

# pulling default scope per platform
def get_scope_for_container(src):
    return src.query([
        Filter('x_mitre_platforms', 'contains', 'Containers')
    ])

# All objects of a specified type by optional platform scope
def fetch_nodes_for_scope_by_type (src, nodetype, scope='*'):
    print ("Fetching: " + nodetype)
    filters = [Filter('type', '=', nodetype)]
    if scope !='*':
        filters.append(Filter('x_mitre_platforms', 'contains', scope))
    return src.query(filters)
    
def fetch_relations_for_scope_by_type(src, reltype, srcids=[], trgids=[]):
    filters = [Filter('type', '=', 'relationship'),Filter('relationship_type', '=', reltype)]
    if (len(srcids)) > 0:
        filters.append(Filter('source_ref', 'in', srcids))
    if (len(trgids)) > 0:
        filters.append(Filter('target_ref', 'in', trgids))

    return src.query(filters)

# Builds full set of attack pattern (core) nodes in scope 
def build_attack_core_in_scope(src, scope="*"):
    objects = fetch_nodes_for_scope_by_type(src, gm.NodeType.NODE_ATTACK_PATTERN.type, scope)
    nodes=dict()
    print("Fetched core attack base of: " + str(len(objects)) + " node(s)")
    for object in objects: 
        desc = gm.textNormalize(object.description)
        # nodes[object.id] = {'type': object.type, 'name':  object.name, 'desc': desc}
        nodes[object.id] = gm.Technique(object.id, object.name, desc)

   # Add all sub techniques otherwise ignored due to platform filter
    target = list(nodes.keys())
    source= get_source_by_target(src, 'subtechnique-of', gm.NodeType.NODE_ATTACK_PATTERN.type, target)
    for srcid in source.keys(): 
        desc = gm.textNormalize(source[srcid].description)
        # nodes[srcid] = {'type': source[srcid].type, 'name':  source[srcid].name, 'desc': desc}
        nodes[srcid] = gm.Technique(srcid, source[srcid].name, desc)

    print("Fetched extension of: " + str(len(source)) + " sub-technique attack-pattern(s)")
    # Extend ATTACK-PATTERN Matching for the specified scope 
    # Reverse-lookup via software using the technique othewise ignored due to platform

    malwares = fetch_nodes_for_scope_by_type(src, 'malware', scope)
    tools = fetch_nodes_for_scope_by_type(src, 'tool', scope)
    src_ids=[]
    for mw in malwares:
        src_ids.append(mw.id)
    for tool in tools:
        src_ids.append(tool.id)

    print("Fetched extension of: " + str(len(src_ids)) + " software ref attack-pattern(s)")
    if len(src_ids) > 0:
        targettec= get_target_by_source(src, 'uses', gm.NodeType.NODE_ATTACK_PATTERN.type, src_ids)
        for srcid in source.keys(): 
            desc = gm.textNormalize(source[srcid].description)
            # nodes[srcid] = {'type': source[srcid].type, 'name':  source[srcid].name, 'desc': desc}
            nodes[srcid] = gm.Technique(srcid, source[srcid].name, desc)
    return nodes

def build_nodes_in_scope(src, nodetypes, scope="*"):
    # As the node hierarchy is extended from attack-pattern at the core
    # we start with attack-types
    nodes = dict()
    # nodetypes=technique,observed_fact,asset,recommendation,software_malware,software_tool,actor
    techniques = build_attack_core_in_scope(src, scope)
    if (gm.NodeType.NODE_ATTACK_PATTERN.code in nodetypes):
        nodes[gm.NodeType.NODE_ATTACK_PATTERN.code]=techniques

    # we extend to data components and sources (observed_facts, assets), and data sources via 'detects'
    technique_ids=list(techniques.keys())
    if (gm.NodeType.NODE_DATA_COMPONENT.code in nodetypes or gm.NodeType.NODE_DATA_SOURCE.code in nodetypes):
        # we extend to data components and sources (observed_facts, assets), and data sources via 'detects'
        srcdatacomps= get_source_by_target(src, 'detects', gm.NodeType.NODE_DATA_COMPONENT.type, technique_ids)
        assets = dict()
        observedfacts = dict()
        for srcid in srcdatacomps.keys(): 
            desc = gm.textNormalize(srcdatacomps[srcid]['description'])
            observedfacts[srcid] = gm.ObservedFact(srcid, srcdatacomps[srcid]['name'], desc)
            refassetid=srcdatacomps[srcid]['x_mitre_data_source_ref']
            refasset=src.get(refassetid)
            rdesc = gm.textNormalize(refasset['description'])
            assets[refassetid]=gm.Asset(refassetid, refasset['name'], rdesc)
        nodes[gm.NodeType.NODE_DATA_COMPONENT.code]=observedfacts
        nodes[gm.NodeType.NODE_DATA_SOURCE.code]=assets

    # we extend to software - tool & malware via 'uses'
    if (gm.NodeType.NODE_TOOL.code in nodetypes or gm.NodeType.NODE_MALWARE.code in nodetypes):
        software = dict()
        malware= get_source_by_target(src, 'uses', gm.NodeType.NODE_MALWARE.type, technique_ids)
        for srcid in malware.keys(): 
            desc = gm.textNormalize(malware[srcid]['description'])
            software[srcid] = gm.Malware(srcid, malware[srcid]['name'], desc)
        tools= get_source_by_target(src, 'uses', gm.NodeType.NODE_TOOL.type, technique_ids)
        for srcid in tools.keys(): 
            desc = gm.textNormalize(tools[srcid]['description'])
            software[srcid] = gm.Tool(srcid, tools[srcid]['name'], desc)
        nodes[gm.NodeType.NODE_MALWARE.code]=software
    
    # we extend to actors with tool & malware (software) via 'uses'
    if gm.NodeType.NODE_INTRUSION_SET.code in nodetypes:
        actors = dict()
        software_ids= list(nodes[gm.NodeType.NODE_MALWARE.code].keys())
        actordict= get_source_by_target(src, 'uses', gm.NodeType.NODE_INTRUSION_SET.type, software_ids)
        for actid in actordict.keys(): 
            desc = "External references: " + str(len(actordict[actid]['external_references'])) + " - Revoked state: " + str(actordict[actid]['revoked'])
            actors[actid] = gm.IntrusionGroup(actid, actordict[actid]['name'], desc)
        nodes[gm.NodeType.NODE_INTRUSION_SET.code]=actors

    # we extend to recommendation with course-of-action via 'mitigates'
        #NODE_COURSE_OF_ACTION
    if gm.NodeType.NODE_COURSE_OF_ACTION.code in nodetypes:
        reccomendations = dict()
        recdict= get_source_by_target(src, 'mitigates', gm.NodeType.NODE_COURSE_OF_ACTION.type, technique_ids)
        for rectid in recdict.keys(): 
            desc = gm.textNormalize(recdict[rectid]['description'])
            reccomendations[rectid] = gm.Recommendation(rectid, recdict[rectid]['name'], desc)
        nodes[gm.NodeType.NODE_COURSE_OF_ACTION.code]=reccomendations

    return nodes


def build_edges_in_scope(src,nodes,edgetypes):
    edges= dict()

    technique_ids =list()
    dc_ids=list()
    software_ids=list()
    actor_ids=list()
    reco_ids=list()

    try :
        technique_ids= list(nodes[gm.NodeType.NODE_ATTACK_PATTERN.code].keys())
        dc_ids=list(nodes[gm.NodeType.NODE_DATA_COMPONENT.code].keys())
        software_ids=list(nodes[gm.NodeType.NODE_MALWARE.code].keys())
        actor_ids=list(nodes[gm.NodeType.NODE_INTRUSION_SET.code].keys())
        reco_ids=list(nodes[gm.NodeType.NODE_COURSE_OF_ACTION.code].keys())
    except:
        print ("Skipping some scoped ids")


    #edgeexport=uses,subtechnique_of,relates_to,mitigates,detects
    #starting with detects edge core of our approach
    if (gm.EdgeType.EDGE_DETECTS.code in edgetypes):
        # name, src_id, trg_id)
        detects=dict()
        rels=fetch_relations_for_scope_by_type(src, gm.EdgeType.EDGE_DETECTS.type, dc_ids, technique_ids) # srcids=[], trgids=[]
        for rel in rels: 
            detects[rel.id] = gm.Detects(rel.id, rel.source_ref, rel.target_ref)
        edges[gm.EdgeType.EDGE_DETECTS.code]=detects

    if (gm.EdgeType.EDGE_SUBTECHNIQUE_OF.code in edgetypes):
        subtechs=dict()
        rels=fetch_relations_for_scope_by_type(src, gm.EdgeType.EDGE_SUBTECHNIQUE_OF.type, [], technique_ids) # srcids=[], trgids=[]
        for rel in rels: 
            subtechs[rel.id] = gm.IsSubtechniqueOf(rel.id, rel.source_ref, rel.target_ref)
        edges[gm.EdgeType.EDGE_SUBTECHNIQUE_OF.code]=subtechs
    
    if (gm.EdgeType.EDGE_RELATES_TO.code in edgetypes):
        relates=dict()
        for dcid in dc_ids:
            refdc=src.get(dcid)
            relid = dcid.replace('x-mitre-data-component--', '') + refdc['x_mitre_data_source_ref'].replace('x-mitre-data-source--', '')
            relates[relid] = gm.RelatesTo(relid, dcid, refdc['x_mitre_data_source_ref'])
        edges[gm.EdgeType.EDGE_RELATES_TO.code]=relates

    if (gm.EdgeType.EDGE_USES.code in edgetypes):
        uses=dict()
        softuses=fetch_relations_for_scope_by_type(src, gm.EdgeType.EDGE_USES.type,software_ids, technique_ids) # srcids=[], trgids=[]
        for rel in softuses: 
            uses[rel.id] = gm.Uses(rel.id, rel.source_ref, rel.target_ref)
        actuses=fetch_relations_for_scope_by_type(src, gm.EdgeType.EDGE_USES.type,actor_ids, software_ids) # srcids=[], trgids=[]
        for rel in actuses: 
            uses[rel.id] = gm.Uses(rel.id, rel.source_ref, rel.target_ref)
        edges[gm.EdgeType.EDGE_USES.code]=uses

    if (gm.EdgeType.EDGE_MITIGATES.code in edgetypes):
        # name, src_id, trg_id)
        mitigates=dict()
        rels=fetch_relations_for_scope_by_type(src, gm.EdgeType.EDGE_MITIGATES.type, reco_ids, technique_ids) # srcids=[], trgids=[]
        for rel in rels: 
            mitigates[rel.id] = gm.Detects(rel.id, rel.source_ref, rel.target_ref)
        edges[gm.EdgeType.EDGE_MITIGATES.code]=mitigates

    return edges


def build_graph_model (src, name, nodetypes, edgetypes, scope="*"):
    
    nodes=gm.build_nodes_in_scope(src, nodetypes, scope)
    edges = gm.build_edges_in_scope(src,nodes,edgetypes)
    graph=gm.Graph(name, nodes, edges)

    return  graph

