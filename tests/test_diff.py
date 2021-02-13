import pytest
import yaml
import diffjson


class TestBranch(object):
    @pytest.fixture
    def original_branch(self, shared_datadir):
        data = yaml.safe_load((shared_datadir / 'original.yaml').read_text())
        return diffjson.generate_branch(data)

    @pytest.fixture
    def changed_branch_01(self, shared_datadir):
        data = yaml.safe_load((shared_datadir / 'changed_01.yaml').read_text())
        return diffjson.generate_branch(data)

    @pytest.fixture
    def changed_branch_02(self, shared_datadir):
        data = yaml.safe_load((shared_datadir / 'changed_02.yaml').read_text())
        return diffjson.generate_branch(data)

    def test_diff_01(self, original_branch, changed_branch_01):
        expected =  {'/branch01/b01-01': ['string', 'changed']}
        diff = changed_branch_01 - original_branch
        value = diff.search('/branch01/b01-01')
        assert len(value) == 1
        assert value[0] == expected

    def test_diff_02(self, original_branch, changed_branch_01):
        expected =  {'/branch01/b01-02': [1, 'NullBranch']}
        diff = changed_branch_01 - original_branch
        value = diff.search('/branch01/b01-02')
        assert len(value) == 1
        assert value[0] == expected

    def test_diff_03(self, original_branch, changed_branch_01):
        expected =  {'/branch02/b02-01/[1]/value/b02-01-i02-01/[2]/name':
                      ['n02-01-i02-01-i03', 'changed']}
        diff = changed_branch_01 - original_branch
        value = diff.search('/branch02/b02-01/[1]/value/b02-01-i02-01/[2]/name')
        assert len(value) == 1
        assert value[0] == expected

    def test_diff_04(self, original_branch, changed_branch_01):
        expected = {'/branch02/b02-01/[2]/name':
                      ['n02-01-i03', 'NullBranch']}
        diff = changed_branch_01 - original_branch
        value = diff.search('/branch02/b02-01/[2]/name')
        assert len(value) == 1
        assert value[0] == expected

    def test_diff_multi_01(self, original_branch, changed_branch_01, changed_branch_02):
        expected = {'/branch01/b01-01': ['string', 'changed', 'changed 2']}
        diff = diffjson.diff_branches(
            [original_branch, changed_branch_01, changed_branch_02])
        value = diff.search('/branch01/b01-01')
        assert len(value) == 1
        assert value[0] == expected

    def test_diff_masked(self, original_branch, changed_branch_01):
        expected = {'/branch02/b02-01/n02-01-i01/value':
                      ['v02-01-i01', 'v02-01-i01']}
        masks = {'/branch02/b02-01': lambda x: x['name']}
        diff = diffjson.diff_branches(
            [original_branch, changed_branch_01], nodenamemasks=masks)
        value = diff.search('/branch02/b02-01/n02-01-i01/value')
        assert len(value) == 1
        assert value[0] == expected

    def test_is_changed_root_01(self, original_branch):
        diff = original_branch - original_branch
        assert diff.is_unchanged()

    def test_is_changed_root_02(self, original_branch, changed_branch_01):
        diff = changed_branch_01 - original_branch
        assert not diff.is_unchanged()

    def test_is_changed_child_01(self, original_branch, changed_branch_01):
        diff = changed_branch_01 - original_branch
        nn = diffjson.parse('/branch01')
        childbranch = diff._search(nn)[0]
        assert not childbranch.is_unchanged()

    def test_is_changed_child_02(self, original_branch, changed_branch_01):
        diff = changed_branch_01 - original_branch
        nn = diffjson.parse('/branch03')
        childbranch = diff._search(nn)[0]
        assert childbranch.is_unchanged()

    def test_dump_hide_unchanged(self, original_branch, changed_branch_01):
        diff = changed_branch_01 - original_branch
        expected ={
            '/': ['DictBranch', 'DictBranch'],
            '/branch01': ['DictBranch', 'DictBranch'],
            '/branch01/b01-01': ['string', 'changed'],
            '/branch01/b01-02': [1, 'NullBranch'],
            '/branch01/b01-05': ['NullBranch', 'added'],
            '/branch02': ['DictBranch', 'DictBranch'],
            '/branch02/b02-01': ['ListBranch', 'ListBranch'],
            '/branch02/b02-01/[1]': ['DictBranch', 'DictBranch'],
            '/branch02/b02-01/[1]/value': ['DictBranch', 'DictBranch'],
            '/branch02/b02-01/[1]/value/b02-01-i02-01': ['ListBranch', 'ListBranch'],
            '/branch02/b02-01/[1]/value/b02-01-i02-01/[2]':
            ['DictBranch', 'DictBranch'],
            '/branch02/b02-01/[1]/value/b02-01-i02-01/[2]/value':
             ['v02-01-i02-01-i03', 'changed'],
            '/branch02/b02-01/[1]/value/b02-01-i02-01/[2]/name':
             ['n02-01-i02-01-i03', 'changed'],
            '/branch02/b02-01/[1]/value/b02-01-i02-01/[3]':
             ['NullBranch', 'DictBranch'],
            '/branch02/b02-01/[1]/value/b02-01-i02-01/[3]/value':
             ['NullBranch', 'v02-01-i02-01-i04'],
            '/branch02/b02-01/[1]/value/b02-01-i02-01/[3]/name':
             ['NullBranch', 'n02-01-i02-01-i04'],
            '/branch02/b02-01/[2]': ['DictBranch', 'NullBranch'],
            '/branch02/b02-01/[2]/value': ['DictBranch', 'NullBranch'],
            '/branch02/b02-01/[2]/value/b02-01-i03-01': ['v02-01-i03-01', 'NullBranch'],
            '/branch02/b02-01/[2]/name': ['n02-01-i03', 'NullBranch']}
        assert diff.dump(hide_unchanged=True) == expected
