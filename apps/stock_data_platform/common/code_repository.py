def get_sw_ind_list():
    # 获取申万行业分类，可以获取申万2014年版本（28个一级分类，104个二级分类，227个三级分类）
    # 和2021年本版（31个一级分类，134个二级分类，346个三级分类）列表信息
    # index_code industry_name level industry_code is_pub parent_code
    df_level1 = pro.index_classify(level='L1', src='SW2021')
    df_level2 = pro.index_classify(level='L2', src='SW2021')
    df_level3 = pro.index_classify(level='L3', src='SW2021')

    df_temp = pd.merge(df_level3, df_level2, how="left",
                       left_on="parent_code", right_on="industry_code",
                       suffixes=("_level3", "_level2"))
    df_temp = pd.merge(df_temp, df_level1, how="left",
                       left_on="parent_code_level2", right_on="industry_code")
    df_temp = df_temp.rename({"index_code": "index_code_level1", "is_pub": "is_pub_level1",
                              "industry_name": "industry_name_level1"}, axis=1)

    return df_temp[['index_code_level3', 'industry_name_level3', 'is_pub_level3',
                    'index_code_level2', 'industry_name_level2', 'is_pub_level2',
                    'index_code_level1', 'industry_name_level1', 'is_pub_level1']]