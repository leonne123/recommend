import pandas as pd
from collections import Counter
import time
import pickle as pk

class Recommend:
    def __init__(self, data, rules, filters, TopN):
        self.data = data
        self.Rule = rules
        self.Filter = filters
        self.TopN = TopN

    # ************************Calculation Process************************
    def main(self):
        # Calculate recommendation scores based on user groups
        return self.data.groupby(['ACC_NBR']).apply(self.Recommendation).reset_index().rename(columns={0: 'RECOMMEND'})

    # *****************Cosine Distance Evaluation, TopN Recommendation*****************
    def Recommendation(self, data):
        self.index = 0
        self.result = {}

        # 0  Mapping Helper Function
        def transform(data):
            print(data)
            if self.index == 0:
                # 0.0 Groupby defaults to calculating both sides for the first element, eliminating this influence
                self.index += 1
            else:
                # 0.1 Get the rule dictionary corresponding to the content
                rule_dict = self.Rule[data['CONTENT_NAME'].values[0]]
                # 0.2 Multiply the rule dictionary's values by content rating
                result_update = dict(map(lambda x: (x[0], x[1] * data['SCORE'].values[0]), rule_dict.items()))
                print(result_update)
                # 0.3 Add the result to the result dictionary, taking the maximum value if there is a duplicate
                r, r_update = Counter(self.result), Counter(result_update)
                self.result = dict(r | r_update)

        # 1  Map distance and rating weighted results based on rules
        data.groupby('CONTENT_NAME').apply(transform).reset_index().rename(columns={0: 'RECOMMEND'})
        # 2  Exclude historical records based on filtering
        filter_dict = self.Filter[data['ACC_NBR'].values[0]]
        self.result = dict(filter(lambda x: x[0] not in filter_dict.keys(), self.result.items()))
        # 3  Return the TopN results after sorting
        return dict(sorted(self.result.items(), key=lambda x: x[1], reverse=True)[0:self.TopN])

if __name__ == '__main__':
    start = time.time()

    TopN = 5

    file = pd.ExcelFile('target.xlsx')
    datas = pd.read_excel(file, sheet_name='Sheet1', encoding='utf-8')
    with open('rule.txt', 'rb') as f:
        rules = pk.load(f)
    with open('filter.txt', 'rb') as f:
        filters = pk.load(f)
    result = Recommend(datas, rules, filters, TopN).main()
    pd.set_option('display.max_columns', None)
    print(result)
    result.to_csv('result.csv', encoding='utf_8_sig', index=0)

    end = time.time()
    print(end - start)