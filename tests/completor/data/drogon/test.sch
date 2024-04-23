WELSPECS
  --WELL   GROUP  IHEEL JHEEL       DREF PHASE       DRAD INFEQ SIINS XFLOW PRTAB  DENS
   'A1' 'DUMMY'    28    37 1575.81971   OIL         1*    1*  SHUT    1*    1*    1* /
  /

COMPORD
 'A1'  INPUT /
/

COMPDAT
-------------------------------------------------------------------------------------------
-- Well : A1 : Lateral : 1
-------------------------------------------------------------------------------------------
-- WELL   I   J   K   K2 FLAG  SAT CF          DIAM  KH          SKIN DFACT DIR  RO
    A1  28  37   1   1  OPEN  1* 1.27194551  0.311  114.88788  0.0   1*    X   19.652259  /
    A1  28  37   2   2  OPEN  1* 3.67578858  0.311 336.318088  0.0   1*    X   20.924668  /
    A1  28  37   3   3  OPEN  1* 7.92025953  0.311 727.803499  0.0   1*    X   21.373217  /
    A1  28  37   4   4  OPEN  1* 118.349656  0.311 9740.10833  0.0   1*    X   12.784487  /
    A1  28  37   5   5  OPEN  1* 294.985871  0.311  26721.376  0.0   1*    X   19.928724  /
    A1  28  37   6   6  OPEN  1* 5.28790464  0.311 471.168716  0.0   1*    X   18.407388  /
    A1  28  38   6   6  OPEN  1* 40.4257482  0.311 3312.19194  0.0   1*    X   12.535772  /
    A1  28  38   7   7  OPEN  1* 1.70716613  0.311 150.795009  0.0   1*    X   17.661088  /
    A1  28  38   8   8  OPEN  1* 2.21198615  0.311 192.036154  0.0   1*    X   16.284687  /
    A1  29  38   8   8  OPEN  1* 2.78513556  0.311 239.344926  0.0   1*    X   15.535037  /
    A1  29  38   9   9  OPEN  1* 5.42614956  0.311 463.609065  0.0   1*    X   15.127031  /
    A1  29  38  10  10  OPEN  1* 3.26152723  0.311  276.59607  0.0   1*    X   14.621753  /
    A1  29  39   8   8  OPEN  1* 10.8601698  0.311 875.395434  0.0   1*    Y   11.675669  /
    A1  30  39   8   8  OPEN  1* 33.2444313  0.311 2789.98421  0.0   1*    Y   13.946626  /
    A1  30  39   7   7  OPEN  1* 14.3361235  0.311  1076.6418  0.0   1*    Y    8.692897  /
    A1  30  39   6   6  OPEN  1* 10.9829068  0.311 884.536241  0.0   1*    X   11.632887  /
    A1  30  39   5   5  OPEN  1* 11.8553141  0.311 1025.28895  0.0   1*    X   15.997006  /
    A1  30  40   5   5  OPEN  1* 41.2833991  0.311 3573.62275  0.0   1*    X   16.065460  /
    A1  31  40   5   5  OPEN  1* 69.2228715  0.311 5543.59781  0.0   1*    Y   11.353216  /
    A1  31  40   4   4  OPEN  1* 270.569974  0.311 23121.8021  0.0   1*    Y   15.140099  /
    A1  31  41   4   4  OPEN  1* 68.2881225  0.311 5444.96789  0.0   1*    Y   11.143431  /
    A1  32  41   4   4  OPEN  1* 97.0857644  0.311 7704.03241  0.0   1*    Y   10.917474  /
    A1  32  41   5   5  OPEN  1* 49.9299583  0.311 3823.22019  0.0   1*    Y    9.406092  /
    A1  32  41   6   6  OPEN  1* 1.99590293  0.311 169.511142  0.0   1*    Y   14.719107  /
    A1  32  42   6   6  OPEN  1* 31.0570356  0.311 2642.66942  0.0   1*    Y   14.846855  /
    A1  32  42   7   7  OPEN  1* 10.2562712  0.311  855.75701  0.0   1*    Y   13.588228  /
    A1  33  42   7   7  OPEN  1* 19.5588571  0.311 1663.51215  0.0   1*    Y   14.815672  /
    A1  33  42   8   8  OPEN  1* 45.7100801  0.311 3897.80845  0.0   1*    Y   14.991981  /
    A1  33  43   8   8  OPEN  1* 16.3874512  0.311 1399.32541  0.0   1*    Y   15.086781  /
/


