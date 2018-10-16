#From the flows.ccv extract the n most different  flows by aggregating the Standard Deviation values
import csv
import sys
import Flow
import numpy as np
from sklearn.preprocessing import StandardScaler
import time
from scipy.stats import entropy
from scipy.stats import spearmanr
from sklearn.preprocessing import scale
#take parameters for zero and percentage up

def anomaly_detection(number):
    flows = {}
    with open('flows.csv', 'r') as csv_file:
        reader = csv.reader(csv_file)
        dictionary = dict(reader)
        for key,value in dictionary.items():
            values = value.split(',')
          #  print(values)
            flow = Flow.flow(values[0], values[1], int(values[2]), int(values[3]),float(values[4]))
            flow.strConstructor(float(values[5]),float(values[6]),float(values[7]),float(values[8]),float(values[9]),float(values[10]))
            flows[key]= flow

    matrix = np.zeros([0,6])
    for i,j in flows.items():
        temp = np.array([j.byte_total_avg,j.packet_total_avg,j.avg_bps,j.avg_pps,j.avg_time_diff,j.std_time_diff])
        matrix = np.vstack([matrix,temp])
    #
    #get Hash Ids
    temp1 = np.array(list(flows.keys()))

    #Standarization Anomaly Detection
    start_time = time.time()
    scaler =  abs(StandardScaler().fit_transform(matrix))
    #sum rows
    temp2 = scaler.sum(axis=1)
    scaler = np.insert(scaler,0,temp1,axis=1)
    scaler = np.insert(scaler,7,temp2,axis=1)
    scaler = scaler[scaler[:, 7].argsort()[::-1]]
    #TODO add std check if the values are little or similar
    print ("Standarization indicates the Hash ID:", scaler[:number,0])
    print("Produced Standarziation Anomaly Detection in: %s seconds ---" % (time.time() - start_time))

    #Spearman Correlation Anomaly Detection
    start_time = time.time()
    _, p = spearmanr(matrix,axis=1)
    temp2 = p.sum(axis=1)
    output = np.vstack([temp1,temp2])
    output = np.transpose(output)
    output = output[output[:, 1].argsort()[::-1]]
    print ("Pearson Correlation indicates the Hash ID:", output[:number, 0])
    print("Produced Pearson Correlation Anomaly Detection in: %s seconds ---" % (time.time() - start_time))

    #Relative Entropy
    start_time = time.time()
    temp2 = abs(scale(entropy(np.transpose(matrix)),with_mean=True,with_std=True))
    output = np.vstack([temp1,temp2])
    output = np.transpose(output)
    output = output[output[:, 1].argsort()[::-1]]
    print ("Relative Entropy indicates the Hash ID:", output[:number, 0])
    print("Relative Entropy Anomaly Detection in: %s seconds ---" % (time.time() - start_time))


if __name__ == '__main__':
    #TODO make configurations check
    #From configurations specify the number of instances to show
    anomaly_detection(int(sys.argv[1:][0]))



