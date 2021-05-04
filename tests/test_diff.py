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
        expected = ['string', 'changed']
        diff = changed_branch_01 - original_branch
        value = diff.search('/branch01/b01-01')
        assert len(value) == 1
        assert value[0] == expected

    def test_diff_02(self, original_branch, changed_branch_01):
        expected = [1, None]
        diff = changed_branch_01 - original_branch
        value = diff.search('/branch01/b01-02')
        assert len(value) == 1
        assert value[0] == expected

    def test_diff_03(self, original_branch, changed_branch_01):
        expected = ['n02-01-i02-01-i03', 'changed']
        diff = changed_branch_01 - original_branch
        value = diff.search('/branch02/b02-01/[1]/value/b02-01-i02-01/[2]/name')
        assert len(value) == 1
        assert value[0] == expected

    def test_diff_04(self, original_branch, changed_branch_01):
        expected = ['n02-01-i03', None]
        diff = changed_branch_01 - original_branch
        value = diff.search('/branch02/b02-01/[2]/name')
        assert len(value) == 1
        assert value[0] == expected

    def test_diff_multi_01(self, original_branch, changed_branch_01, changed_branch_02):
        expected = ['string', 'changed', 'changed 2']
        diff = diffjson.DiffRootBranch(
            [original_branch, changed_branch_01, changed_branch_02])
        value = diff.search('/branch01/b01-01')
        assert len(value) == 1
        assert value[0] == expected

    def test_diff_multi_details01(self, original_branch, changed_branch_01, changed_branch_02):
        expected = ('/branch01/b01-01', ['string', 'changed', 'changed 2'])
        diff = diffjson.DiffRootBranch(
            [original_branch, changed_branch_01, changed_branch_02])
        value = diff.search('/branch01/b01-01', details=True)
        assert len(value) == 1
        assert value[0] == expected

    def test_diff_masked(self, original_branch, changed_branch_01):
        expected = ['v02-01-i01', 'v02-01-i01']
        masks = {'/branch02/b02-01': lambda x: x['name']}
        diff = diffjson.DiffRootBranch(
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
        childbranch = diff.raw_search(nn)[0]
        assert not childbranch.is_unchanged()

    def test_is_changed_child_02(self, original_branch, changed_branch_01):
        diff = changed_branch_01 - original_branch
        nn = diffjson.parse('/branch03')
        childbranch = diff.raw_search(nn)[0]
        assert childbranch.is_unchanged()

    def test_dump_as_table(self, original_branch, changed_branch_01):
        diff = changed_branch_01 - original_branch
        expected = [
            ['LocationPath', 'Data0', 'Data1'],
            ['/', 'DictBranch', 'DictBranch'],
            ['/branch01', 'DictBranch', 'DictBranch'],
            ['/branch01/b01-01', 'string', 'changed'],
            ['/branch01/b01-02', 1, 'NullBranch'],
            ['/branch01/b01-03', 2.0, 2.0],
            ['/branch01/b01-04', True, True],
            ['/branch01/b01-05', 'NullBranch', 'added'],
            ['/branch02', 'DictBranch', 'DictBranch'],
            ['/branch02/b02-01', 'ListBranch', 'ListBranch'],
            ['/branch02/b02-01/[0]', 'DictBranch', 'DictBranch'],
            ['/branch02/b02-01/[0]/name', 'n02-01-i01', 'n02-01-i01'],
            ['/branch02/b02-01/[0]/value', 'v02-01-i01', 'v02-01-i01'],
            ['/branch02/b02-01/[1]', 'DictBranch', 'DictBranch'],
            ['/branch02/b02-01/[1]/name', 'n02-01-i02', 'n02-01-i02'],
            ['/branch02/b02-01/[1]/value', 'DictBranch', 'DictBranch'],
            ['/branch02/b02-01/[1]/value/b02-01-i02-01', 'ListBranch',
                'ListBranch'],
            ['/branch02/b02-01/[1]/value/b02-01-i02-01/[0]',
                'DictBranch', 'DictBranch'],
            ['/branch02/b02-01/[1]/value/b02-01-i02-01/[0]/name',
                'n02-01-i02-01-i01', 'n02-01-i02-01-i01'],
            ['/branch02/b02-01/[1]/value/b02-01-i02-01/[0]/value',
                'v02-01-i02-01-i01', 'v02-01-i02-01-i01'],
            ['/branch02/b02-01/[1]/value/b02-01-i02-01/[1]',
                'DictBranch', 'DictBranch'],
            ['/branch02/b02-01/[1]/value/b02-01-i02-01/[1]/name',
                'n02-01-i02-01-i02', 'n02-01-i02-01-i02'],
            ['/branch02/b02-01/[1]/value/b02-01-i02-01/[1]/value',
                'v02-01-i02-01-i02', 'v02-01-i02-01-i02'],
            ['/branch02/b02-01/[1]/value/b02-01-i02-01/[2]',
                'DictBranch', 'DictBranch'],
            ['/branch02/b02-01/[1]/value/b02-01-i02-01/[2]/name',
                'n02-01-i02-01-i03', 'changed'],
            ['/branch02/b02-01/[1]/value/b02-01-i02-01/[2]/value',
                'v02-01-i02-01-i03', 'changed'],
            ['/branch02/b02-01/[1]/value/b02-01-i02-01/[3]',
                'NullBranch', 'DictBranch'],
            ['/branch02/b02-01/[1]/value/b02-01-i02-01/[3]/name',
                'NullBranch', 'n02-01-i02-01-i04'],
            ['/branch02/b02-01/[1]/value/b02-01-i02-01/[3]/value',
                'NullBranch', 'v02-01-i02-01-i04'],
            ['/branch02/b02-01/[1]/value/b02-01-i02-02',
                'DictBranch', 'DictBranch'],
            ['/branch02/b02-01/[1]/value/b02-01-i02-02/name',
                'n02-01-i02-02', 'n02-01-i02-02'],
            ['/branch02/b02-01/[1]/value/b02-01-i02-02/value',
                'v02-01-i02-02', 'v02-01-i02-02'],
            ['/branch02/b02-01/[2]', 'DictBranch', 'NullBranch'],
            ['/branch02/b02-01/[2]/name', 'n02-01-i03', 'NullBranch'],
            ['/branch02/b02-01/[2]/value', 'DictBranch', 'NullBranch'],
            ['/branch02/b02-01/[2]/value/b02-01-i03-01',
                'v02-01-i03-01', 'NullBranch'],
            ['/branch03', 'DictBranch', 'DictBranch'],
            ['/branch03/b03-01', None, None]]
        assert diff.dump_as_table() == expected

    def test_dump_as_table_hide_unchanged(self, original_branch, changed_branch_01):
        diff = changed_branch_01 - original_branch
        expected = [
            ['LocationPath', 'Data0', 'Data1'],
            ['/', 'DictBranch', 'DictBranch'],
            ['/branch01', 'DictBranch', 'DictBranch'],
            ['/branch01/b01-01', 'string', 'changed'],
            ['/branch01/b01-02', 1, 'NullBranch'],
            ['/branch01/b01-05', 'NullBranch', 'added'],
            ['/branch02', 'DictBranch', 'DictBranch'],
            ['/branch02/b02-01', 'ListBranch', 'ListBranch'],
            ['/branch02/b02-01/[1]', 'DictBranch', 'DictBranch'],
            ['/branch02/b02-01/[1]/value', 'DictBranch', 'DictBranch'],
            ['/branch02/b02-01/[1]/value/b02-01-i02-01',
                'ListBranch', 'ListBranch'],
            ['/branch02/b02-01/[1]/value/b02-01-i02-01/[2]',
                'DictBranch', 'DictBranch'],
            ['/branch02/b02-01/[1]/value/b02-01-i02-01/[2]/name',
                'n02-01-i02-01-i03', 'changed'],
            ['/branch02/b02-01/[1]/value/b02-01-i02-01/[2]/value',
                'v02-01-i02-01-i03', 'changed'],
            ['/branch02/b02-01/[1]/value/b02-01-i02-01/[3]',
                'NullBranch', 'DictBranch'],
            ['/branch02/b02-01/[1]/value/b02-01-i02-01/[3]/name',
                'NullBranch', 'n02-01-i02-01-i04'],
            ['/branch02/b02-01/[1]/value/b02-01-i02-01/[3]/value',
                'NullBranch', 'v02-01-i02-01-i04'],
            ['/branch02/b02-01/[2]', 'DictBranch', 'NullBranch'],
            ['/branch02/b02-01/[2]/name', 'n02-01-i03', 'NullBranch'],
            ['/branch02/b02-01/[2]/value', 'DictBranch', 'NullBranch'],
            ['/branch02/b02-01/[2]/value/b02-01-i03-01',
                'v02-01-i03-01', 'NullBranch']]
        assert diff.dump_as_table(hide_unchanged=True) == expected

    def test_dump_as_structure_two(self, original_branch, changed_branch_01):
        diff = changed_branch_01 - original_branch
        branch = diff.raw_search(diffjson.parse('/branch01'))[0]
        expected = [{'b01-01': 'string', 'b01-02': 1,
                     'b01-03': 2.0, 'b01-04': True},
                    {'b01-01': 'changed',
                     'b01-03': 2.0, 'b01-04': True,
                     'b01-05': 'added'}]
        assert branch.dump_as_structure() == expected

    def test_dump_as_structure_two_hide_unchanged(
            self, original_branch, changed_branch_01):
        diff = changed_branch_01 - original_branch
        unchanged = diff.raw_search(diffjson.parse('/branch01/b01-03'))[0]
        changed = diff.raw_search(diffjson.parse('/branch01'))[0]
        u_01 = unchanged.dump()
        u_02 = unchanged.dump(hide_unchanged=True)
        c_01 = changed.dump()
        c_02 = changed.dump(hide_unchanged=True)

        assert (u_01 != u_02) and (c_01 == c_02)

    def test_dump_as_structure_two_added(
            self, original_branch, changed_branch_01):
        diff = changed_branch_01 - original_branch
        expected = [[None, 'added'],
                    [None,
                     {'name': 'n02-01-i02-01-i04',
                      'value': 'v02-01-i02-01-i04'}],
                    [None, 'n02-01-i02-01-i04'],
                    [None, 'v02-01-i02-01-i04']]
        assert diff.search('//', dump_mode='added') == expected

    def test_dump_as_structure_two_added_details(
            self, original_branch, changed_branch_01):
        diff = changed_branch_01 - original_branch
        expected = [('/branch01/b01-05', [None, 'added']),
                    ('/branch02/b02-01/[1]/value/b02-01-i02-01/[3]',
                        [None,
                         {'name': 'n02-01-i02-01-i04',
                          'value': 'v02-01-i02-01-i04'}]),
                    ('/branch02/b02-01/[1]/value/b02-01-i02-01/[3]/name',
                         [None, 'n02-01-i02-01-i04']),
                    ('/branch02/b02-01/[1]/value/b02-01-i02-01/[3]/value',
                         [None, 'v02-01-i02-01-i04'])]
        assert diff.search('//', details=True, dump_mode='added') == expected

    def test_dump_as_structure_two_bulk_added(
            self, original_branch, changed_branch_01):
        diff = changed_branch_01 - original_branch
        expected = [[None, 'added'],
                    [None,
                     {'name': 'n02-01-i02-01-i04',
                      'value': 'v02-01-i02-01-i04'}]]
        assert diff.search('//', dump_mode='bulk_added') == expected

    def test_dump_as_structure_two_bulk_added_details(
            self, original_branch, changed_branch_01):
        diff = changed_branch_01 - original_branch
        expected = [('/branch01/b01-05', [None, 'added']),
                    ('/branch02/b02-01/[1]/value/b02-01-i02-01/[3]',
                        [None,
                         {'name': 'n02-01-i02-01-i04',
                          'value': 'v02-01-i02-01-i04'}])]
        assert diff.search('//', details=True, dump_mode='bulk_added') == expected
    def test_dump_as_structure_two_removed(
            self, original_branch, changed_branch_01):
        diff = changed_branch_01 - original_branch
        expected = [[1, None],
                    [{'name': 'n02-01-i03',
                      'value': {'b02-01-i03-01': 'v02-01-i03-01'}},
                     None],
                    ['n02-01-i03', None],
                    [{'b02-01-i03-01': 'v02-01-i03-01'}, None],
                    ['v02-01-i03-01', None]]
        assert diff.search('//', dump_mode='removed') == expected

    def test_dump_as_structure_two_removed_details(
            self, original_branch, changed_branch_01):
        diff = changed_branch_01 - original_branch
        expected = [('/branch01/b01-02', [1, None]),
                    ('/branch02/b02-01/[2]',
                       [{'name': 'n02-01-i03',
                         'value': {'b02-01-i03-01': 'v02-01-i03-01'}},
                         None]),
                    ('/branch02/b02-01/[2]/name', ['n02-01-i03', None]),
                    ('/branch02/b02-01/[2]/value',
                        [{'b02-01-i03-01': 'v02-01-i03-01'}, None]),
                    ('/branch02/b02-01/[2]/value/b02-01-i03-01',
                        ['v02-01-i03-01', None])]
        assert diff.search('//', details=True, dump_mode='removed') == expected

    def test_dump_as_structure_two_bulk_removed(
            self, original_branch, changed_branch_01):
        diff = changed_branch_01 - original_branch
        expected = [[1, None],
                    [{'name': 'n02-01-i03',
                      'value': {'b02-01-i03-01': 'v02-01-i03-01'}},
                     None]]
        assert diff.search('//', dump_mode='bulk_removed') == expected

    def test_dump_as_structure_two_bulk_removed_details(
            self, original_branch, changed_branch_01):
        diff = changed_branch_01 - original_branch
        expected = [('/branch01/b01-02', [1, None]),
                    ('/branch02/b02-01/[2]',
                       [{'name': 'n02-01-i03',
                         'value': {'b02-01-i03-01': 'v02-01-i03-01'}},
                         None])]
        assert diff.search('//', details=True, dump_mode='bulk_removed') == expected

    def test_dump_as_structure_two_changed(
            self, original_branch, changed_branch_01):
        diff = changed_branch_01 - original_branch
        expected = [['string', 'changed'],
                    ['n02-01-i02-01-i03', 'changed'],
                    ['v02-01-i02-01-i03', 'changed']]
        assert diff.search('//', dump_mode='changed') == expected

    def test_dump_as_structure_two_changed_details(
            self, original_branch, changed_branch_01):
        diff = changed_branch_01 - original_branch
        expected = [('/branch01/b01-01', ['string', 'changed']),
                    ('/branch02/b02-01/[1]/value/b02-01-i02-01/[2]/name',
                       ['n02-01-i02-01-i03', 'changed']),
                    ('/branch02/b02-01/[1]/value/b02-01-i02-01/[2]/value',
                        ['v02-01-i02-01-i03', 'changed'])]
        assert diff.search('//', details=True, dump_mode='changed') == expected

    def test_dump_as_structure_multi_dump_mode(
            self, original_branch, changed_branch_01, changed_branch_02):
        diff = diffjson.DiffRootBranch(
            [original_branch, changed_branch_01, changed_branch_02])
        try:
            diff.search('//', dump_mode='added')
        except TypeError as e:
            assert True
        else:
            assert False