WELSEGS
-- WELL   SEGMENTTVD  SEGMENTMD WBVOLUME INFOTYPE PDROPCOMP MPMODEL
    A1  0.0         0.0        1*       ABS      HF-       HO      /
---------------------------------------------------------------
-- Well : A1 : Lateral : 1 : Tubing layer
---------------------------------------------------------------
--  SEG  SEG2  BRANCH  OUT MD       TVD       DIAM ROUGHNESS
     2    2    1        1  2371.596 1577.726  0.15 0.00065    /
     3    3    1        2  2381.708 1581.539  0.15 0.00065    /
     4    4    1        3  2391.834 1585.358  0.15 0.00065    /
     5    5    1        4  2402.215 1589.201  0.15 0.00065    /
     6    6    1        5  2413.230 1593.026  0.15 0.00065    /
     7    7    1        6  2419.746 1595.162  0.15 0.00065    /
     8    8    1        7  2425.809 1597.064  0.15 0.00065    /
     9    9    1        8  2438.314 1600.723  0.15 0.00065    /
    10   10    1        9  2450.446 1603.903  0.15 0.00065    /
    11   11    1       10  2468.742 1608.086  0.15 0.00065    /
    12   12    1       11  2538.718 1616.383  0.15 0.00065    /
    13   13    1       12  2626.385 1618.627  0.15 0.00065    /
    14   14    1       13  2680.837 1620.095  0.15 0.00065    /
    15   15    1       14  2717.512 1621.083  0.15 0.00065    /
    16   16    1       15  2762.839 1622.305  0.15 0.00065    /
    17   17    1       16  2823.756 1623.947  0.15 0.00065    /
    18   18    1       17  2862.442 1624.989  0.15 0.00065    /
    19   19    1       18  2905.477 1626.149  0.15 0.00065    /
    20   20    1       19  2984.406 1628.276  0.15 0.00065    /
    21   21    1       20  3058.393 1630.270  0.15 0.00065    /
    22   22    1       21  3128.915 1632.171  0.15 0.00065    /
    23   23    1       22  3186.551 1633.724  0.15 0.00065    /
    24   24    1       23  3248.668 1635.398  0.15 0.00065    /
    25   25    1       24  3298.664 1636.746  0.15 0.00065    /
    26   26    1       25  3337.500 1637.792  0.15 0.00065    /
    27   27    1       26  3389.861 1639.204  0.15 0.00065    /
    28   28    1       27  3424.949 1640.149  0.15 0.00065    /
    29   29    1       28  3479.908 1641.630  0.15 0.00065    /
    30   30    1       29  3530.864 1643.004  0.15 0.00065    /
---------------------------------------------------------------
-- Well : A1 : Lateral : 1 : Device layer
---------------------------------------------------------------
--  SEG  SEG2  BRANCH  OUT MD       TVD       DIAM ROUGHNESS
    31   31     2       2  2371.696 1577.726  0.15 0.00065    / -- AICD types
    32   32     3       3  2381.808 1581.539  0.15 0.00065    / -- AICD types
    33   33     4       4  2391.934 1585.358  0.15 0.00065    / -- AICD types
    34   34     5       5  2402.315 1589.201  0.15 0.00065    / -- AICD types
    35   35     6       6  2413.330 1593.026  0.15 0.00065    / -- AICD types
    36   36     7       7  2419.846 1595.162  0.15 0.00065    / -- AICD types
    37   37     8       8  2425.909 1597.064  0.15 0.00065    / -- AICD types
    38   38     9       9  2438.414 1600.723  0.15 0.00065    / -- AICD types
    39   39    10      10  2450.546 1603.903  0.15 0.00065    / -- AICD types
    40   40    11      11  2468.842 1608.086  0.15 0.00065    / -- AICD types
    41   41    12      12  2538.818 1616.383  0.15 0.00065    / -- AICD types
    42   42    13      13  2626.485 1618.627  0.15 0.00065    / -- AICD types
    43   43    14      14  2680.937 1620.095  0.15 0.00065    / -- AICD types
    44   44    15      15  2717.612 1621.083  0.15 0.00065    / -- AICD types
    45   45    16      16  2762.939 1622.305  0.15 0.00065    / -- AICD types
    46   46    17      17  2823.856 1623.947  0.15 0.00065    / -- AICD types
    47   47    18      18  2862.542 1624.989  0.15 0.00065    / -- AICD types
    48   48    19      19  2905.577 1626.149  0.15 0.00065    / -- AICD types
    49   49    20      20  2984.506 1628.276  0.15 0.00065    / -- AICD types
    50   50    21      21  3058.493 1630.270  0.15 0.00065    / -- AICD types
    51   51    22      22  3129.015 1632.171  0.15 0.00065    / -- AICD types
    52   52    23      23  3186.651 1633.724  0.15 0.00065    / -- AICD types
    53   53    24      24  3248.768 1635.398  0.15 0.00065    / -- AICD types
    54   54    25      25  3298.764 1636.746  0.15 0.00065    / -- AICD types
    55   55    26      26  3337.600 1637.792  0.15 0.00065    / -- AICD types
    56   56    27      27  3389.961 1639.204  0.15 0.00065    / -- AICD types
    57   57    28      28  3425.049 1640.149  0.15 0.00065    / -- AICD types
    58   58    29      29  3480.008 1641.630  0.15 0.00065    / -- AICD types
    59   59    30      30  3530.964 1643.004  0.15 0.00065    / -- AICD types
