# diffjson
Utilities to diff json data.
https://nfwprod.github.io/diffjson/

# Features

- Enable search like XPATH.
- Enable diff for multi json data.

# Branch Class for Search

## Branch Class
Convert dict/list json data to Branch class format by 'generate_branch'.
Branch class is hierachical class tree.

- RootBranch
  - Root for all child branches.
  - Provide search and other methods for users.
- DictBranch
  - Child branch for dict format child.
- ListBranch
  - Child branch for list format child.
- Leaf
  - Edge branch for str, bool, int, and float.
- Branch
  - Branch common class for inheritate.

## Search
Branch class accept search with xpath like strings. (Strongly inspired by josonpath-ng!!)


```yaml
# Example Data, sample.yaml
branch01:
  b01-01: string
  b01-02: 1
  b01-03: 2.0
  b01-04: True
branch02:
  b02-01:
    - name: n02-01-i01
      value: v02-01-i01
    - name: n02-01-i02
      value:
        b02-01-i02-01:
          - name: n02-01-i02-01-i01
            value: v02-01-i02-01-i01
          - name: n02-01-i02-01-i02
            value: v02-01-i02-01-i02
          - name: n02-01-i02-01-i03
            value: v02-01-i02-01-i03
        b02-01-i02-02:
          name: n02-01-i02-02
          value: v02-01-i02-02
    - name: n02-01-i03
      value:
        b02-01-i03-01: v02-01-i03-01
branch03:
  b03-01: null
```

```python
import diffjson
import yaml

with open('sample.yaml'), 'r') as f:
  sampledata = yaml.safe_load(f)

# Get dict format data under b01-01
b = diffjson.generate_branch(sampledata)
result = b.search('/branch01/b01-01')

print(result)
> ['string']

```

Search returns all matched data as List style.

# DiffBranch Class for Diff JSON Data

## DiffBranch Class
Diff multi json data as Branch instance by 'diff_branch'.

- DiffRootBranch
  - Root for all child diff branches.
- DiffCommonBranch
  - Child branch for all data format.
  - Diff for dict, list and leaf are contained in DiffCommonBranch.Branch.
- DiffBranch
  - Branch common class for inheritate.

## Diff

```python
diffbranch = diffjson.diff_branch([data01, data02, data03])

# Export diff in csv format
diffbranch.export_csv('./diff.csv')
```

## NodenameMasks Options
Sometimes data are contained in list format and orders are changes randomly.
For example,,

Data Before.
```yaml
- name: id01
  value: data01
- name: id02
  value: data02
- name: id03
  value: data03
```

Data After.
```yaml
- name: id01
  value: data01
- name: id03
  value: data03
- name: id02
  value: changed
```

We want to diff "name: id02" and "name: id02".
Don't want to diff second data "name: id02" and "name: id03".

For such case, use mask function.

```python

masks = {'/': lambda x: x['name'], '/branch01': lambda x: x['id']}

diffbranch = diffjson.diff_branch(
                [data01, data02, data03],
                nodenamemasks=masks)
```

Nodename masks convert list part to dict part with lambda generated key like follows.

Data Before
```yaml
id01:
  name: id01
  value: data01
id02:
  name: id02
  value: data02
id03:
  name: id03
  value: data03
```

Data After
```yaml
id01:
  name: id01
  value: data01
id02:
  name: id02
  value: changed
id03:
  name: id03
  value: data03
```
