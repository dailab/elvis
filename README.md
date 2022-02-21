

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
from elvis import ScenarioConfig, simulate, num_time_steps

import yaml
with open("elvis/data/config_builder/office.yaml", 'r') as f:
    yaml_str = yaml.safe_load(f)
config_from_yaml = ScenarioConfig.from_yaml(yaml_str)

results = simulate(config_from_yaml, start_date='2020-01-01 00:00:00', end_date='2020-12-31 23:00:00', resolution='01:00:00')
load_profile = results.aggregate_load_profile(8760)

import matplotlib.pyplot as plt
plt.plot(load_profile)
```

## Applications in the wild and acknowledgements

ELVIS was developed at the [DAI-Laboratory](https://dai-labor.de/) supported in part by Stromnetz Berlin, as well as the Federal Minister for Environment, Nature Conservation and Nuclear Safety (BMU) through the research project [FlexNet4E-Mobility](https://www.erneuerbar-mobil.de/projekte/flexnet4e-mobility) (funding reference 16EM3147-2) and the Federal Ministry for Economic Affairs and Energy (BMWi) throught the project [Neue Berliner Luft](https://www.neueberlinerluft.de/) (funding reference 01MZ18013E).

It's conceputally based on earlier similar simulations tools that have been peer-reviewed and published in:
* Draz, Mahmoud, Marcus Voß, Daniel Freund, and Sahin Albayrak "The impact of electric vehicles on low voltage grids: A case study of berlin." 2018 Power Systems Computation Conference (PSCC). IEEE, 2018.
* Draz, Mahmoud, and Sahin Albayrak. "A Power Demand Estimator for Electric Vehicle Charging Infrastructure." 2019 IEEE Milan PowerTech. IEEE, 2019.

An earlier tool has been presented at the poster sesssion at the 10th European openmod Workshop in Berlin (15.-17.1.2020).

ELVIS has been completely re-implemented as a software tool to be used with a web-based [Graphical User Interface](https://elvis.aot.tu-berlin.de/) (contact izgh.hadachi[at]dai-labor.de if you want to get test user access) and to be integrated prototypically as a load in DIgSILENT PowerFactory for Stromnetz Berlin. It's conceptually related to the earlier simulation tools and was further conceputally inspired by similar tools such as:
* https://github.com/RAMP-project/RAMP-mobility
* https://github.com/TUMFTM/urbanev
* https://github.com/rl-institut/spice_ev
* https://gitlab.com/diw-evu/emobpy/emobpy

ELVIS has been used to simulate data in the peer-reviewed paper:
* Hadachi, Izgh, Marcus Voss, and Sahin Albayrak. "Sector-Coupled District Energy Management with Heating and Bi-Directional EV-Charging." 2021 IEEE Madrid PowerTech. IEEE, 2021.

[This talk](https://www.youtube.com/watch?v=bayf0SAoyPk) at the Berliner Energietage presents some example results of the tool.
