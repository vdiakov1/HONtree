# command line "python json8_d3.py >> json8_D3.log"  #-*- coding: utf-8 -*-
"""
Created on Fri Dec 09 12:45:33 2016 in response to a test assignment from Mickey Shoughnessy[mickey@appthis.com]
@author: V.Diakov
This is an example of using the keywords-relation class KRe
Lines 24-38 contain the code that parses JSON data to build the decoder 'jd' (takes ~30min to run)
Lines 41-51 (commented out) load a decoder that has been created by a previous run
Lines 58-62 create paths (i.e. keyword sequences) associated with 2 arbitrary keywords
Lines 64-71 retrieve the information associated with the 2 keywords and saves it on hard drive in 'xtract_from_json_D'
"""
import json
import pickle
import keywords_relation as KR

# read data
filename = '33-55-080313.dat'
f=open(filename,"r") ; string = f.read() ; f.close()
events = string.split('\n') ; events = events[:-1]; string = '' # skip the last (empty) row; clear string from memory
parsed_events = [json.loads(event) for event in events] ; events = [] # parse events ; clear events from memory

jd = KR.KRe() # kreate keywords-relation object
"""
#first pass (+ saving dictionaries and relational matrices):
print('Building dictionaries...')
jd.build_dictionaries(parsed_events)
print('                        ...done!')
print('                                Saving results...')
c_f=open('keywords_D.pickle','wb'); pickle.dump(jd.get_keywords(),c_f); c_f.close()
c_f=open('keyword_hash_D.pickle','wb'); pickle.dump(jd.get_keyword_hash(),c_f); c_f.close()
print('                                                 ...done!')

print('Building relational matrix...')
jd.keywords_relational_matrix(parsed_events)
print('                             ...done!')
print('                                     Saving results...')
c_f=open('relational_matrix_D.pickle','wb'); pickle.dump(jd.get_m(),c_f); c_f.close()
c_f=open('relational_g_matrix_D.pickle','wb'); pickle.dump(jd.get_g(),c_f); c_f.close()
print('                                                       ...done!')
m = jd.get_m()
"""
# load the first-pass results:
print('loading the first-pass results...')
c_f = open('keywords_D.pickle','rb'); keywords=pickle.load(c_f); c_f.close()
c_f = open('keyword_hash_D.pickle','rb'); keyword_hash=pickle.load(c_f); c_f.close()
c_f = open('relational_matrix_D.pickle','rb'); m=pickle.load(c_f); c_f.close()
c_f = open('relational_g_matrix_D.pickle','rb'); g=pickle.load(c_f); c_f.close()
print('                                  ...done!')
jd.set_keyword_hash(keyword_hash)
jd.set_keywords(keywords)
jd.set_m(m)
jd.set_g(g)

print('Check keyword hierarchy in the json data:')
print("  the product of the relational matrix 'm*m.T' should be zero,")
x=sum(sum(abs(m*m.T))); print('  the actual computed value sum(sum(abs(m*m.T)))=%r' %x)
if x==0: print('    => keywords are related as a directed graph.') #

paths = [] ; words = ['language', 'publisherForceToStore']
for word in words: paths += jd.related_paths(word) #
print('%r' %paths)
print(jd.paths_to_string(paths))

print('retrieving events info...')
to_numeric = True
retrieved = jd.retrieve_data(parsed_events, paths, to_numeric)
print('                         ...done!')
c_f = open('xtract_from_json_D3','w')
for line in retrieved: c_f.write(line) #
c_f.close()
