
# IPFix Monitor Interface

### Main files
###### Javascript polling & chart file : js/pollingbck.js
###### Configuration file : js/ipfixConfig.js (contains app-name, ports..etc. Can be utilised more)
###### Home Page : ipfix-flows.html


Go to http://127.0.0.1:8080/ to see the GUI



Use the disable graphs flag to stop graphs from loading (currently this is required as a bug in the graphs halts the system).
`http://127.0.0.1:8080/?disable_graphs=true`

#### Configuration:

Go to ipfixConfig.json to configure the ip address of the machine running TENNISON before starting the GUI.


#### Procedure:

1. The system registers the APP name, and makes the first call for the existing thresholds to render the chart and information DIV elements.
2. Once the DIV elements scaffolding is in place, the system polls for 
Threshold information from the NBI
IPFix information from the NBI
3. Once the information has arrived the system loops through the IPFix records to check if the record matches ALL fields of any thresholds in the threshold information given
For each FULL fields match ascertained there is a further check to see if the IPfix record has been plotted already, and to ascertain a consistent source of information (ONLY accept IPFix records from one switch)
4. The system then takes the most recent stored information from the last plot to calculate the period's throughput (currentOctetCount-previousOctetCount)/(currentRecordTime-previousRecordTime)
5. Once this has been ascertained the flow information is stored in an array which keeps historical ipfix octetCount and flowEndMilliSecond time (or another timeframe depending on the ipfix subtype).
6. Depending on what record subtype it is (ipfix,prefix,interfix) the system will put the data needed in the array for plotting data.
- For a prefix record, the system plots 2 points : the flowStart time with 0 throughput as the first record, and the flowEnd time with the calculated throughput. This is so that the chart is seen staring from zero on the chart at the time of the flow starting.
- For an interfix record it plots just one point, which has the current flowEnd time with the calculated throughput.
- For an ipfix record, it plots 2 points : The current flowEnd time with the calculated throughput, and the CURRENT TIME with 0 throughput. This shows as the end of the flow on the chart.
7. At the same time the current threshold value is collected and put into a array which will be fed to the same chart for the corresponding ipfix records to be plotted.
8. The chart for the threshold being looped is then plotted and the the process (from point 3. ) is repeated until all records have been checked.

The colours are selected randomly using a random colour generator, but the colour for a flow after generated is kept throughout the lifetime of a flow, even if it's started and stopped, unless the page is refreshed.

