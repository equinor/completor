-- One-branch well schedule for testing the NaN error

WELSPECS
A1   MYGRP 35  113  0.0   OIL   1*   STD   SHUT   YES   1   AVG   1* /
/

COMPDAT                                                                                                                                                                 
--WELL                      I     J    K1    K2 OP/SH  SATN       TRAN      WBDIA         KH       SKIN DFACT   DIR      PEQVR                                          
-------------------------------------------------------------------------------------------------------------------------------                                         
 'A1'       35   113    72    72  OPEN    1* 298.626067     0.2159 196217.868         30    1*     Y  /                                        
 'A1'       36   113    72    72  OPEN    1* 387.741486     0.2159 254075.894         30    1*     Y  /                                        
/

WELSEGS                                                                                                                                                                 
--WELL                        TDEP       CLEN        VOL  TYPE DROPT MPMOD                                                                                              
 'A1'     1565.2834       1893         1*   ABS   HF-    HO /                                                                                            
--------------------------------------------------------------------------------                                                                                        
-- Branch 1: A1.A1                                                                                                                        
--------------------------------------------------------------------------------                                                                                        
--SEGS  SEGE BRNCH  SEGJ       CLEN       NDEP       TDIA      ROUGH       AREA                                                                                         
     6     6     1     5 2167.24558 1566.40678      0.159    0.00065         1* /                                                                                       
     7     7     1     6 2228.00876 1566.16386      0.159    0.00065         1* /                                                                                       
/

COMPSEGS                                                                                                                                                                
 'A1' /                                                                                                                                                  
--   I     J     K BRNCH       MD_S       MD_E   DIR IJK_E       CDEP  CLEN SEGNO                                                                                       
    35   113    72     1   2178.280   2202.052    1*    1*  1566.2504    1*     6 /                                                                                     
    36   113    72     1   2202.052   2253.965    1*    1* 1566.09798    1*     7 /                                                                                     
/

