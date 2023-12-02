import pandas as pd
import numpy as np
import itertools as it
import time
import pickle as pk

# Make lists hashable to be used as dictionary keys
class MyList(list):
    def __hash__(self):
        return hash(self[0])

# Rule filtering class
class Rule:
    def __init__(self, data):
        self.data = data
        self.user_item = None
        self.Rule = {}

    # ************************Calculation Process************************
    def main(self):
        # 1 User-item pivot table, mean centering (user direction)
        self.user_item = pd.pivot_table(self.data, index='ACC_NBR', columns='CONTENT_NAME', values='SCORE')
        self.user_item = self.user_item.groupby(['ACC_NBR']).apply(self.Amend)
        # 2 Generate association rules, calculate similarity (adjusted cosine)
        Rule = self.Association()
        Rule['SIMILARITY'] = Rule['RULE'].map(self.Similarity)
        # 3 Refine rules and return
        return self.Reprocess_rule(Rule)

    # **********************Pairwise Association Rules**********************
    def Association(self):
        # 1 User-product table, exclude users with a single product
        datas = self.data.groupby(['ACC_NBR']).apply(lambda x: x['CONTENT_NAME'].tolist()).reset_index().rename(
            columns={0: 'ITEM'})
        datas = datas[datas['ITEM'].map(lambda x: len(x)) > 1]
        # 2 Pairwise rules, calculate the number of user rules
        datas['ITEM'] = datas['ITEM'].map(lambda x: [i for i in it.combinations(x, 2)])
        datas['COUNT'] = datas['ITEM'].map(lambda x: len(x))

        # 3 Group calculation, generate rule chains and merge
        def merge(data):
            data = (np.concatenate(np.array(data['ITEM'])))
            return pd.Series((data.tolist()))

        datas = datas.groupby(['COUNT']).apply(merge).reset_index().rename(columns={0: 'RULE'}).drop(
            ['COUNT', 'level_1'], axis=1)
        # 4 Group calculation of counts, sort, and deduplicate
        datas['RULE'] = datas['RULE'].map(lambda x: MyList(sorted(x)))
        return datas.groupby(['RULE']).count().reset_index()

    # ***********************Mean-Centering Adjustment**********************
    def Amend(self, data):
        # 1 Get ID, transpose rows and columns
        acc_nbr = data.index.values[0]
        data = data.T
        # 2 Get column data
        data = data[acc_nbr]
        # 3 Calculate mean, return adjusted data
        mean = data.mean(axis=0, skipna=True)
        return data.map(lambda x: x - mean if x != 0 else x)

    # ***********************Similarity Calculation************************
    def Similarity(self, rule_list):
        # 1 Insert rule dictionary
        for rule in rule_list:
            rule_v = self.user_item[rule].copy(deep=True)
            if rule not in self.Rule.keys():
                rule_v.fillna(0, inplace=True)
                self.Rule[rule] = rule_v
        # 2 Return similarity
        return np.corrcoef(self.Rule[rule_list[0]], self.Rule[rule_list[1]])[0, 1]

    # *******************Refinement, Generate Dictionary**********************
    def Reprocess_rule(self, rule):
        # 1 Fill 0
        rule.fillna(0, inplace=True)
        # 2 Reconstruct
        rule['L'] = rule['RULE'].map(lambda x: x[0])
        rule['R'] = rule['RULE'].map(lambda x: x[1])
        rule.drop(['RULE'], axis=1, inplace=True)
        # 3 Mirror and union
        ruleT = rule[['R', 'L', 'SIMILARITY']].rename(columns={'L': 'R', 'R': 'L'})
        rule = pd.concat([rule, ruleT], sort=False)
        # 4 Output dictionary
        rule_dict = rule.groupby('L').apply(
            lambda x: x.set_index('R').T.to_dict('int')['SIMILARITY']).reset_index().rename(columns={0: 'RULE'})
        return rule_dict.set_index('L').T.to_dict('int')['RULE']

if __name__ == '__main__':
    start = time.time()

    file = pd.ExcelFile('target.xlsx')
    datas = pd.read_excel(file, sheet_name='Sheet1', encoding='utf-8')
    result = Rule(datas).main()
    for k, v in result.items():
        print(k, ' : ', v)
    with open('rule.txt', 'wb') as f:
        pk.dump(result, f)

    end = time.time()
    print(end - start)