# -*- coding: utf-8 -*-
"""
Created on Tue Dec 13 06:49:51 2016
@author: V.Diakov
CLASS: KRe - keywords relations analysis. Assumes JSON keywords relate as a directional (acyclic) graph
             with a few keyword exceptions, this is a tree graph; the exceptions are treated.
METHODS:
- build_flat_map: creates (recursively) a list of key sequences ('list_map') and the corresponding list of values from a parsed json entry ('event')
- flat_dictionary: creates (or adds-on) a keywords list ('keywords') and the corresponding keyword hash ('keyword_hash') # and keyword-sequence hash ('flat_hash') from 'list_map' (a.k.a. 'flat_map')
- build_dictionaries: builds-on keyword dictionary and hash from a list of json entries ('parsed_events')
- related_paths: finds keyword sequences associated with a keyword
- retrieve_data: scans JSON data and retrieves data associated with given paths (i.e. keyword sequences)
                 the retrieved data are delivered as JSON strings with a header showing the search paths
                 the conversion of data to numeric values is controlled by the 'to_numeric' parameter
APPROACH: As mentioned, the raw data show that keywords are related as a tree graph (e.g. A1->A2,B2, A2->A3,B3, B2->C3,D3 ; the digits represent the layer number, the letters - nodes within a layer, the arrows - relations between nodes)
          Some exceptions, though, exist. Different branches get 'entangled' when one node belongs to different branches (e.g. A2->C3->B4, B2->C3->D4 : C3 belongs to both A2->*->B4 and B2->*->D4 paths, with no A2->*->D4 nor B2->*->B4 being allowed)
          This makes keyword relations not quite a graph, but a 'graph with memory' or a higher order network.
          Here, along with a graph-describing relational matrix 'g' that has information about nearest neighbors only,
          an association rules matrix 'm' is also employed that compiles paths (keyword sequences) information.
          Both matrices are computed by the keywords_relational_matrix method and employed to gather the paths associated with a given keyword
"""

import numpy as np

def if_float(a): # if the string represents a number, make it float
    try:               res = float(a)
    except ValueError: res = a
    return res
def build_flat_map(arr,list_map=[], ndcs=[], leafs=[]): # build a flat map of a structure (e.g. json object)
    if (type(arr) == list) | (type(arr) == dict) | (type(arr) == np.ndarray):
        span = range(len(arr)); 
        if type(arr) == dict: span = arr.keys() ;
        for i in span: list_map, ndcs, leafs = build_flat_map(arr[i], list_map, ndcs+[i], leafs)#
        ndcs=ndcs[:-1]
    else: list_map.append(ndcs) ; ndcs = ndcs[:-1] ; leafs += [arr]#; disp("build_flat_map: appended %r" % flat_map[-1])
    return list_map, ndcs, leafs
def nonzero_ndx(arr):
    try: ndx = arr.index(1)
    except ValueError: ndx = None #
    return ndx
def collect_nonzeros(arr): 
    ndcs=[]; ndx1=0; s=list(np.sign(arr)); 
    ndx=nonzero_ndx(s) ; 
    while ndx >= 0 : 
        ndcs.append(ndx + ndx1); ndx1 += ndx+1; 
        if ndx1 <= len(s)-1: ndx = nonzero_ndx(s[(ndx1):]) #
        else : ndx = None #
    return ndcs
def replace_ndcs(list_map): # replace json array indices (integers) with 'anArrayIndex'
    changes_made = [('list_map ndx','keyset ndx','ndx value')]
    for j in range(len(list_map)):
        for i in range(len(list_map[j])):
            if type(list_map[j][i])==int: 
                changes_made.append((j,i,list_map[j][i])) ; list_map[j][i]='anArrayIndex' ; 
    return changes_made
def json_string(name,names,values): # make a json string from lists of corresponding names and values
    s='{"'+str(name)+'":{'
    for i in range(len(names)): s += '"'+str(names[i])+'":"'+str(values[i])+'", ' #
    s = s[:-2] + '}}\n'
    return s

