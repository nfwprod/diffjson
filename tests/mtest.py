import diffjson
import yaml

with open('./data/original.yaml', 'r') as f:
    data = yaml.safe_load(f)
    branch = diffjson.generate_branch(data)

with open('./data/changed_01.yaml', 'r') as f:
    data = yaml.safe_load(f)
    branch_changed_01 = diffjson.generate_branch(data)

diff = branch_changed_01 - branch

mask = {'/branch02/b02-01': lambda x: x['name']}
diff2 = diffjson.diff_branches([branch, branch_changed_01], mask)

