import gmodel as gm 

class Node(object):
    # Constructor
    def __init__(self, id, name, desc):
        self.name = name
        self.id = id
        self.desc = desc
        self.mtype = gm.NodeType.ATTACK_BASE.code

    # To get feature tuple

    def getFeatureData(self):
        return (self.id, self.name, self.desc)

    def getCode(self):
        return (self.mtype)

    @staticmethod
    def getFeatureHeader():
        return ('id', 'name', 'desc')
  
    # To check the Mitre-Att&ck type
    def isOfType(self, mtype):
        return self.mtype == mtype 

class Technique(Node):
    def __init__(self, id, name, desc):
        super(Technique, self).__init__(id, name, desc)
        self.mtype = gm.NodeType.NODE_ATTACK_PATTERN.code
    pass

class ObservedFact(Node):
    def __init__(self, id, name, desc):
        super(ObservedFact, self).__init__(id, name, desc)
        self.mtype = gm.NodeType.NODE_DATA_COMPONENT.code
    pass

class Asset(Node):
    def __init__(self, id, name, desc):
        super(Asset, self).__init__(id, name, desc)
        self.mtype = gm.NodeType.NODE_DATA_SOURCE.code
    pass

class Recommendation(Node):
    def __init__(self, id, name, desc):
        super(Recommendation, self).__init__(id, name, desc)
        self.mtype = gm.NodeType.NODE_COURSE_OF_ACTION.code
    pass

class Malware(Node):
    def __init__(self, id, name, desc):
        super(Malware, self).__init__(id, name, desc)
        self.mtype = gm.NodeType.NODE_MALWARE.code
    pass

class Tool(Node):
    def __init__(self, id, name, desc):
        super(Tool, self).__init__(id, name, desc)
        self.mtype = gm.NodeType.NODE_TOOL.code
    pass

class IntrusionGroup(Node):
    def __init__(self, id, name, desc):
        super(IntrusionGroup, self).__init__(id, name, desc)
        self.mtype = gm.NodeType.NODE_INTRUSION_SET.code
    pass


  
class Edge(object):
    # Constructor
    def __init__(self, id, src_id, trg_id):
        self.id = id
        self.source_id = src_id
        self.target_id = trg_id
        self.mtype = gm.EdgeType.ATTACK_BASE.code

    # To get feature tuple
    def getFeatureData(self):
        return (self.id, self.source_id,self.target_id)

    @staticmethod
    def getFeatureHeader():
        return ('id', 'source_id', 'target_id')
  
    # To check the Mitre-Att&ck type
    def isOfType(self, mtype):
        return self.mtype == mtype 
  
  
class Uses(Edge):
    def __init__(self, id, src_id, trg_id):
        super(Uses, self).__init__(id, src_id, trg_id)
        self.mtype = gm.EdgeType.EDGE_USES.code
    pass

class IsSubtechniqueOf(Edge):
    def __init__(self, id, src_id, trg_id):
        super(IsSubtechniqueOf, self).__init__(id, src_id, trg_id)
        self.mtype = gm.EdgeType.EDGE_SUBTECHNIQUE_OF.code
    pass

class RelatesTo(Edge):
    def __init__(self, id, src_id, trg_id):
        super(RelatesTo, self).__init__(id, src_id, trg_id)
        self.mtype = gm.EdgeType.EDGE_RELATES_TO.code
    pass

class Mitigates(Edge):
    def __init__(self, id, src_id, trg_id):
        super(Mitigates, self).__init__(id, src_id, trg_id)
        self.mtype = gm.EdgeType.EDGE_MITIGATES.code
    pass

class Detects(Edge):
    def __init__(self, id, src_id, trg_id):
        super(Detects, self).__init__(id, src_id, trg_id)
        self.mtype = gm.EdgeType.EDGE_DETECTS.code
    pass


class Graph(object):
    # Constructor
    def __init__(self, name, nodes, edges):
        self.name = name
        self.edges = edges
        self.nodes = nodes

    # To get feature tuple
    def getNodes(self):
        return self.nodes

    def getEdges(self):
        return self.edges

    
