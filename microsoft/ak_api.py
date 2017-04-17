'''Retrieval/handler for Microsoft Knowledge API

Usage:
  ak_api.py evaluate --year=<year>

Options:
  year:   year to retrieve publications for
'''

import time, os.path, ConfigParser
import requests, pymongo
from docopt import docopt
from doc_parse import DocParser

class AK_API:
    offset = 100000
    db_name = 'metric'
    collection_name = 'publications'
    
    def __init__(self):
        DocParser(__doc__).parse_doc(self)
    
    def mongo_connect(self):
        '''Connect to MongoDB
        '''
        print 'Connecting to MongoDB ...'
        self.client = pymongo.MongoClient()
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
        
        if(os.path.isfile('ak_api.cfg')):
            config = ConfigParser.SafeConfigParser()
            config.readfp(open('ak_api.cfg'))
            key = config.get('api', 'key')
        else:   
            key = raw_input('What is your API key? ')
            
        return key
        
    def get_author(self):
        '''Get author name for query
        Returns:
            (string) -- author name, lowercase
        '''
        author = raw_input('What is the name of the author to search for? ')
        return author.lower()
        
    def evaluate(self, year = 2011):
        '''Perform GET request to API "evaluate" command
        '''
        self.mongo_connect()
        key = self.get_credentials()       
        current_year = time.strftime("%Y")
        count = 0
        
        while(True):
            url = 'https://westus.api.cognitive.microsoft.com/academic/v1.0/evaluate?'
            
            data = {}
            data['expr'] = 'Y={year}'.format(year = year)
            data['attributes'] = 'Id,Ti,Y,CC,AA.AuN,AA.AuId,AA.AfN,F.FN,J.JN'
            data['count'] = self.offset
            data['offset'] = count * self.offset
            
            # add parameters to url
            for k, v in data.iteritems():
                url += k + '=' + str(v) + '&'
            
            headers = {
                'Ocp-Apim-Subscription-Key': key,
            }       
            
            print 'Getting items at {number} ...'.format(number = count * self.offset)
            r = requests.get(url, headers = headers)
            
            result = r.json()
            
            if('error' in result):
                print result['error']
                return
            
            self.add_pubs(result['entities'])
                
            count += 1
            
            if(len(result['entities']) < self.offset):
                return
            
        print 'Complete.'
        
    def add_pubs(self, pubs):
        '''Add publication data to MongoDB
        Args:
            pubs (dict) -- of publications, from json
        '''
        print 'Saving current result in MongoDB...'
        
        try:
            collection = self.db[self.collection_name].insert_many(pubs, ordered = False)
        except pymongo.errors.BulkWriteError:
            print 'Ignoring duplicate entries.'
        
if(__name__ == '__main__'):
    a = AK_API()
