# Módulo de Configuração
# Centraliza todas as constantes e parâmetros globais da simulação para fácil manutenção.

# Parâmetros de Sinal
FS = 25600  # Frequência de amostragem
EXPECTED_LEN = 32768  # Comprimento esperado do sinal
GRAV_ACCEL = 9.81  # Aceleração da gravidade

# Parâmetros de Simulação
N_PRIOR_FDT = 10  # Número de minutos antes do FDT para iniciar o EKF

# Dicionários de Metadados
BEARINGS_FOR_GAMMA_BAR_CALC = {
    "35Hz12kN": ["Bearing1_2", "Bearing1_3"],
    "37.5Hz11kN": ["Bearing2_1", "Bearing2_2"],
    "40Hz10kN": ["Bearing3_3", "Bearing3_4"],
}

FCFS = { # Frequências Características de Falha (FCFs)
    "35Hz12kN": {"FTF": 13.49, "BSF": 72.33, "BPFO": 107.91, "BPFI": 172.09},
    "37.5Hz11kN": {"FTF": 14.45, "BSF": 77.50, "BPFO": 115.62, "BPFI": 184.38},
    "40Hz10kN": {"FTF": 15.42, "BSF": 82.66, "BPFO": 123.32, "BPFI": 196.68},
}

NUM_FILES_DICT_FULL = {
    "Bearing1_1": 123, "Bearing1_2": 161, "Bearing1_3": 158, "Bearing1_4": 122, "Bearing1_5": 52,
    "Bearing2_1": 491, "Bearing2_2": 161, "Bearing2_3": 533, "Bearing2_4": 42, "Bearing2_5": 339,
    "Bearing3_1": 2538, "Bearing3_2": 2496, "Bearing3_3": 371, "Bearing3_4": 1515, "Bearing3_5": 114,
}

ARTICLE_BEARINGS_DATA = [
    {"name_in_code": "Bearing1_2", "condition_key": "35Hz12kN", "article_id_display": "Artigo B1 (C1)", "t_fdt": 35, "t_eol_true": 126, "vt": 0.1, "wt": 0.05},
    {"name_in_code": "Bearing1_3", "condition_key": "35Hz12kN", "article_id_display": "Artigo B2 (C1)", "t_fdt": 59, "t_eol_true": 151, "vt": 0.1, "wt": 0.05},
    {"name_in_code": "Bearing2_1", "condition_key": "37.5Hz11kN", "article_id_display": "Artigo B3 (C2)", "t_fdt": 446, "t_eol_true": 490, "vt": 0.02, "wt": 0.05},
    {"name_in_code": "Bearing2_2", "condition_key": "37.5Hz11kN", "article_id_display": "Artigo B4 (C2)", "t_fdt": 47, "t_eol_true": 160, "vt": 0.05, "wt": 0.08},
    {"name_in_code": "Bearing3_3", "condition_key": "40Hz10kN", "article_id_display": "Artigo B5 (C3)", "t_fdt": 327, "t_eol_true": 353, "vt": 0.1, "wt": 0.1},
    {"name_in_code": "Bearing3_4", "condition_key": "40Hz10kN", "article_id_display": "Artigo B6 (C3)", "t_fdt": 1418, "t_eol_true": 1478, "vt": 0.1, "wt": 0.1},
]
ARTICLE_BEARINGS_MAP = {b["name_in_code"]: b for b in ARTICLE_BEARINGS_DATA}
