import pytest
import yaml
import diffjson


class TestBranch(object):
    @pytest.fixture
    def original_data(self, shared_datadir):
        return yaml.safe_load((shared_datadir / 'original.yaml').read_text())

    @pytest.fixture
    def original_branch(self, shared_datadir):
        data = yaml.safe_load((shared_datadir / 'original.yaml').read_text())
        return diffjson.generate_branch(data)

    @pytest.fixture
    def childbranch_01(self, original_branch):
        lp_str = '/branch01'
        lp = diffjson.parse(lp_str)
        return original_branch.raw_search(lp)[0]

    @pytest.fixture
    def childbranch_01_01(self, original_branch):
        lp_str = '/branch01/b01-01'
        lp = diffjson.parse(lp_str)
        return original_branch.raw_search(lp)[0]

    @pytest.fixture
    def childbranch_02(self, original_branch):
        lp_str = '/branch02'
        lp = diffjson.parse(lp_str)
        return original_branch.raw_search(lp)[0]

    @pytest.fixture
    def childbranch_02_01(self, original_branch):
        lp_str = '/branch02/b02-01'
        lp = diffjson.parse(lp_str)
        return original_branch.raw_search(lp)[0]

    ###########################################################
    # Functions for Development
    ###########################################################
    def test_generate_branch(self, original_data):
        try:
            b = diffjson.generate_branch(original_data)
        except Exception as e:
            raise e

    def test_locationpath(self, childbranch_01_01):
        value = childbranch_01_01.locationpath
        assert isinstance(value, diffjson.LocationPath)
        assert str(value) == '/branch01/b01-01'

    def test_parent(self, childbranch_01_01):
        # This test uses locationpath.
        # So can be failed with test_locationpath.
        value = childbranch_01_01.parent
        assert isinstance(value, diffjson.DictBranch)
        assert str(value.locationpath) == '/branch01'

    def test_childnodenames(self, childbranch_01):
        expected = {'b01-01', 'b01-02', 'b01-03', 'b01-04'}
        value = childbranch_01.childnodenames
        bnns = set([str(bnn) for bnn in value])
        assert bnns == expected

    def test_childbranches(self, childbranch_01):
        expected = {'string', 1, 2.0, True}
        value = childbranch_01.childbranches
        branches = set([branch.dump() for branch in value])
        assert branches == expected

    def test_descendants(self, childbranch_02):
        expected = [
            [
                {'name': 'n02-01-i01', 'value': 'v02-01-i01'},
                {'name': 'n02-01-i02', 'value': {'b02-01-i02-01': [{'name': 'n02-01-i02-01-i01', 'value': 'v02-01-i02-01-i01'}, {'name': 'n02-01-i02-01-i02', 'value': 'v02-01-i02-01-i02'}, {'name': 'n02-01-i02-01-i03', 'value': 'v02-01-i02-01-i03'}], 'b02-01-i02-02': {'name': 'n02-01-i02-02', 'value': 'v02-01-i02-02'}}}, {'name': 'n02-01-i03', 'value': {'b02-01-i03-01': 'v02-01-i03-01'}}
            ],
            {'name': 'n02-01-i01', 'value': 'v02-01-i01'},
            {'name': 'n02-01-i02', 'value': {'b02-01-i02-01': [{'name': 'n02-01-i02-01-i01', 'value': 'v02-01-i02-01-i01'}, {'name': 'n02-01-i02-01-i02', 'value': 'v02-01-i02-01-i02'}, {'name': 'n02-01-i02-01-i03', 'value': 'v02-01-i02-01-i03'}], 'b02-01-i02-02': {'name': 'n02-01-i02-02', 'value': 'v02-01-i02-02'}}},
            {'name': 'n02-01-i03', 'value': {'b02-01-i03-01': 'v02-01-i03-01'}},
            'n02-01-i01',
            'v02-01-i01',
            'n02-01-i02',
            {'b02-01-i02-01': [{'name': 'n02-01-i02-01-i01', 'value': 'v02-01-i02-01-i01'}, {'name': 'n02-01-i02-01-i02', 'value': 'v02-01-i02-01-i02'}, {'name': 'n02-01-i02-01-i03', 'value': 'v02-01-i02-01-i03'}], 'b02-01-i02-02': {'name': 'n02-01-i02-02', 'value': 'v02-01-i02-02'}},
            [{'name': 'n02-01-i02-01-i01', 'value': 'v02-01-i02-01-i01'}, {'name': 'n02-01-i02-01-i02', 'value': 'v02-01-i02-01-i02'}, {'name': 'n02-01-i02-01-i03', 'value': 'v02-01-i02-01-i03'}],
            {'name': 'n02-01-i02-02', 'value': 'v02-01-i02-02'},
            {'name': 'n02-01-i02-01-i01', 'value': 'v02-01-i02-01-i01'},
            {'name': 'n02-01-i02-01-i02', 'value': 'v02-01-i02-01-i02'},
            {'name': 'n02-01-i02-01-i03', 'value': 'v02-01-i02-01-i03'},
            'n02-01-i02-01-i01',
            'v02-01-i02-01-i01',
            'n02-01-i02-01-i02',
            'v02-01-i02-01-i02',
            'n02-01-i02-01-i03',
            'v02-01-i02-01-i03',
            'n02-01-i02-02',
            'v02-01-i02-02',
            'n02-01-i03',
            {'b02-01-i03-01': 'v02-01-i03-01'},
            'v02-01-i03-01'
        ]
        value = childbranch_02.descendants
        data = [branch.dump() for branch in value]
        assert data == expected

    def test_rootbranch(self, childbranch_01_01):
        value = childbranch_01_01.rootbranch
        assert isinstance(value, diffjson.RootBranch)

    def test_nodename(self, childbranch_01_01):
        value = childbranch_01_01.nodename
        assert value == diffjson.NodenameKey('b01-01')

    def test_getitem_dict(self, childbranch_01):
        value = childbranch_01['b01-01']
        assert value == 'string'

    def test_getitem_item(self, childbranch_02_01):
        value = childbranch_02_01[0]
        assert value == {'name': 'n02-01-i01', 'value': 'v02-01-i01'}

    def test_childbranch(self, childbranch_01):
        expected = diffjson.parse('/branch01/b01-01')
        bnn = diffjson.NodenameKey('b01-01')
        value = childbranch_01.childbranch(bnn)
        assert value.locationpath == expected

    def test_isat(self, childbranch_01_01):
        assert childbranch_01_01.isat('/branch01/b01-01')

    ###########################################################
    # Functions for Users
    ###########################################################
    def test_search_direct(self, original_branch):
        value = original_branch.search('/branch01/b01-01')
        assert len(value) == 1
        assert value[0] == 'string'

    def test_search_direct_index(self, original_branch):
        value = original_branch.search('/branch02/b02-01[0]/value')
        assert len(value) == 1
        assert value[0] == 'v02-01-i01'

    def test_search_direct_dict(self, original_branch, original_data):
        value = original_branch.search('/branch01')
        assert len(value) == 1
        assert value[0] == original_data['branch01']

    def test_search_descendant(self, original_branch):
        value = original_branch.search('/branch02//b02-01-i03-01')
        assert len(value) == 1
        assert value[0] == 'v02-01-i03-01'

    def test_search_descendant_root(self, original_branch):
        value = original_branch.search('//b01-01')
        assert len(value) == 1
        assert value[0] == 'string'

    def test_search_detail(self, original_branch):
        value = original_branch.search('/branch02//b02-01-i03-01', details=True)
        assert len(value) == 1
        assert value[0][0] == '/branch02/b02-01/[2]/value/b02-01-i03-01'
        assert value[0][1] == 'v02-01-i03-01'

    def test_search_with_pedicates_01(self, original_branch, original_data):
        value = original_branch.search('/branch01[b01-01="string"]')
        assert len(value) == 1
        assert value[0] == original_data['branch01']

    def test_search_with_pedicates_02(self, original_branch, original_data):
        value = original_branch.search('/branch01[b01-01="not match"]')
        assert len(value) == 0

    def test_set(self, original_branch):
        original_branch.set('/branch01/b01-01', 'changed')
        value = original_branch.search('/branch01/b01-01')
        assert len(value) == 1
        assert value[0] == 'changed'

    def test_set_dict(self, original_branch):
        original_branch.set('/branch01/b01-01', {'b01-01-new': 'dict'})
        value = original_branch.search('/branch01/b01-01/b01-01-new')
        assert len(value) == 1
        assert value[0] == 'dict'

    def test_setdefault_exist(self, original_branch):
        original_branch.setdefault('/branch01', 'b01-01', 'changed')
        value = original_branch.search('/branch01/b01-01')
        assert len(value) == 1
        assert value[0] == 'string'

    def test_setdefault_noexist(self, original_branch):
        original_branch.setdefault('/branch01', 'b01-99', 'new')
        value = original_branch.search('/branch01/b01-99')
        assert len(value) == 1
        assert value[0] == 'new'

    def test_setdefault_noexist_dict(self, original_branch):
        original_branch.setdefault('/branch01', 'b01-99', {'b01-99-01': 'new'})
        value = original_branch.search('/branch01/b01-99/b01-99-01')
        assert len(value) == 1
        assert value[0] == 'new'

    def test_insert_01(self, original_branch):
        original_branch.insert('/branch02/b02-01', 0, 'insert')
        value = original_branch.search('/branch02/b02-01/[0]')
        value1 = original_branch.search('/branch02/b02-01/[1]/name')
        assert len(value) == 1
        assert value[0] == 'insert'
        assert len(value1) == 1
        assert value1[0] == 'n02-01-i01'

    def test_insert_02(self, original_branch):
        original_branch.insert('/branch02/b02-01', 1, 'insert')
        value = original_branch.search('/branch02/b02-01/[1]')
        value0 = original_branch.search('/branch02/b02-01/[0]/name')
        value2 = original_branch.search('/branch02/b02-01/[2]/name')
        assert len(value) == 1
        assert value[0] == 'insert'
        assert len(value0) == 1
        assert value0[0] == 'n02-01-i01'
        assert len(value2) == 1
        assert value2[0] == 'n02-01-i02'

    def test_insert_03(self, original_branch):
        original_branch.insert('/branch02/b02-01', 3, 'insert')
        value0 = original_branch.search('/branch02/b02-01/[0]/name')
        value2 = original_branch.search('/branch02/b02-01/[2]/name')
        value = original_branch.search('/branch02/b02-01/[3]')
        assert len(value) == 1
        assert value[0] == 'insert'
        assert len(value0) == 1
        assert value0[0] == 'n02-01-i01'
        assert len(value2) == 1
        assert value2[0] == 'n02-01-i03'

    def test_insert_04(self, original_branch):
        original_branch.insert('/branch02/b02-01', 4, 'insert')
        value0 = original_branch.search('/branch02/b02-01/[0]/name')
        value2 = original_branch.search('/branch02/b02-01/[2]/name')
        value = original_branch.search('/branch02/b02-01/[3]')
        # Insert accepts index more than length and add data at the last index.
        value4 = original_branch.search('/branch02/b02-01/[4]')
        assert len(value) == 1
        assert value[0] == 'insert'
        assert len(value0) == 1
        assert value0[0] == 'n02-01-i01'
        assert len(value2) == 1
        assert value2[0] == 'n02-01-i03'
        assert len(value4) == 0

    def test_bundle(self, original_branch):
        pass

    def test_pop(self, original_branch, original_data):
        poped = original_branch.pop('/branch01/b01-01')
        value = original_branch.search('/branch01/b01-01')
        assert len(value) == 0
        assert len(poped) == 1
        assert poped[0] == original_data['branch01']['b01-01']

    def test_remove(self, original_branch):
        original_branch.remove('/branch01/b01-01')
        value = original_branch.search('/branch01/b01-01')
        assert len(value) == 0

