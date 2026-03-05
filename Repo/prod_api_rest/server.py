import pandas as pd
from flask import Flask, request, jsonify
from typing import Dict, Any,List, Tuple,Optional

#create class dataset:
class Dataset:
    def __init__(self):
       pass

    def load_data(self,file_pat:str)-> Dict[str, Any]:
        df=pd.DataFrame()
        
        df = pd.read_csv(file_pat)
        
        #create a dictionary to store the data
        data_dict :Dict[str, Any] ={}
        data_dict = df.to_dict(orient='records')

        #use id_contract as index
        res_dic = {}
        for item in data_dict:
            res_dic[item['id_contract']] = item
        
        return res_dic
         



