import const
import datetime
import requests

PROMETHEUS = 'http://prometheus:9090'
BENTOML = 'http://bento-fyp:3000/'
PROMETHEUS_ENDPOINT_INSTANT_QUERY = '/api/v1/query'
PROMETHEUS_ENDPOINT_RANGE_QUERY = '/api/v1/query_range'

def getData():
        lastVals = [0] * len(const.cumulative_cols)

        timeSteps = 24
        period = [ [[0] * 22] * 12 ] * 24

        ### Creating the 3D input: 24x12x20  (new model: 24x12x21) ###

        current_timestamp = datetime.datetime.now().timestamp()
        start_timestamp = datetime.datetime.fromtimestamp(current_timestamp-120).strftime("%Y-%m-%dT%H:%M:%S.%fZ") # endtime - 2 minutes
        end_timestamp = datetime.datetime.fromtimestamp(current_timestamp).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        window_5min_timestamp = datetime.datetime.fromtimestamp(current_timestamp-120-300).strftime("%Y-%m-%dT%H:%M:%S.%fZ") # endtime - 2 minutes
        window_30min_timestamp = datetime.datetime.fromtimestamp(current_timestamp-120-1800).strftime("%Y-%m-%dT%H:%M:%S.%fZ") # endtime - 2 minutes

        # Iterate for each service
        for m, service in enumerate(const.containers):
            first = True

            # Iterate for each feature in a service
            n = 0
            for _, feature in enumerate(const.cumulative_cols + const.other_cols):
                q = '{0}{{name="{1}"}}'.format(feature, service)
                # response = requests.get(PROMETHEUS + PROMETHEUS_ENDPOINT_INSTANT_QUERY, params={'query': q, 'time': datetime.datetime.fromtimestamp(current_timestamp-5*step).strftime("%Y-%m-%dT%H:%M:%S.%fZ")})

                # Start and end times are inclusive in range query
                response = requests.get(PROMETHEUS + PROMETHEUS_ENDPOINT_RANGE_QUERY, 
                                        params={
                                            'query': q,
                                            'start': start_timestamp,
                                            'end': end_timestamp,
                                            'step':'5s'
                                            })
                # print(q, start_timestamp, end_timestamp)

                results = response.json()
                # DEBUG
                # print(results)
                dataV = results['data']

                # DEBUG: Print all 19 values of a feature
                # print(m, n,": ", end="")
                if len(dataV['result']) < 1:
                    break
                periodData = dataV['result'][0]['values']
                # print(periodData)

                if feature in const.cumulative_cols:
                    for k in range(24):                        
                        period[k][m][n] = float(periodData[k+1][1]) - float(periodData[k][1]) 
                        # print("{:0.4f}".format(period[k][m][n]), end=" ")
                else:
                    for k in range(24):
                        if periodData[k][1] == "" and k!=0:
                            period[k][m][n] = float(periodData[k-1][1])
                        else:
                            period[k][m][n] = float(periodData[k][1])
                        # print("{:0.4f}".format(period[k][m][n]), end=" ")

                # DEBUG
                # print('\n')
                
                n += 1

            if const.rt_metrics[m][0] !=0:
                # RT Step sum
                for rt in const.rt_metrics[m]:
                    q = '{0}'.format(rt)
                    # DEBUG
                    # print(q)

                    # Start and end times are inclusive in range query
                    response = requests.get(PROMETHEUS + PROMETHEUS_ENDPOINT_RANGE_QUERY, 
                                            params={
                                                'query': q,
                                                'start': start_timestamp,
                                                'end': end_timestamp,
                                                'step':'5s'
                                                })

                    results = response.json()
                    # DEBUG
                    # print(results)
                    dataV = results['data']
                    if len(dataV['result']) < 1:
                        break
                    # print(dataV['result'][0]['values'])
                    periodData = dataV['result'][0]['values']

                    

                # DEBUG: Print RT values of a feature
                # print(m, n,": ", end="")
                # for k in range(24):                        
                #     print(period[k][m][n], end=" ")
                # DEBUG
                # print('\n')

                n += 1

                # RT 5min Window sum
                for rt in const.rt_metrics[m]:
                    q = '{0}'.format(rt)

                    # Start and end times are inclusive in range query
                    response = requests.get(PROMETHEUS + PROMETHEUS_ENDPOINT_RANGE_QUERY, 
                                            params={
                                                'query': q,
                                                'start': window_5min_timestamp,
                                                'end': end_timestamp,
                                                'step':'5s'
                                                })

                    results = response.json()
                    # DEBUG
                    # print(results)
                    dataV = results['data']
                    if len(dataV['result']) < 1:
                        break
                    # print(dataV['result'][0]['values'])
                    periodData = dataV['result'][0]['values']

                    movingAvg5min = 0
                    if len(periodData)==60:
                        for i in range(12*5):
                            movingAvg5min += float(periodData[i][1])
                            
                        for k in range(24):
                            period[k][m][n] += movingAvg5min
                            movingAvg5min = float(periodData[k+12*5][1]) - float(periodData[k][1])

                # DEBUG: Print RT values of a feature
                # print(m, n,": ", end="")
                # for k in range(24):                        
                #     print(period[k][m][n], end=" ")
                # DEBUG
                # print('\n')

                n += 1

                # RT 30min Window sum
                for rt in const.rt_metrics[m]:
                    q = '{0}'.format(rt)

                    # Start and end times are inclusive in range query
                    response = requests.get(PROMETHEUS + PROMETHEUS_ENDPOINT_RANGE_QUERY, 
                                            params={
                                                'query': q,
                                                'start': window_30min_timestamp,
                                                'end': end_timestamp,
                                                'step':'5s'
                                                })

                    results = response.json()
                    # DEBUG
                    # print(results)
                    dataV = results['data']
                    if len(dataV['result']) < 1:
                        break
                    # print(dataV['result'][0]['values'])
                    periodData = dataV['result'][0]['values']

                    movingAvg30min = 0
                    if len(periodData)==60:
                        for i in range(12*5):
                            movingAvg30min += float(periodData[i][1])
                            
                        for k in range(24):
                            period[k][m][n] += movingAvg30min
                            movingAvg30min = float(periodData[k+12*5][1]) - float(periodData[k][1])

                # DEBUG: Print RT values of a feature
                # print(m, n,": ", end="")
                # for k in range(24):                        
                #     print(period[k][m][n], end=" ")
                # DEBUG
                # print('\n')

                n += 1
            
            else:
                for k in range (24):
                    period[k][m][n] = 0
                    # DEBUG: Print RT values of a feature
                    # print(m, n,": ", end="")
                    # for k in range(24):                        
                    #     print(period[k][m][n], end=" ")
                    # DEBUG
                    # print('\n')
                    n += 1
                    period[k][m][n] = 0
                                        # DEBUG: Print RT values of a feature
                    # print(m, n,": ", end="")
                    # for k in range(24):                        
                    #     print(period[k][m][n], end=" ")
                    # DEBUG
                    # print('\n')

                    n += 1
                    period[k][m][n] = 0
                    # DEBUG: Print RT values of a feature
                    # print(m, n,": ", end="")
                    # for k in range(24):                        
                    #     print(period[k][m][n], end=" ")
                    # DEBUG
                    # print('\n')
                    n -= 2


            # break

        return period
