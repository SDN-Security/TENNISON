import json
from pprint import pprint
import matplotlib.pyplot as plt


with open('flows.json') as data_file:
    data = json.load(data_file)

pprint(data)

for i in data:
    # Check if greater than 2 or insert a bigger more reasonable value
    if(len(i['values']['delta_bps_records'])>=2):
        plt.plot(i['values']['delta_bps_records'])
        plt.ylabel('delta_bps')
        # plt.xlabel( )
        plt.title('sourceIPv4Address: ' + str(i['values']['sourceIPv4Address']) +' -> '+ 'sourceTransportPort: ' + str(i['values']['sourceTransportPort']) +'\n'+
                  'destinationIPv4Address: ' + str(i['values']['destinationIPv4Address']) +' -> '+ 'destinationTransportPort: ' + str(i['values']['destinationTransportPort']) )
        plt.show()