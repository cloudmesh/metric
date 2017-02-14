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
            for b_row in biblio_rows:
                for s_row in self.stats_rows:
                    if(self.match_orgs(s_row['INSTNM'], b_row['Organization'])):
                        update += 1
                        b_row['location_street'] = s_row['ADDR']
                        b_row['location_city'] = s_row['CITY']
                        b_row['location_state'] = s_row['STABBR']
                        b_row['location_zip'] = s_row['ZIP']
                        b_row['location_longitude'] = s_row['LONGITUD']
                        b_row['location_latitude'] = s_row['LATITUDE']
                        
                        if(len(fields) < b_row.keys()):
                            fields = b_row.keys()
                            
                        break
                new_csv.append(b_row)
                
            print 'Updated ' + str(update) + ' rows, saving data-coords.csv ...'
                
            with open('data-coords.csv', 'wb') as c:
                dict_writer = csv.DictWriter(c, fieldnames = fields)
                dict_writer.writeheader()
                dict_writer.writerows(new_csv)
                
            print 'Complete.'
            
    def match_orgs(self, a, b):
        '''Check whether organizations name match, disregarding punctuation and word order
        Args:
            a (string) -- first org
            b (string) -- second org
        Returns:
            (bool) -- whether or not they match
        '''
        replace  = {',': '', 'of': '', '&': '', '-': ' '}
        
        for k, v in replace.iteritems():
            a = a.replace(k, v)
            b = b.replace(k, v)
        
        a_list = a.lower().split()
        b_list = b.lower().split()
        
        return set(a_list) == set(b_list)
        
AddLocation()       
