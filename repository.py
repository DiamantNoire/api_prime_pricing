from server import Dataset


class Repository:
    def get_client_data(self,index):
        dataset = Dataset()
        data_dict = dataset.load_data(file_pat='train.csv')
        res_data = data_dict[index]
        return res_data