/


COMPSEGS
A1 /
-------------------------------------------------------
-- Well : A1 : Lateral : 1
-------------------------------------------------------
--  I   J   K   BRANCH STARTMD  ENDMD    DIR DEF  SEG
    28  37   1   2     2366.541 2376.651  1*  3*  31   /
    28  37   2   3     2376.651 2386.766  1*  3*  32   /
    28  37   3   4     2386.766 2396.902  1*  3*  33   /
    28  37   4   5     2396.902 2407.527  1*  3*  34   /
    28  37   5   6     2407.527 2418.933  1*  3*  35   /
    28  37   6   7     2418.933 2420.559  1*  3*  36   /
    28  38   6   8     2420.559 2431.058  1*  3*  37   /
    28  38   7   9     2431.058 2445.570  1*  3*  38   /
    28  38   8  10     2445.570 2455.323  1*  3*  39   /
    29  38   8  11     2455.323 2482.161  1*  3*  40   /
    29  38   9  12     2482.161 2595.275  1*  3*  41   /
    29  38  10  13     2595.275 2657.496  1*  3*  42   /
    29  39   8  14     2657.496 2704.177  1*  3*  43   /
    30  39   8  15     2704.177 2730.846  1*  3*  44   /
    30  39   7  16     2730.846 2794.831  1*  3*  45   /
    30  39   6  17     2794.831 2852.681  1*  3*  46   /
    30  39   5  18     2852.681 2872.203  1*  3*  47   /
    30  40   5  19     2872.203 2938.751  1*  3*  48   /
    31  40   5  20     2938.751 3030.062  1*  3*  49   /
    31  40   4  21     3030.062 3086.725  1*  3*  50   /
    31  41   4  22     3086.725 3171.104  1*  3*  51   /
    32  41   4  23     3171.104 3201.998  1*  3*  52   /
    32  41   5  24     3201.998 3295.338  1*  3*  53   /
    32  41   6  25     3295.338 3301.991  1*  3*  54   /
    32  42   6  26     3301.991 3373.010  1*  3*  55   /
    32  42   7  27     3373.010 3406.712  1*  3*  56   /
    33  42   7  28     3406.712 3443.186  1*  3*  57   /
    33  42   8  29     3443.186 3516.629  1*  3*  58   /
    33  43   8  30     3516.629 3545.098  1*  3*  59   /
/


