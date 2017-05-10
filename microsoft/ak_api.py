'''Retrieval/handler for Microsoft Knowledge API

Usage:
  ak_api.py evaluate <year> [--offset=<offset>]
  ak_api.py parents
  ak_api.py citations

Options:
  year:   year to retrieve publications for
'''

import time, os.path, ConfigParser, csv
import requests, pymongo, numpy
from docopt import docopt
from doc_parse import DocParser

class AK_API:
    db_name = 'metric'
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
        
    def evaluate(self, year, offset = 100000):
        '''Perform GET request to API "evaluate" command
        '''
        offset = int(offset)
        key = self.get_credentials()       
        current_year = time.strftime("%Y")
        count = 0
        
        while(True):
            url = 'https://westus.api.cognitive.microsoft.com/academic/v1.0/evaluate?'
            
            data = {}
            data['expr'] = 'Y={year}'.format(year = year)
            data['attributes'] = 'Id,Ti,Y,L,D,CC,ECC,AA.AuN,AA.AuId,AA.AfN,AA.AfId,AA.S,F.FId,F.FN,J.JId,J.JN,C.Cid,C.CN,RId'
            data['count'] = offset
            data['offset'] = count * offset
            
            # add parameters to url
            for k, v in data.iteritems():
                url += k + '=' + str(v) + '&'
            
            headers = {
                'Ocp-Apim-Subscription-Key': key,
            }       
            
            print 'Getting items from {start} to {finish} ...'.format(start = count * offset + 1, finish = (count + 1) * offset)
            r = requests.get(url, headers = headers)
            
            result = r.json()
            
            if('error' in result):
                print result['error']
                return
            
            self.add_pubs(result['entities'])
                
            count += 1
            
            if(len(result['entities']) < offset):
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
            reader = csv.DictReader(f, delimiter='\t')
            fields = {f['id']: f['name'].lower() for f in reader}
            ids = dict(zip(fields.values(), fields.keys()))
        
        with open('FieldOfStudyHierarchy.txt') as f:
            reader = csv.DictReader(f, delimiter='\t')
            
            parents = {}
            children = {}
            
            for row in reader:
                parent_id = row['parent_id']
                if(row['parent_level'] == 'L0' and parent_id not in parents):
                    parents[parent_id] = parent_id
                    children[parent_id] = {'level': 'L0'}
          
                child = children.get(row['child_id'])
                if(child):
                    child['parents'][row['parent_id']] = row['prob']
                else:
                    children[row['child_id']] = {'parents': {row['parent_id']: row['prob']}, 'level': row['child_level']}
                    
                    
            def get_prob(parent, prob, level = 1):
                c_parents = children[parent].get('parents')
                if(not c_parents):
                    print prob
                    return prob
                for c_parent, c_prob in c_parents.items():
                    get_prob(c_parent, float(c_prob) * float(prob), level + 1)

            for child, info in children.iteritems():
                if('parents' in info):
                    for parent, prob in info['parents'].items():
                        print get_prob(parent, prob)
                    exit()
                        
            '''parents = {}
            for row in reader:
                child = parents.get(row['child_id']) or {}
                
                if(child):
                    if(row['parent_level'] == 'L0' and row['prob'] > child['prob']):
                        child['parent_id'] = row['parent_id']
                        child['level'] = row['parent_level']
                        child['prob'] = row['prob']
                else:
                    if(row['parent_level'] == 'L0'):
                        child['parent_id'] = row['parent_id']
                        child['level'] = row['parent_level']
                        child['prob'] = row['prob']
                        parents[row['child_id']] = child'''
                        
            
                        
                # if not child: try again with one of its parents
            
        for record in records:
            if('F' in record):
                for field in record['F']:
                    field_name = field['FN']                            
                    field_id = ids.get(field_name)
                            
                    if(field_id):
                        parent = parents.get(field_id)
                        if(parent):
                            field['parent'] = fields.get(parent)
                            
                self.db[self.collection_name].update(
                    {'_id': record['_id']},
                    {'$set': {'F': record['F']}}
                )
                                         
        return records
        
if(__name__ == '__main__'):
    a = AK_API()
