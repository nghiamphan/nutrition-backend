ENERGY_PROFILE_FACTOR = "energy_profile_factor"
SATURATION_PROFILE_FACTOR = "saturation_profile_factor"
SUGARS_PROFILE_FACTOR = "sugars_profile_factor"
SODIUM_PROFILE_FACTOR = "sodium_profile_factor"
MAX_ADDITIVES_PENALTY = "max_additives_penalty"
NON_ORGANIC_PENALTY = "non_organic_penalty"

ENERGY_PROFILE_FACTOR_DEFAULT_VALUE = 1
SATURATION_PROFILE_FACTOR_DEFAULT_VALUE = 1
SUGARS_PROFILE_FACTOR_DEFAULT_VALUE = 1
SODIUM_PROFILE_FACTOR_DEFAULT_VALUE = 1
MAX_ADDITIVES_PENALTY_DEFAULT_VALUE = 50
NON_ORGANIC_PENALTY_DEFAULT_VALUE = 10

# The presence of any additive in each class (no, low, moderate, high) will add the following penalty
# ONnly the penalty for the highest class is considered. For example, if a product has 1 additive in the moderate class and 1 additive in the high class, the presence penalty will be 30.
RISK_ADDITIVE_PRESENCE_PENALTY = [0, 5, 15, 30]

# The presence of each additive in each class (no, low, moderate, high) will add the following penalty
RISK_PER_ADDITIVE_PENALTY = [0, 2, 5, 10]