WSEGAICD
-------------------------------------------------------------------------------------------------------------------
-- Well : A1 : Lateral : 1
-------------------------------------------------------------------------------------------------------------------
-- WELL   SEG  SEG2 ALPHA      SF              RHO     VIS DEF  X     Y    FLAG   A    B    C    D     E     F
    A1  31   31   1.7253e-05  -0.1978192407  1025.0  1.0  5*  3.05  0.67  OPEN  1.0  1.0  1.0  2.43  1.18  2.1  /
    A1  32   32   1.7253e-05  -0.1977394427  1025.0  1.0  5*  3.05  0.67  OPEN  1.0  1.0  1.0  2.43  1.18  2.1  /
    A1  33   33   1.7253e-05  -0.1973083199  1025.0  1.0  5*  3.05  0.67  OPEN  1.0  1.0  1.0  2.43  1.18  2.1  /
    A1  34   34   1.7253e-05  -0.1882292708  1025.0  1.0  5*  3.05  0.67  OPEN  1.0  1.0  1.0  2.43  1.18  2.1  /
    A1  35   35   1.7253e-05  -0.1753493836  1025.0  1.0  5*  3.05  0.67  OPEN  1.0  1.0  1.0  2.43  1.18  2.1  /
    A1  36   36   1.7253e-05    -1.23012578  1025.0  1.0  5*  3.05  0.67  OPEN  1.0  1.0  1.0  2.43  1.18  2.1  /
    A1  37   37   1.7253e-05  -0.1904914298  1025.0  1.0  5*  3.05  0.67  OPEN  1.0  1.0  1.0  2.43  1.18  2.1  /
    A1  38   38   1.7253e-05  -0.1378216326  1025.0  1.0  5*  3.05  0.67  OPEN  1.0  1.0  1.0  2.43  1.18  2.1  /
    A1  39   39   1.7253e-05  -0.2050569084  1025.0  1.0  5*  3.05  0.67  OPEN  1.0  1.0  1.0  2.43  1.18  2.1  /
    A1  40   40   1.7253e-05 -0.07452072924  1000.0  1.0  5*  3.05  0.67  OPEN  1.0  1.0  1.0  2.43  1.18  2.1  /
    A1  41   41   1.7253e-05 -0.01768133826  1000.0  1.0  5*  3.05  0.67  OPEN  1.0  1.0  1.0  2.43  1.18  2.1  /
    A1  42   42   1.7253e-05 -0.03214341621  1000.0  1.0  5*  3.05  0.67  OPEN  1.0  1.0  1.0  2.43  1.18  2.1  /
    A1  43   43   1.7253e-05 -0.04284373583  1000.0  1.0  5*  3.05  0.67  OPEN  1.0  1.0  1.0  2.43  1.18  2.1  /
    A1  44   44   1.7253e-05 -0.07499366304  1000.0  1.0  5*  3.05  0.67  OPEN  1.0  1.0  1.0  2.43  1.18  2.1  /
    A1  45   45   1.7253e-05   -0.031257238  1000.0  1.0  5*  3.05  0.67  OPEN  1.0  1.0  1.0  2.43  1.18  2.1  /
    A1  46   46   1.7253e-05 -0.03457212757  1000.0  1.0  5*  3.05  0.67  OPEN  1.0  1.0  1.0  2.43  1.18  2.1  /
    A1  47   47   1.7253e-05  -0.1024494118  1000.0  1.0  5*  3.05  0.67  OPEN  1.0  1.0  1.0  2.43  1.18  2.1  /
    A1  48   48   1.7253e-05 -0.03005367135  1000.0  1.0  5*  3.05  0.67  OPEN  1.0  1.0  1.0  2.43  1.18  2.1  /
    A1  49   49   1.7253e-05 -0.02190324766  1000.0  1.0  5*  3.05  0.67  OPEN  1.0  1.0  1.0  2.43  1.18  2.1  /
    A1  50   50   1.7253e-05 -0.03529603401  1000.0  1.0  5*  3.05  0.67  OPEN  1.0  1.0  1.0  2.43  1.18  2.1  /
    A1  51   51   1.7253e-05 -0.02370251542  1000.0  1.0  5*  3.05  0.67  OPEN  1.0  1.0  1.0  2.43  1.18  2.1  /
    A1  52   52   1.7253e-05 -0.06473755234  1000.0  1.0  5*  3.05  0.67  OPEN  1.0  1.0  1.0  2.43  1.18  2.1  /
    A1  53   53   1.7253e-05 -0.02142704322  1000.0  1.0  5*  3.05  0.67  OPEN  1.0  1.0  1.0  2.43  1.18  2.1  /
    A1  54   54   1.7253e-05  -0.3006429249  1000.0  1.0  5*  3.05  0.67  OPEN  1.0  1.0  1.0  2.43  1.18  2.1  /
    A1  55   55   1.7253e-05 -0.02816131534  1000.0  1.0  5*  3.05  0.67  OPEN  1.0  1.0  1.0  2.43  1.18  2.1  /
    A1  56   56   1.7253e-05     -0.0593438  1000.0  1.0  5*  3.05  0.67  OPEN  1.0  1.0  1.0  2.43  1.18  2.1  /
    A1  57   57   1.7253e-05 -0.05483364022  1000.0  1.0  5*  3.05  0.67  OPEN  1.0  1.0  1.0  2.43  1.18  2.1  /
    A1  58   58   1.7253e-05 -0.02723199563  1000.0  1.0  5*  3.05  0.67  OPEN  1.0  1.0  1.0  2.43  1.18  2.1  /
    A1  59   59   1.7253e-05 -0.07025074246  1000.0  1.0  5*  3.05  0.67  OPEN  1.0  1.0  1.0  2.43  1.18  2.1  /
/