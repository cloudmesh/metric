'''Retrieval/handler for Microsoft Knowledge API

Usage:
  ak_api.py evaluate <year> [--count=<count> --offset=<offset> --skip=<skip>]
  ak_api.py parents
  ak_api.py citations

Options:
  year:     year to retrieve publications for
  count:    number of entities to retrieve per call
  offset:   starting index
  skip:     number of entities to skip (skip * count)
'''

import time, re, os.path, ConfigParser
import requests, pymongo, numpy
from docopt import docopt
from doc_parse import DocParser

class AK_API:
    db_name = 'microsoft'
    collection_name = 'publications'
    
    def __init__(self):
        self.mongo_connect()
        DocParser(__doc__).parse_doc(self)
    
    def mongo_connect(self):
        '''Connect to MongoDB
        '''
        opts = {}
        opts['port'] = int(self.get_config_option('mongo', 'port'))
        
        print 'Connecting to MongoDB on port {port}...'.format(**opts)
        
        self.client = pymongo.MongoClient(**opts)
        self.db = self.client[self.db_name]
        
        # create index
        if(self.collection_name not in self.db.collection_names()):
            self.db[self.collection_name].create_index('Id', unique = True)

    def get_credentials(self):
        '''Get API key
        Returns:
            (string) -- API Key
        '''
        print 'Getting API key ...'
        
        key = self.get_config_option('api', 'key')

        if(not key):   
            key = raw_input('What is your API key? ')
            
        return key
        
    def get_config_option(self, section, option):
        '''Get configuration item
        Args:
            section (str): config section
            option (str): item in section
        Return:
            str: config item
        '''
        if(os.path.isfile('ak_api.cfg')):
            config = ConfigParser.SafeConfigParser()
            config.readfp(open('ak_api.cfg'))
            option = config.get(section, option)
            return option
        else:
            print 'Unable to locate configuration file.'
            return None
        
    def get_author(self):
        '''Get author name for query
        Returns:
            (string) -- author name, lowercase
        '''
        author = raw_input('What is the name of the author to search for? ')
        return author.lower()
        
    def evaluate(self, year, count = 100000, offset = 0, skip = 0):
        '''Perform GET request to API "evaluate" command
        '''
        offset = int(offset)
        count = int(count)
        key = self.get_credentials()       
        current_year = time.strftime("%Y")
        counter = int(skip)
        
        while(True):
            url = 'https://westus.api.cognitive.microsoft.com/academic/v1.0/evaluate?'
            
            data = {}
            data['expr'] = "Or(Y={year}, D='{year}'".format(year = year)
            data['attributes'] = 'Id,Ti,Y,L,D,CC,ECC,AA.AuN,AA.AuId,AA.AfN,AA.AfId,AA.S,F.FId,F.FN,J.JId,J.JN,C.Cid,C.CN,RId'
            data['count'] = count
            data['offset'] = counter * count
            data['orderby'] = 'Id:asc'
            
            # add parameters to url
            for k, v in data.iteritems():
                url += k + '=' + str(v) + '&'
            
            headers = {
                'Ocp-Apim-Subscription-Key': key,
            }       
            
            print 'Getting items from {start} to {finish} ...'.format(start = counter * count + 1, finish = (counter + 1) * count)
            r = requests.get(url, headers = headers)
            
            result = r.json()
            entities = [e for e in result['entities'] if e]
            
            print "{} results retrieved".format(len(entities))
            
            if('error' in result):
                print result['error']
                break
            
            if(len(entities) >= offset):
                self.add_pubs(result['entities'])
                counter += 1
            else:
                break
            
        print 'Complete.'
        
    def add_pubs(self, pubs):
        '''Add publication data to MongoDB
        Args:
            pubs (dict) -- of publications, from json
        '''
        print 'Saving current result in MongoDB...'
        
        try:
            self.db[self.collection_name].insert_many(pubs, ordered = False)
        except pymongo.errors.BulkWriteError:
            print 'Ignoring duplicate entries.'
            
    def citations(self):
        '''Get citation count by FOS
        '''
        print 'Retrieving citation count ...'  
        
        collection = self.db[self.collection_name]       
        result = collection.find({}, {'_id': 0, 'CC': 1, 'F.parent': 1})
        
        citations = {}
        
        for pub in result:
            if('CC' in pub and 'F' in pub):
                fields = []
                
                for f in pub['F']:
                    if('parent' in f):
                        parent = f['parent']
                        fields.append(parent)
                    
                fields = list(set(fields))
                
                for f in fields:
                    if f in citations:
                        citations[f].append(pub['CC'])
                    else:
                        citations[f] = [pub['CC']]
        
        print 'Computing averages ...'
        citations = {k: numpy.mean(v) for k, v in citations.iteritems()}
        
        print citations
        return citations
        
    def parents(self):
        '''Add field of study parents
        Warning:
            Microsoft has duplicate entries for any given field name, field names from FieldsOfStudy.txt do not match current field names retrieved from API
        '''
        print 'Adding parents to fields ...'
        
        records = self.db[self.collection_name].find()
        
        with open('FieldsOfStudy.txt') as f:
            fields = {}
            for row in f.readlines():
                fid, fname = row.split('\t')
                # replace em dash with minus
                fname = re.sub('\xe2\x80\x93', '-', fname)
                fields[fid] = fname.strip().lower()
            
            # reverse fields dict
            ids = dict(zip(fields.values(), fields.keys()))

        # cache tree
        with open('FieldOfStudyHierarchy.txt') as f:
            children = {}
            for row in f.readlines():
                ci, cl, pi, pl, p = row.split()
                
                if(pl == 'L0' and pi not in children):
                    children[pi] = {'parents': [], 'level': 'L0'}
                
                child = children.get(ci)
                if(child):
                    child['parents'].append({'id': pi, 'prob': float(p)})
                else:
                    children[ci] = {'parents': [{'id': pi, 'prob': float(p)}], 'level': cl}
                
        # build branches
        for child, branch in children.iteritems(): 
            for parent in branch['parents']:
                if(parent['id'] in children):
                    parent['pointer'] = children[parent['id']]
                    
            # remove parents with no pointer
            branch['parents'] = [p for p in branch['parents'] if 'pointer' in p]
        
        # get probabilities            
        def get_prob(parent, probs = []):
            '''recursive function for tree traversal through fields of study hierarchy
            '''
            for parent in parent['pointer']['parents']:
                new_prob = parent['prob'] * probs[-1][1] if probs else float(parent['prob'])
                probs.append((parent['id'], new_prob))
                get_prob(parent, probs)
                
            return probs
            
        parents = {}
        for child, branch in children.iteritems():
            # check if the "child" is a top-level parent
            if(children[child]['level'] == 'L0'):
                top = (child,)
            else:
                probs = []
                for parent in branch['parents']:
                    probs.extend(get_prob(parent, [(parent['id'], parent['prob'])]))
                
                # determine best probability
                top = (None, 0)
                for prob in probs:
                    pid, probability = prob
                    if(children[pid]['level'] == 'L0' and probability > top[1]):
                        top = prob
            
            parents[child] = fields.get(top[0])
                      
        print "Updating records ..."       
        bulk = self.db[self.collection_name].initialize_unordered_bulk_op()
        
        for record in records:            
            if('F' in record):
                for field in record['F']:
                    if('parent' not in field):
                        field_name = field['FN']                   
                        field_id = ids.get(field_name)
                                
                        if(field_id):
                            parent = parents.get(field_id)
                            if(parent):
                                field['parent'] = parent
                                         
                bulk.find({'_id': record['_id']}).update({'$set': {'F': record['F']}})
        
        print "Executing MongoDB bulk update ..."
        try:        
            bulk.execute()
        except pymongo.errors.BulkWriteError as err:
            print "Write error: " + err
            
        print 'Complete.'
        
if(__name__ == '__main__'):
    a = AK_API()
