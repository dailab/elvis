

<img src="https://i.imgur.com/CVM5RUD.png" alt="Elvis Logo" height="120px" 
/>

# Electric Vehicle Charging Infrastructure Simulator (ELVIS)
This repository contains the source code for Elvis, a planning and management tool for electric vehicles charging infrastructure.
## Installation
### Install using pip

To install the package simply run
```bash
pip install py-elvis
```
This installs the package locally using pip and installs required packages, if not available. 

### Manually download and locally install the elvis package

This may be useful if you want to add changes to the package. Then download or checkout this repository and in the top level that contains the `setup.py` file, run
```bash
pip install -r requirements.txt
python setup.py install
```
This installs the package locally using pip and installs required packages, if not available. 

## Usage

Following, a simple example using one of the pre-defined scenario configurations
```python
import pandas as pd
import yaml
from elvis.config import ScenarioConfig
from elvis.simulate import simulate
from elvis.utility.elvis_general import num_time_steps

with open("elvis/data/config_builder/office.yaml", 'r') as f:
    yaml_str = yaml.safe_load(f)
	
config_from_yaml = ScenarioConfig.from_yaml(yaml_str)

start = '2020-01-01 00:00:00' # format: '%y-%m-%d %H:%M:%S'
end = '2020-12-31 23:00:00'
resolution = '01:00:00'

realisation = config_from_yaml.create_realisation(start, end, '01:00:00')
results = simulate(realisation)

load_profile = results.aggregate_load_profile(num_time_steps(realisation.start_date, realisation.end_date, realisation.resolution))
df = pd.DataFrame(load_profile)

df.head(24).plot()
```

## Acknowledgement

This work was supported in part by Stromnetz Berlin, as well as the Federal Minister for Environment, Nature Conservation and Nuclear Safety (BMU) through the research project [FlexNet4E-Mobility](https://www.erneuerbar-mobil.de/projekte/flexnet4e-mobility) (funding reference 16EM3147-2) and the Federal Ministry for Economic Affairs and Energy (BMWi) throught the project [Neue Berliner Luft](https://www.neueberlinerluft.de/) (funding reference 01MZ18013E).
