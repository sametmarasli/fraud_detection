from kafka import KafkaConsumer, TopicPartition
from json import loads
import numpy as np
import time
import pickle
import os
import logging
import pandas as pd

def decode_json(jsons_comb):

    x_train = loads(jsons_comb[0])
    y_train = loads(jsons_comb[1])

    return x_train, y_train

def get_data_from_kafka(**kwargs):

    consumer = KafkaConsumer(
        kwargs["topic"],                                # specify topic to consume from
        bootstrap_servers=[kwargs["client"]],
        consumer_timeout_ms=3000,
        api_version=(0,10,2),                       # break connection if the consumer has fetched anything for 3 secs (e.g. in case of an empty topic)
        auto_offset_reset='earliest',                   # automatically reset the offset to the earliest offset (should the current offset be deleted or anything)
        enable_auto_commit=True,                        # offsets are committed automatically by the consumer
        #group_id='my-group',
        value_deserializer=lambda x: loads(x.decode('utf-8')))


    logging.info('Consumer constructed')

    try:
        xs = []
        ys = []

        
        for message in consumer:                            # loop over messages
            message = message.value
            x, y = decode_json(message)            # decode JSON
            xs.extend(x)
            ys.extend(y)

        x_train = pickle.load(open(os.getcwd() + kwargs['path_train_set'], "rb"))[0]
        Xs = pd.DataFrame(xs, columns=x_train.columns)
        ys = pd.Series(ys)
        
        logging.info(f"Messages are collected.")
        
        new_samples = [Xs, ys]
        pickle.dump(new_samples, open(os.getcwd()+kwargs['path_new_data']+str(time.strftime("%Y%m%d_%H%M"))+"_new_samples.p", "wb"))     # write data
        logging.info(str(Xs.shape[0])+' new samples serialized')

        consumer.close()

    except Exception as e:
        print(e)
        logging.info('Error: '+e)

def load_data(**kwargs):

    # Load the Kafka-fetched data that is stored in the to_use_for_model_update folder

    for file_d in os.listdir(os.getcwd()+kwargs['path_new_data']):

        if 'new_samples.p' in file_d:

            new_samples = pickle.load(open(os.getcwd()+kwargs['path_new_data'] + file_d, "rb"))
            train_set= pickle.load(open(os.getcwd()+kwargs['path_train_set'], "rb"))
            test_set = pickle.load(open(os.getcwd()+kwargs['path_test_set'], "rb"))

            logging.info('data loaded')
            return [train_set, test_set, new_samples]

        else:
            logging.info('no data found')



