from utz import YM


def test_ym():
    ym0 = YM(202212)
    for ym in [ YM('202212'), YM(2022, 12), YM('2022', '12') ]:
        assert ym == ym0

    assert ym0 -  1 == YM(202211)
    assert ym0 -  2 == YM(202210)
    assert ym0 - 11 == YM(202201)
    assert ym0 - 12 == YM(202112)
    assert ym0 - 13 == YM(202111)
    assert ym0 - 23 == YM(202101)
    assert ym0 - 24 == YM(202012)
    assert ym0 - 25 == YM(202011)

    assert ym0 +  1 == YM(202301)
    assert ym0 +  2 == YM(202302)
    assert ym0 + 11 == YM(202311)
    assert ym0 + 12 == YM(202312)
    assert ym0 + 13 == YM(202401)
    assert ym0 + 23 == YM(202411)
    assert ym0 + 24 == YM(202412)
    assert ym0 + 25 == YM(202501)
