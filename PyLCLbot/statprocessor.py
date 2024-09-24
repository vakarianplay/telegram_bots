import csv
import logging
import random
import time

class StatisticCSV:
    def __init__(self, filename='/home/kias-x/PyLCLbot/statistic.csv'):
        self.filename = filename
        logging.info("load statistic file")
        
    def statRec(self, winner, loser):
        with open(self.filename, 'r', newline='') as file:
            reader = csv.reader(file)
            data = list(reader)

        participants = [winner, loser]
        for participant in participants:
            found = False
            for row in data:
                if row[0] == participant:
                    if participant == winner:
                        row[1] = str(int(row[1]) + 1)  
                    else:
                        row[2] = str(int(row[2]) + 1)  
                    found = True
                    break
            if not found:
                if participant == winner:
                    data.append([participant, '1', '0'])  
                else:
                    data.append([participant, '0', '1'])
        
        with open(self.filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(data)
            
        logging.info("Add record" + str(data))
        
    def getStatUser(self, username):
        with open(self.filename, 'r', newline='') as file:
            reader = csv.reader(file)
            for row in reader:
                if row[0] == username:
                    return str(row[1]), str(row[2])
                #make else return
            return None
    
if __name__ == "__main__":
    print ("it is class")
