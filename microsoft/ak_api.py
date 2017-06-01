'''Retrieval/handler for Microsoft Knowledge API

Usage:
  ak_api.py evaluate <year> [--count=<count> --start=<start>]
  ak_api.py extended <year> [--count=<count> --start=<start>]
  ak_api.py january <year> [--count=<count>]
  ak_api.py compare [--count=<count>]
  ak_api.py parents
  ak_api.py citations

Options:
  year:     year to retrieve publications for
  count:    number of entities to retrieve per call
  start:    month to begin on
'''

import time, json, re, calendar, string, os.path, ConfigParser
import requests, pymongo, numpy
from docopt import docopt
from doc_parse import DocParser

class AK_API:
    db_name = 'microsoft'
    
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
        
        # create indexes
        if('publications' not in self.db.collection_names()):
            self.db.publications.create_index('Id', unique = True)
            
        if('extended' not in self.db.collection_names()):
            self.db.extended.create_index('Id', unique = True)
            
        if('fields' not in self.db.collection_names()):
            self.db.fields.create_index('Id', unique = True)

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
        
    def evaluate(self, year, count = 100000, start = 0):
        '''Perform GET request to API "evaluate" command
        Args:
            year (str) -- year to update
            count (int) -- results per call
            start (int) -- month to start on (0 being January)
        '''
        count = int(count)
        key = self.get_credentials()
        attributes = 'Id,Ti,L,Y,D,CC,ECC,AA.AuN,AA.AuId,AA.AfN,AA.AfId,AA.S,F.FId,F.FN,J.JId,J.JN,C.CId,C.CN,RId'
        
        for m in xrange(int(start), 12):
            date = {}
            date['year'] = year
            date['month'] = str(m + 1) if m > 8 else '0' + str(m + 1)
            date['day'] = calendar.monthrange(int(year), m + 1)[1]
            print "Getting results for {year}-{month} ...".format(**date)
            expr = "D=['{year}-{month}-01','{year}-{month}-{day}']".format(**date)         
            self.retrieve_pubs(year, count, key, attributes, self.add_pubs, expr = expr)
        
    def extended(self, year, count = 100000, start = 0):
        '''Get extended metadata
        Args:
            year (str) -- year to update
            count (int) -- results per call
            start (int) -- month to start on (0 being January)
        '''
        count = int(count)
        key = self.get_credentials()
        
        for m in xrange(int(start), 12):
            date = {}
            date['year'] = year
            date['month'] = str(m + 1) if m > 8 else '0' + str(m + 1)
            date['day'] = calendar.monthrange(int(year), m + 1)[1]
            expr = "D=['{year}-{month}-01','{year}-{month}-{day}']".format(**date)
            print "Getting results for {year}-{month} ...".format(**date)            
            self.retrieve_pubs(year, count, key, 'E', self.add_extended, expr = expr)
            
    def january(self, year, count = 100000):
        '''Get publications for January of given year, by title
        Args:
            year (str) -- year to retrieve
            count (int) -- number of results per call
        '''
        count = int(count)
        key = self.get_credentials()
        attributes = 'Id,Ti,L,Y,D,CC,ECC,AA.AuN,AA.AuId,AA.AfN,AA.AfId,AA.S,F.FId,F.FN,J.JId,J.JN,C.CId,C.CN,RId'
        
        for l in string.lowercase:
            print "Retrieve January publications for {year} starting with {letter} ...".format(letter = l, year = year)
            expr = "And(Ti='{letter}'...,D=['{year}-01-01','{year}-01-31'])".format(letter = l, year = year)
            self.retrieve_pubs(year, count, key, attributes, self.add_pubs, expr = expr)
            
    def compare(self, count = 100):
        print "Matching records ..."
        
        import time
        
        start = time.time()
        
        with open('pubs_xup.txt') as f:       
            ids = []
            counter = 0
            for row in f.readlines():
                if('|' not in row):
                    continue
                    
                pid, title = row.strip().split('|', 1)
                
                
                title = title.lower().decode('ISO-8859-1').encode('utf-8')
                title = title.replace('-', ' ')
                title = title.replace('/', ' ')
                title = title.replace('+', ' ')
                title = title.translate(None, string.punctuation)
                
                
                record = self.dd.publications.find_one({'Ti': title})
                
                '''# match without first word
                if(not record):
                    title = title.split(' ', 1)[1] if ' ' in title else title
                    record = self.db.publications.find_one({'Ti': title})'''
                
                if(record):
                    ids.append(str(pid) + '|' + str(record['Id']) + '\n')
                
                counter += 1
                
                if(counter >= int(count)):
                    break
                    
        print "Accuracy: " + str(float(len(ids))/int(counter))
                
        print "Time elapsed for {} items with {} matches: {}".format(counter, len(ids), time.time()-start)
        print "Amount of time per match: {} seconds".format(str((time.time()-start) / int(counter)))
        
        print "Saving file ..."
        
        with open('xsede_ms.txt', 'w+') as f:
            f.writelines(ids)
        
        print "Complete."
        
    def retrieve_pubs(self, year, count, key, attributes, hook, expr = ''):
        '''Get publications from via API
        Args:
            year (str) -- year
            attributes (str) -- paper entity attributes to retrieve
            start (int) -- month to start on
            callback (function) -- function to handle results 
        '''
        offset = 0
        data = {}
        data['expr'] = expr
        data['attributes'] = attributes
        data['count'] = count
    
        while(True):
            data['offset'] = offset
            
            # add parameters to url
            url = 'https://westus.api.cognitive.microsoft.com/academic/v1.0/evaluate?'
            for k, v in data.iteritems():
                url += k + '=' + str(v) + '&'
            
            headers = {
                'Ocp-Apim-Subscription-Key': key,
            }       
            
            print "Getting items from {} to {} ...".format(offset + 1, offset + count)
            
            try:
                r = requests.get(url, headers = headers)              
            except requests.exceptions.ChunkedEncodingError:
                print "Connection reset. Trying again ..."
                continue
            
            result = r.json()

            if('error' in result):
                print result['error']
                return
                
            if(r.status_code == 500):
                print "Server error. Exiting."
                return
            
            entities = [e for e in result['entities'] if e]
            
            print "{} results retrieved".format(len(entities))
            
            if(len(entities)):
                hook(entities)
                offset += count
                
                if(len(entities) < count):
                    break
            else:
                break
        
    def add_pubs(self, pubs):
        '''Add publication data to MongoDB
        Args:
            pubs (dict) -- of publications, from json
        '''
        print 'Saving current result in MongoDB...'
        
        try:
            self.db.publications.insert_many(pubs, ordered = False)
        except pymongo.errors.BulkWriteError:
            print 'Ignoring duplicate entries.'
            
    def add_extended(self, pubs):
        '''Add extended metadata to MongoDB
        Args:
            pubs (dict) -- of publications, from json
        '''
        print 'Saving current result in MongoDB...'
        
        try:
            self.db.extended.insert_many(pubs, ordered = False)
        except pymongo.errors.BulkWriteError:
            print 'Ignoring duplicate entries.'
            
    def citations(self):
        '''Get citation count by FOS
        '''
        print 'Retrieving citation count ...'  
        
        collection = self.db.publications      
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
        print 'Getting parent fields ...'
        
        records = self.db.publications.find()
        
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
                      
        print "Adding parents to records ..."       
        bulk = self.db.fields.initialize_unordered_bulk_op()
        
        for record in records:            
            if('F' in record):
                top_fields = []
                for field in record['F']:
                    field_name = field['FN']                   
                    field_id = ids.get(field_name)
                            
                    if(field_id):
                        parent = parents.get(field_id)
                        if(parent and parent not in top_fields):
                            top_fields.append(parent)
                                         
                bulk.insert({'Id': record['Id'], 'fields': top_fields})
        
        print "Executing MongoDB bulk insert ..."
        try:
            bulk.execute()
        except pymongo.errors.BulkWriteError:
            print "Ignoring Duplicates."
            
        print 'Complete.'
        
if(__name__ == '__main__'):
    a = AK_API()
