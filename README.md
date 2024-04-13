# StockProject
## Content
```
.
|-- Backtrader
|-- BaseClass
|   |-- BaseDataFetch.py
|   |-- Test.py
|   `-- __init__.py
|-- DataFetch
|   `-- stock_basic.py
|-- DataStore
|   |-- Important
|   |-- Local
|   `-- Temp
|-- Note
|   |-- Debug
|   `-- YoutubeClass
|-- README.md
|-- Work
|-- common
|   |-- AutoEmail.py
|   |-- IndustryTop.yaml
|   |-- config.py
|   `-- utils.py
|-- demo_test.py
|-- draft.py
|-- main.py
|-- requirements.txt
`-- requirements2.txt
```

- DataStore: data storage directory
  - Important: will be uploaded to github
    - `df_sw2021_industry_info.pkl`: 
      - description: SWS 2021 Industry Classification (31 first-level classifications, 134 second-level classifications, 346 third-level classifications)
      - code in `common/code_repository.py` **get_sw_ind_list**
  - Local: will not be uploaded to github
  - Temp: temporary storage

## Download package from third-party source
- create env
  - conda create -n env39 python=3.9
  - conda create -n env37 python=3.7
  - conda create -n env36 python=3.6
    - Recommend to use python3.6 because matplotlib (need by cerebro.plot)should be 3.2.2
  - show virtual env in jupyter notebook
    - conda install nb_conda
    - pip install -r requirements.txt
    - jupyter notebook
      - add nbextensions
        - install: pip install jupyter_contrib_nbextensions
        - setup: jupyter contrib nbextension install --user
        - Open the jupyter notebook; Go to Nbextensions tab


- get directory path
```python
import os
print(os.path) # xxx/anaconda3/lib/python3.8/posixpath.py
# pip install --target=xxx/anaconda3/lib/python3.8/site-packages PACKAGE
```

