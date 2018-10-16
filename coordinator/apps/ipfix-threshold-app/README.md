## Synopsis

The purpose of the scripts is to estimate an appropriate traffic load threshold in order to trigger Snort Scan when necessary.


## Brief methodology

1. Retrieve previous setted thresholds.
2. Query the IPfix messages.
3. Create Flow objects.
4. Update the Objects by distinghuishing Idle time and active time of traffic load.
5. Update thresholds with a selected algorithm, go to step 2 (loop).
6. When stopped print a JSON file with the Flows Objects characteristics and a log file.


## Requirements

Install via pip: numpy, pandas, pyflux.


## Algorithms Descritption

1. The basic algorithm which is the default; fetches new IPfix messages every setted "Query time". Checks if during this time there have been enough new values recording the traffic in bytes for each flow. 
	If there are, a margin is applied with a mulitple of a default 3.5 times the standard Deviation of the recorded values during the interval of the "Query time". In addition the value produced is multiplied with itself with 		the value of "exponential Smoothing" and added with the previous threshold value by multplying `1 - "exponential Smoothing  value"`.
2. Forecasting algorithm, uses the Local Linear trend model from Pyflux module. Suitable for smaller query periods, in order to make better use of the forecast. The threshold is given by the maximum of the 95% CI forecast.
    In addition, the forecast horizon is determined by the number of the rate values recorded between the previosu IPfix fetch queries.


## Usage

Run the `thresholdUpdater.py` via Python 2.7 in the same machine which run the Tennison project. It has two approaches to update the thresholds: the basic or use the forecast model.
Depending on the functionality the paramterers should be inserted accordingly.
The parameters are set in the `config.json` file.
1. "type" -> Select "0" for the default algorithm or 1 for the Forecasting algorithm.
2. "Query time" -> is the time of every when the scirpt will run and update the threshold. (for both types)
3. "minimumStep" -> Is an additional parameter that allows to update only if the number of new vlaues recording the traffic in bytes exceed a threshold. (for both types)
4. "margin" -> the multiple of standard deviation. Default is 3.5. (for type 0)

Stop the Script when necessary and it will print locally a JSON file with the flows objects named `flows.json`.
In addition an `output.log` is generated with information and warning messages.

This script will use the `Flow.py` accordingly.


## Additional

The `trafficVisualisation.py` is for the purpose of Visualisaing the traffic after the execution of the `thresholdUpdater.py`. Needs GUI interface and to pip install matplotlib (can run either python 2.7 or 3.6). Reads the Json files produced by the `thresholdUpdater.py`.

The `IPfixAnomalyDetection_.py` is on hold possibly will be updated upon further discussion.