class KRe(object): # keywords relations
    def __init__(self):
        self.keywords = []   # the set of keywords used in JSON data
        self.keyword_hash = {}
        self.m = np.zeros(1) # matrix m[j,i] (directional) association rules: shows how many times j-th keyword precedes the i-th keyword
        self.g = np.zeros(1) # matrix g[j,i] shows if j-th keyword immediately precedes the i-th keyword
    def build_dictionaries(self, parsed_events):
        for event in parsed_events: # from each event, add-on new keywords [sequences] to dictionaries
            flat_map, ndcs, leafs = build_flat_map(event)
            self.flat_dictionary(flat_map)
        self.keyword_hash['anArrayIndex']=len(self.keywords) ; self.keywords.append('anArrayIndex') # the last keyword
    def flat_dictionary(self, flat_map): # build dictionary from flat_map keys as keys' sequence separated by ':'
        for keyset in flat_map: 
            for key in keyset: # scan keywords from keyset
                if (type(key) == str)|(type(key)==unicode): 
                    word=str(key) # add 'key'+':' to 'nam'
                    if self.keywords.count(word)==0: # add a new word to keywords
                        self.keyword_hash[word]=len(self.keywords) ; self.keywords.append(word) ; 
    def keywords_relational_matrix(self, parsed_events): # build the association rules matrices m and g
        n=len(self.keywords); self.m=np.zeros(n*n).reshape(n,n); self.g=np.int_(self.m) # initialize relational matrices m and g
        for event in parsed_events:
            flat_map, ndcs, leafs = build_flat_map(event); replace_ndcs(flat_map)
            for keyset in flat_map:
                for i in range(1,len(keyset)):
                    self.g[self.keyword_hash[str(keyset[i-1])], self.keyword_hash[str(keyset[i])]] = 1
                    for j in range(i): self.m[self.keyword_hash[str(keyset[j])], self.keyword_hash[str(keyset[i])]] += 1 #
    def key_ndx(self, word):
        try: res = self.keyword_hash[word]
        except KeyError: res = None
        return res
    def find_parents(self, word): # find keywords parental to the given word
        n=self.key_ndx(word); seniority = []
        if n>=0: 
            parents = self.find_ancestry(n) #
            seniority = self.sort_ancestry(parents)
        return seniority
    def find_ancestry(self, ndx): return collect_nonzeros(self.m[:,ndx])
    def find_descendants(self, ndx): return collect_nonzeros(self.m[ndx,:])
    def sort_ancestry(self, parents): 
        if len(parents)>1: # sort ancestry if more than one parent
            nrps = [] # number of related parents (list)
            for parent in parents:
                pts = self.find_ancestry(parent)
                xtr_ancstry = list(set(pts)-set(parents))# in case kwd is used in un-related trees
                nrps.append(len(pts)-len(xtr_ancstry))
        a=np.array(parents) ; s=np.argsort(nrps) ; seniority = list(a[s])
        return seniority # list of parents, sorted by seniority
    def list_branches(self, path, branches): # build branches as a list of allowable paths
        kids = self.immediate_descendants(path)
        if kids == []: branches += [path] # other restrictions on branches can go in this 'if' statement
        else: 
            for kid in kids: self.list_branches(path+[kid], branches) #
    def immediate_descendants(self, path): # some keywords (e.g. 'attributes') are used in several trees
        kids = collect_nonzeros(self.g[path[-1],:]); related = []
        for kid in kids: 
            pts = self.find_ancestry(kid)
            if len(list(set(path)-set(pts)))==0: related.append(kid) # include descendants related with current path
        return related
    def related_paths(self, word): # for keyword index 'word', find related paths for json data querying
        if type(word) == str: word = self.keyword_hash[word] #
        parents = self.sort_ancestry( self.find_ancestry(word) )
        branches=[] ; self.list_branches( parents+[word], branches )
        return branches
    def get_value(self, path, event, to_numeric=False): # a recursive get_value from paths - arbitrary lists - is needed here
        a = event
        for ndx in path: 
            keyword = self.keywords[ndx]
            if keyword=='anArrayIndex': keyword=0 # a band-aid patch, real arrays/lists needed here
            a = a[keyword]
        if to_numeric: a = if_float(a) #
        return a
    def path_to_string(self, path): 
        s=''
        for ndx in path: s += self.keywords[ndx]+'/'
        return s[:-1]
    def paths_to_string(self, paths, res = []):
        for path in paths: res.append( self.path_to_string(path) ) #
        return res
    def retrieve_data(self, parsed_events, paths, to_numeric=False): # retrieve data following specified json paths into json formats
        header = json_string("header", list(range(len(paths))), self.paths_to_string(paths, []))
        retrieved = [header] + [ [self.get_value(path, event, to_numeric) for path in paths] for event in parsed_events]
        return retrieved
    def get_keywords(self): return self.keywords #
    def get_keyword_hash(self): return self.keyword_hash #
    def get_m(self): return self.m #
    def get_g(self): return self.g #
    def set_keywords(self, keywords): self.keywords = keywords #
    def set_keyword_hash(self, keyword_hash): self.keyword_hash = keyword_hash #
    def set_m(self, m): self.m = m #
    def set_g(self, g): self.g = g #
