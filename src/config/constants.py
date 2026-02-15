"""
PLC-specific constants and enumerations
"""
from enum import Enum


class PLCInstruction(str, Enum):
    """Common PLC ladder logic instructions"""
    XIC = "XIC"  # Examine If Closed (normally open contact)
    XIO = "XIO"  # Examine If Open (normally closed contact)
    OTE = "OTE"  # Output Energize
    OTL = "OTL"  # Output Latch
    OTU = "OTU"  # Output Unlatch
    TON = "TON"  # Timer On-Delay
    TOF = "TOF"  # Timer Off-Delay
    CTU = "CTU"  # Count Up
    CTD = "CTD"  # Count Down
    RES = "RES"  # Reset


class TagType(str, Enum):
    """PLC tag data types"""
    BOOL = "BOOL"
    SINT = "SINT"
    INT = "INT"
    DINT = "DINT"
    REAL = "REAL"
    TIMER = "TIMER"
    COUNTER = "COUNTER"


class RockwellProcessorType(str, Enum):
    """Supported Rockwell PLC processor types"""
    COMPACTLOGIX_L18 = "1769-L18ER-BB1B"
    COMPACTLOGIX_L24 = "1769-L24ER-QB1B"
    COMPACTLOGIX_L33 = "1769-L33ER"
    CONTROLLOGIX_L71 = "1756-L71"
    CONTROLLOGIX_L82 = "1756-L82E"


# CSV Column Headers
CSV_HEADERS = {
    "LOGIC": "Logic",
    "DESCRIPTION": "LogicDescription",
    "INTERLOCK1": "Interlock1",
    "INTERLOCK2": "Interlock2",
    "INTERLOCK3": "Interlock3",
    "INTERLOCK4": "Interlock4",
    "INTERLOCK5": "Interlock5",
    "CONDITION": "Condition",
    "NEXT_LOGIC": "Logic",  # Last column
}

# Special interlock values
ALWAYS_ON = "AlwaysOn"
NO_INTERLOCK_VALUES = ["", ALWAYS_ON, None]

# L5X XML Namespaces
L5X_SCHEMA_VERSION = "1.0"
L5X_DEFAULT_SOFTWARE_REV = "33.00"

# File size limits (bytes)
MAX_CSV_SIZE = 5 * 1024 * 1024  # 5MB
MAX_L5X_SIZE = 50 * 1024 * 1024  # 50MB

# Validation constants
MAX_STATES_PER_MACHINE = 100
MAX_INTERLOCKS_PER_STATE = 10
MAX_MACHINE_NAME_LENGTH = 100
