# Sensitivity Analysis


It is also possible to create an ensemble simulation with different
completion designs by calling Completor® with a case file template in
the RMS workflow.

Under “Internal variables” in the ERT configuration file define
\<RMS_WF_NAME\> to PRED_COMPLETOR. Set up a Completor® template case
file with parameter variables instead of fixed variables
(*../ert/input/config/op5_template.case* shown as an example below). Set
up a parameter distribution by using a design matrix (for sensitivity
analysis, see example setup in design_input_completor.xlsx) or GEN_KW
(for uncertainty analysis, which may not be relevant with regards to
well completion).

The file to be used for input of the design matrix is
*../input/distributions/completordesignmatrix.xlsx*.
