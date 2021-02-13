import pytest
import diffjson 
import yaml


#test_parse01(self):
p = diffjson.parse('/branch01/b01-01')
with open('./data/searchpath/parse_simple01.yaml', 'w') as f:
    yaml.dump(p, f)

p = diffjson.parse('/branch02/b02-01[0]')
with open('./data/searchpath/parse_list01.yaml', 'w') as f:
    yaml.dump(p, f)
