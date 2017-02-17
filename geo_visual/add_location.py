import csv

class AddLocation:
    biblio_file = 'data.csv'
    stats_file = 'hd2015.csv'
    
    def __init__(self):
        self.get_stats()
        self.add_location()
        
    def get_stats(self):
        '''create list of dicts of stats from National Center for Education Statistics
        '''
        print 'Getting statistics data ...'
        self.stats_rows = []
        with open(self.stats_file, 'rb') as s:
            stats_rows = csv.DictReader(s)
            
            for row in stats_rows:
                self.stats_rows.append(row)

    def add_location(self):
        '''Add location data to biblio data
        '''
        print 'Updating bibliography data ...'
        with open(self.biblio_file, 'rb') as b:
            biblio_rows = csv.DictReader(b)
            
            new_csv = []
            update = 0
            fields = []
            for row in biblio_rows:
                match = self.find_match(row['Organization'])
                
                if(match):
                    update += 1
                    row['location_street'] = match['ADDR']
                    row['location_city'] = match['CITY']
                    row['location_state'] = match['STABBR']
                    row['location_zip'] = match['ZIP']
                    row['location_longitude'] = match['LONGITUD']
                    row['location_latitude'] = match['LATITUDE']
                    
                    if(len(fields) < row.keys()):
                        fields = row.keys()
   
                new_csv.append(row)
                
            print 'Updated ' + str(update) + ' rows, saving data-coords.csv ...'
                
            with open('data-coords.csv', 'wb') as c:
                dict_writer = csv.DictWriter(c, fieldnames = fields)
                dict_writer.writeheader()
                dict_writer.writerows(new_csv)
                
            print 'Complete.'
            
    def find_match(self, org):
        '''Check whether organizations name match, disregarding punctuation and word order
        Args:
            org (string) -- organization name
        Returns:
            (dict) -- matching organization details
        '''
        
        replace  = {',': '', ' of ': ' ', ' at ': ' ', '-': ' ', 'Main Campus': '', ' and ': ' ', ' in ': ' ', '.': '', ' the ': ' ', 'The ': '', ' for ': ' ', ' & ': '', '&': ''}
        
        ignore = ['state', 'university', 'school', 'medicine', 'science', 'technology', 'college', 'medical', 'institute', 'research', 'health', 'system', 'office', 'national', 'sciences', 'center', 'campus', 'city']
        
        org_name = org
        for k, v in replace.iteritems():
            org_name = org_name.replace(k, v)
            
        org_list = org_name.lower().strip().split()
        
        matches = []
        for row in self.stats_rows: 
            stat_org = row['INSTNM']
            
            if(org == stat_org):
                return row
            
            for k, v in replace.iteritems():
                stat_org = stat_org.replace(k, v)
            
            stat_list = stat_org.lower().strip().split()
            
            if(org_name == stat_org or set(org_list) == set(stat_list)):
                return row
            
            match_words = []
            for word in org_list:
                if(word in stat_list):
                    match_words.append(word)
                  
            if(len(match_words) >= 2):
                for word in match_words:
                    if word not in ignore:
                        matches.append(row)
                        break
                             
        if(len(matches) == 1):
            return matches[0]
        elif(len(matches) > 1):
            matches = sorted(matches, key = lambda k: k['INSTNM'])
            print
            print 'Organization: ' + org
            count = 0
            for match in matches:
                print str(count) + ') ' + match['INSTNM']
                count += 1
            
            selection = raw_input('Select the matching organization or None: ')
            selection = int(selection) if selection else -1
            
            if(0 <= selection < len(matches)):
                return matches[selection]
            else:
                return {}
        else:
            return {}
        
AddLocation()       
