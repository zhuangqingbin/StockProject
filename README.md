# StockProject
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

import os

print(os.path)

result: e.g. xxx/anaconda3/lib/python3.8/posixpath.py

- pip install --target=xxx/anaconda3/lib/python3.8/site-packages PACKAGE
