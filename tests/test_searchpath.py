import pytest
import yaml
import diffjson


class TestSearchpathClasses(object):
    def test_init_NodenameRoot(self):
        n = diffjson.NodenameRoot()
        expected = '/'
        assert str(n) == expected

    def test_init_NodenameAsterisk(self):
        n = diffjson.NodenameAsterisk()
        expected = '*'
        assert str(n) == expected

    def test_init_NodenameDescendant(self):
        n = diffjson.NodenameDescendant()
        expected = ''
        assert str(n) == expected

    def test_init_NodenameParent(self):
        n = diffjson.NodenameParent()
        expected = '..'
        assert str(n) == expected

    def test_init_NodenameSelf(self):
        n = diffjson.NodenameSelf()
        expected = '.'
        assert str(n) == expected

    def test_init_NodenameKey(self):
        n = diffjson.NodenameKey('key')
        expected = 'key'
        assert str(n) == expected

    def test_init_NodenameIndex(self):
        n = diffjson.NodenameIndex(1)
        expected = '[1]'
        assert str(n) == expected

    def test_init_LocationStep(self):
        l = diffjson.LocationStep(diffjson.NodenameRoot())
        expected = '/'
        assert str(l) == expected

    def test_init_LocationPath(self):
        lp = diffjson.LocationPath(
            [diffjson.LocationStep(diffjson.NodenameRoot())])
        expected = '/'
        assert str(lp) == expected

    def test_init_Predicate(self):
        plp = diffjson.LocationPath(
            [diffjson.LocationStep(diffjson.NodenameKey('key'))])
        p = diffjson.Predicate(plp, 'predicate')
        expected = 'key=predicate'
        assert str(p) == expected

    def test_init_LocationStepWithPredicates(self):
        plp = diffjson.LocationPath(
            [diffjson.LocationStep(diffjson.NodenameKey('key'))])
        p = diffjson.Predicate(plp, 'predicate')
        ps = diffjson.Predicates([p])
        l = diffjson.LocationStep(diffjson.NodenameRoot(), ps)
        expected = '/[key=predicate]'
        assert str(l) == expected

    # Functions
    def test_init_LocationPath_current(self):
        lp = diffjson.LocationPath([
            diffjson.LocationStep(diffjson.NodenameRoot()),
            diffjson.LocationStep(diffjson.NodenameKey('key01')),
            diffjson.LocationStep(diffjson.NodenameKey('key02')),
            ])
        expected = '/'
        assert str(lp.current()) == expected

    def test_init_LocationPath_branch(self):
        lp = diffjson.LocationPath([
            diffjson.LocationStep(diffjson.NodenameRoot()),
            diffjson.LocationStep(diffjson.NodenameKey('key01')),
            diffjson.LocationStep(diffjson.NodenameKey('key02')),
            ])
        expected = 'key01/key02'
        assert str(lp.branch()) == expected


class TestSearchpathParses(object):
    def test_parse_simple01(self):
        """
        Parser must parse input string and output appropriate LocationPath instance.

        """
        expected = diffjson.LocationPath([
            diffjson.LocationStep(diffjson.NodenameRoot()),
            diffjson.LocationStep(diffjson.NodenameKey('branch01')),
            diffjson.LocationStep(diffjson.NodenameKey('b01-01')),
        ])

        pathstring = '/branch01/b01-01'
        p = diffjson.parse(pathstring)

        assert p == expected
        assert str(p) == pathstring

    def test_parse_complex01(self):
        """
        Parser must parse input string and output appropriate LocationPath instance.

        """
        expected = diffjson.LocationPath([
            diffjson.LocationStep(diffjson.NodenameRoot()),
            diffjson.LocationStep(diffjson.NodenameKey('branch.01-02_03@example.net')),
            diffjson.LocationStep(diffjson.NodenameKey('b01-01')),
        ])

        pathstring = '/branch.01-02_03@example.net/b01-01'
        p = diffjson.parse(pathstring)

        assert p == expected
        assert str(p) == pathstring

    def test_parse_with_index(self):
        """
        Parser with NodeIndex.

        """
        expected = diffjson.LocationPath([
            diffjson.LocationStep(diffjson.NodenameRoot()),
            diffjson.LocationStep(diffjson.NodenameKey('branch01')),
            diffjson.LocationStep(diffjson.NodenameKey('b01-01')),
            diffjson.LocationStep(diffjson.NodenameIndex(1)),
            diffjson.LocationStep(diffjson.NodenameKey('b01-01-01')),
        ])

        pathstring = '/branch01/b01-01/[1]/b01-01-01'
        p = diffjson.parse(pathstring)

        assert p == expected
        assert str(p) == pathstring

    def test_parse_with_asterisk(self):
        """
        Parser with Asterisk.

        """
        expected = diffjson.LocationPath([
            diffjson.LocationStep(diffjson.NodenameRoot()),
            diffjson.LocationStep(diffjson.NodenameKey('branch01')),
            diffjson.LocationStep(diffjson.NodenameAsterisk()),
            diffjson.LocationStep(diffjson.NodenameKey('b01-01-01')),
        ])

        pathstring = '/branch01/*/b01-01-01'
        p = diffjson.parse(pathstring)

        assert p == expected
        assert str(p) == pathstring

    def test_parse_with_decendant(self):
        """
        Parser with Descendant.

        """
        expected = diffjson.LocationPath([
            diffjson.LocationStep(diffjson.NodenameRoot()),
            diffjson.LocationStep(diffjson.NodenameKey('branch01')),
            diffjson.LocationStep(diffjson.NodenameDescendant()),
            diffjson.LocationStep(diffjson.NodenameKey('branch01-01-01')),
        ])

        pathstring = '/branch01//branch01-01-01'
        p = diffjson.parse(pathstring)

        assert p == expected
        assert str(p) == pathstring

    def test_parse_with_parent(self):
        """
        Parser with Parent.

        """
        expected = diffjson.LocationPath([
            diffjson.LocationStep(diffjson.NodenameRoot()),
            diffjson.LocationStep(diffjson.NodenameKey('branch01')),
            diffjson.LocationStep(diffjson.NodenameKey('b01-01')),
            diffjson.LocationStep(diffjson.NodenameParent()),
            diffjson.LocationStep(diffjson.NodenameKey('branch01-02')),
        ])

        pathstring = '/branch01/b01-01/../branch01-02'
        p = diffjson.parse(pathstring)

        assert p == expected
        assert str(p) == pathstring

    def test_parse_with_self(self):
        """
        Parser with Self.

        """
        expected = diffjson.LocationPath([
            diffjson.LocationStep(diffjson.NodenameRoot()),
            diffjson.LocationStep(diffjson.NodenameKey('branch01')),
            diffjson.LocationStep(diffjson.NodenameSelf()),
            diffjson.LocationStep(diffjson.NodenameKey('b01-01')),
        ])

        pathstring = '/branch01/./b01-01'
        p = diffjson.parse(pathstring)

        assert p == expected
        assert str(p) == pathstring
