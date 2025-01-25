from utz import YM

ym0 = YM(202212)


def test_constructors():
    for ym in [
        YM('202212'),
        YM('2022-12'),
        YM(2022, 12),
        YM(y=2022, m=12),
        YM(dict(year=2022, month=12)),
        YM(YM(202212)),
    ]:
        assert ym == ym0


def test_subtract_ints():
    ym0 = YM(202212)
    assert ym0 -  1 == YM(202211)
    assert ym0 -  2 == YM(202210)
    assert ym0 - 11 == YM(202201)
    assert ym0 - 12 == YM(202112)
    assert ym0 - 13 == YM(202111)
    assert ym0 - 23 == YM(202101)
    assert ym0 - 24 == YM(202012)
    assert ym0 - 25 == YM(202011)


def test_subtract_yms():
    for ym1, diff in {
        YM(202401): -13,
        YM(202312): -12,
        YM(202311): -11,
        YM(202302): -2,
        YM(202301): -1,
        YM(202212): 0,
        YM(202211): 1,
        YM(202210): 2,
        YM(202201): 11,
        YM(202112): 12,
    }.items():
        assert ym0 - ym1 == diff
        assert ym1 - ym0 == -diff


def test_add_ints():
    assert ym0 +  1 == YM(202301)
    assert ym0 +  2 == YM(202302)
    assert ym0 + 11 == YM(202311)
    assert ym0 + 12 == YM(202312)
    assert ym0 + 13 == YM(202401)
    assert ym0 + 23 == YM(202411)
    assert ym0 + 24 == YM(202412)
    assert ym0 + 25 == YM(202501)


def test_until():
    assert list(ym0.until(YM(202201))) == []
    assert list(ym0.until(YM(202211))) == []
    assert list(ym0.until(YM(202212))) == []
    assert list(ym0.until(YM(202301))) == [ YM(202212) ]
    assert list(ym0.until(YM(202302))) == [ YM(202212), YM(202301) ]
    assert list(ym0.until(YM(202402))) == [
        YM(ym)
        for ym in [
            202212,
            202301, 202302, 202303, 202304, 202305, 202306, 202307, 202308, 202309, 202310, 202311, 202312,
            202401,
        ]
    ]


def test_to():
    assert list(ym0.to(YM(202201))) == []
    assert list(ym0.to(YM(202211))) == []
    assert list(ym0.to(YM(202212))) == [ YM(202212) ]
    assert list(ym0.to(YM(202301))) == [ YM(202212), YM(202301) ]
    assert list(ym0.to(YM(202401))) == [
        YM(ym)
        for ym in [
            202212,
            202301, 202302, 202303, 202304, 202305, 202306, 202307, 202308, 202309, 202310, 202311, 202312,
            202401,
        ]
    ]
