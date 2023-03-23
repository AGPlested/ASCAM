DEFAULT_GAUSS_CUTOFF_FREQ = 1000

AMPERE_UNIT_FACTORS = {"fA": 1e15, "pA": 1e12, "nA": 1e9, "µA": 1e6, "mA": 1e3, "A": 1}
VOLTAGE_UNIT_FACTORS = {"uV": 1e6, "mV": 1e3, "V": 1}
TIME_UNIT_FACTORS = {"us": 1e6, "ms": 1e3, "s": 1}

PRECISIONS = {
    "us": 0,
    "ms": 3,
    "s": 6,
    "fA": 0,
    "pA": 3,
    "nA": 6,
    "uA": 9,
    "mA": 12,
    "A": 15,
    "uV": 3,
    "mV": 6,
    "V": 9,
    "int": 0,
}

ANALYSIS_FRAME_WIDTH = 250

TEST_FILE_NAME = "181010007_max_bursts_conc.axgx"
TEST_FILE_NAME = "GluA2_T1_SC-recording_40kHzSR.mat"
