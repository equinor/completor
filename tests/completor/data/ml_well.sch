-- Two-branch well schedule for testing the LATERAL_TO_DEVICE keyword

WELSPECS
A1   MYGRP 35  113  0.0   OIL   1*   STD   SHUT   YES   1   AVG   1* /
/

COMPDAT
--WELL                      I     J    K1    K2 OP/SH  SATN       TRAN      WBDIA         KH       SKIN DFACT   DIR      PEQVR
-------------------------------------------------------------------------------------------------------------------------------
 'A1'       35   113    72    72  OPEN    1* 298.626067     0.2159 196217.868         30    1*     Y 19.6401168 /
 'A1'       36   113    72    72  OPEN    1* 387.741486     0.2159 254075.894         30    1*     Y 17.8369894 /
 'A1'       36   113    71    71  OPEN    1* 756.259143     0.2159 213444.014         30    1*     Y  17.491487 /
 'A1'       36   112    71    71  OPEN    1* 1532.59635     0.2159 605308.261         30    1*     X 18.4455805 /
 'A1'       37   112    71    71  OPEN    1* 1990.18841     0.2159 904540.837         30    1*     X 18.6760813 /
 'A1'       37   111    71    71  OPEN    1* 381.965616     0.2159 92974.6543         30    1*     Y 17.5695899 /
 'A1'       37   111    72    72  OPEN    1* 1265.79866     0.2159 215551.216         30    1*     Y 19.1801227 /
 'A1'       37   113    71    71  OPEN    1* 571.056866     0.2159 374227.512         30    1*     X 17.8877638 /
 'A1'       40   111    71    71  OPEN    1* 1647.17097     0.2159 1081814.52         30    1*     X 19.3295074 /
 'A1'       41   111    71    71  OPEN    1* 41.1143925     0.2159 26954.1235         30    1*     X 18.1426592 /
 'A1'       41   111    72    72  OPEN    1* 667.083084     0.2159 438514.751         30    1*     X 19.9505785 /
/

WELSEGS
--WELL                        TDEP       CLEN        VOL  TYPE DROPT MPMOD
 'A1'     1565.2834       1893         1*   ABS   HF-    HO /
--------------------------------------------------------------------------------
-- Branch 1
--------------------------------------------------------------------------------
--SEGS  SEGE BRNCH  SEGJ       CLEN       NDEP       TDIA      ROUGH       AREA
     2     2     1     1       1902 1565.66813      0.159    0.00065         1* /
     3     3     1     2 1941.57416  1566.9189      0.159    0.00065         1* /
     4     4     1     3       1951 1567.21681      0.159    0.00065         1* /
     5     5     1     4 2051.55974 1567.81871      0.159    0.00065         1* /
     6     6     1     5 2167.24558 1566.40678      0.159    0.00065         1* /
     7     7     1     6 2228.00876 1566.16386      0.159    0.00065         1* /
     8     8     1     7 2284.47304 1565.75703      0.159    0.00065         1* /
     9     9     1     8 2371.86609 1565.39687      0.159    0.00065         1* /
    10    10     1     9 2485.43321 1565.64975      0.159    0.00065         1* /
    11    11     1    10 2553.16429 1565.90086      0.159    0.00065         1* /
    12    12     1    11 2603.01001 1566.47477      0.159    0.00065         1* /
 --------------------------------------------------------------------------------
-- Branch 2
--------------------------------------------------------------------------------
--SEGS  SEGE BRNCH  SEGJ       CLEN       NDEP       TDIA      ROUGH       AREA
    72    72     2     9 2371.96452 1565.55903      0.159    0.00065         1* /
    73    73     2    72 2433.98323 1565.62271      0.159    0.00065         1* /
    74    74     2    73 2487.82912 1566.87804      0.159    0.00065         1* /
    75    75     2    74 2509.71419 1568.13253      0.159    0.00065         1* /
    76    76     2    75 2531.24472 1569.29279      0.159    0.00065         1* /
    77    77     2    76 2616.72782 1570.45891      0.159    0.00065         1* /
    78    78     2    77 2698.49266  1570.3235      0.159    0.00065         1* /
    79    79     2    78 2720.76145 1569.82458      0.159    0.00065         1* /
    80    80     2    79 2757.71512 1569.01476      0.159    0.00065         1* /
    81    81     2    80 2809.16035 1566.86658      0.159    0.00065         1* /
    82    82     2    81 2840.81312 1565.70046      0.159    0.00065         1* /
    83    83     2    82 2936.66149 1565.50831      0.159    0.00065         1* /
    84    84     2    83 3023.34594 1565.99544      0.159    0.00065         1* /
    85    85     2    84 3040.54736 1566.11034      0.159    0.00065         1* /
/

COMPSEGS
 'A1' /
--   I     J     K BRNCH       MD_S       MD_E   DIR IJK_E       CDEP  CLEN SEGNO
    35   113    72     1   2178.280   2202.052    1*    1*  1566.2504    1*     6 /
    36   113    72     1   2202.052   2253.965    1*    1* 1566.09798    1*     7 /
    36   113    71     1   2253.965   2314.981    1*    1* 1565.75725    1*     8 /
    36   112    71     1   2314.981   2428.752    1*    1* 1565.56616    1*     9 /
    37   112    71     1   2428.752   2542.115    1*    1* 1565.72385    1*    10 /
    37   111    71     1   2542.115   2564.214    1*    1* 1565.91116    1*    11 /
    37   111    72     1   2564.214   2595.450    1*    1* 1566.18029    1*    12 /
    37   113    71     2   2340.228   2399.701    1*    1* 1565.53372    1*    72 /
    40   111    71     2   2854.970   3022.127    1*    1* 1565.72782    1*    83 /
    41   111    71     2   3022.127   3024.565    1*    1*  1565.9954    1*    84 /
    41   111    72     2   3024.565   3056.530    1*    1* 1566.11559    1*    85 /
/