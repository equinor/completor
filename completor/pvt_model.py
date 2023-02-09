"""The pvt model has been removed and substituted with holdup fractions."""

# Create UDQ keyword for calculating the AICV downhole water cut.
# SUWCT UDQ correlation from SOHF and SWHF

# Downhole water cut, round it to 2 decimals by using NINT / 100
# Add tolerance 1e-20 in case it only flows gas (zero liquid rate)
CORRELATION_UDQ = """UDQ
--Water cut definition
DEFINE SUWCT NINT(SWHF*100/(SWHF+SOHF+1e-20))/100 /
/


