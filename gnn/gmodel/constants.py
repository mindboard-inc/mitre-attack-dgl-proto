from enum import Enum

# MITRE Att&ck

class NodeType(Enum):

    def __init__(self, type, gmap):
        self.type = type
        self.code = gmap

    ATTACK_BASE='object', 'node'
    NODE_ATTACK_PATTERN='attack-pattern', 'technique'
    NODE_DATA_COMPONENT='x-mitre-data-component', 'observed_fact'
    NODE_DATA_SOURCE='x-mitre-data-source', 'asset'
    NODE_COURSE_OF_ACTION='course-of-action', 'recommendation'
    NODE_INTRUSION_SET='intrusion-set', 'actor'
    NODE_TOOL='tool', 'software'
    NODE_MALWARE='malware', 'software'


# NodeType.NODE_ATTACK_PATTERN.gmap # returns 'technique'

class EdgeType(Enum):

    def __init__(self, type, gmap):
        self.type = type
        self.code = gmap

    ATTACK_BASE='relation', 'edge'
    EDGE_USES='uses', 'uses'
    EDGE_SUBTECHNIQUE_OF='subtechnique-of', 'subtechnique_of'
    EDGE_RELATES_TO='x_mitre_data_source_ref', 'relates_to'
    EDGE_MITIGATES='mitigates', 'mitigates'
    EDGE_DETECTS='detects', 'detects'




