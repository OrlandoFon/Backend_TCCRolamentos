# Camada de Acesso a Dados (Repository Pattern)
# Abstrai a forma como os dados dos rolamentos são obtidos (neste caso, de arquivos CSV).
# A lógica de negócio não precisa saber sobre caminhos de arquivo ou formato de dados.

import pandas as pd
import numpy as np
import os
import config
import processing

class BearingDataRepository:
    """
    O Repositório para obter dados de rolamentos. Encapsula toda a lógica de acesso
    aos arquivos do dataset.
    """
    def __init__(self, base_path: str):
        """
        Inicializa o repositório com o caminho base do dataset.
        Args:
            base_path (str): O caminho raiz para a pasta do dataset XJTU-SY.
        """
        self.base_path = base_path

    def get_bearing_metadata(self, bearing_name: str) -> dict | None:
        """Retorna os metadados de um rolamento específico."""
        return config.ARTICLE_BEARINGS_MAP.get(bearing_name)

    def get_all_article_bearings_metadata(self) -> list[dict]:
        """Retorna os metadados de todos os rolamentos listados no artigo."""
        return config.ARTICLE_BEARINGS_DATA

    def get_num_files_for_bearing(self, bearing_name: str) -> int | None:
        """Retorna o número total de arquivos para um rolamento."""
        return config.NUM_FILES_DICT_FULL.get(bearing_name)

    def get_signal_for_minute(self, condition: str, bearing_name: str, minute: int) -> np.ndarray | None:
        """
        Busca, lê e pré-processa o sinal de um rolamento para um minuto específico.
        Retorna o sinal em m/s^2 ou None se o arquivo não for encontrado.
        """
        try:
            file_path = os.path.join(self.base_path, condition, bearing_name, f"{minute}.csv")
            df = pd.read_csv(file_path, header=None, skiprows=1)

            # Converte para numpy, aplica aceleração da gravidade e garante tipo float
            sig = pd.to_numeric(df.iloc[:, 0], errors='coerce').dropna().to_numpy(np.float32) * config.GRAV_ACCEL

            # Garante que o sinal tenha o comprimento esperado (padding ou truncating)
            if len(sig) < config.EXPECTED_LEN:
                sig = np.pad(sig, (0, config.EXPECTED_LEN - len(sig)), 'constant', constant_values=0)
            elif len(sig) > config.EXPECTED_LEN:
                sig = sig[:config.EXPECTED_LEN]

            return sig
        except FileNotFoundError:
            return None
        except Exception:
            # Captura outras exceções de leitura de arquivo ou processamento
            return None

class CustomFDTBearingDataRepository(BearingDataRepository):
    """
    Um Repositório de Dados de Rolamento estendido que calcula o FDT
    dinamicamente usando a função 'detect_fdt' em vez de valores de configuração.
    """
    def __init__(self, base_path: str, fdt_params: dict = None):
        """
        Inicializa o repositório CustomFDT.
        Args:
            base_path (str): O caminho raiz para a pasta do dataset XJTU-SY.
            fdt_params (dict, optional): Parâmetros para a função detect_fdt
                                         (e.g., {'warmup': 3, 'persistence_len': 3, 'amp_offset': 0.02}).
                                         Se None, usará valores padrão.
        """
        super().__init__(base_path)
        # Define parâmetros padrão para detect_fdt
        self.fdt_params = fdt_params if fdt_params is not None else {
            'warmup': 3,
            'persistence_len': 3,
            'amp_offset': 0.02
        }

    def calculate_fdt(self, bearing_name: str) -> int | None:
        """
        Calcula o FDT para um rolamento específico usando a função detect_fdt.
        Este método requer a coleta de todos os dados de espectro de envelope (AES)
        para o rolamento em questão antes de calcular o FDT.

        Args:
            bearing_name (str): O nome do rolamento para o qual o FDT será calculado.

        Returns:
            int | None: O minuto de detecção de falha (índice baseado em 0) ou None se não for detectado.
        """
        metadata = self.get_bearing_metadata(bearing_name)
        if not metadata:
            print(f"Metadados não encontrados para o rolamento: {bearing_name}. Não é possível calcular FDT.")
            return None

        condition = metadata["condition_key"]
        num_files = self.get_num_files_for_bearing(bearing_name)
        if not num_files:
            print(f"Nenhum arquivo encontrado para o rolamento: {bearing_name}. Não é possível calcular FDT.")
            return None

        all_aes_amplitudes = []
        aes_frequencies = None # Para armazenar o vetor de frequências uma vez

        L_aes, overlap_aes = 8192, 2048 # Parâmetros para compute_aes, podem vir do config ou ser otimizados

        print(f"Iniciando coleta de dados para cálculo de FDT para {bearing_name}...")
        for minute in range(1, num_files + 1):
            signal = self.get_signal_for_minute(condition, bearing_name, minute)
            if signal is not None:
                try:
                    env = processing.get_envelope_from_signal(signal)
                    S_e_amp, f_aes = processing.compute_aes(env, config.FS, L_aes, overlap_aes)
                    all_aes_amplitudes.append(S_e_amp)
                    if aes_frequencies is None:
                        aes_frequencies = f_aes
                except Exception as e:
                    print(f"Erro ao processar minuto {minute} para {bearing_name}: {e}")
                    # Em caso de erro, adicione um array de zeros para manter o shape, ou trate como NaN
                    # Para FDT, é melhor ter um valor para representar a ausência/erro
                    all_aes_amplitudes.append(np.zeros_like(aes_frequencies) if aes_frequencies is not None else np.zeros(L_aes // 2))
            else:
                print(f"Arquivo não encontrado para {bearing_name}, minuto {minute}. Pulando.")
                # Adiciona um array de zeros se o arquivo não for encontrado
                all_aes_amplitudes.append(np.zeros_like(aes_frequencies) if aes_frequencies is not None else np.zeros(L_aes // 2))

        if not all_aes_amplitudes or aes_frequencies is None:
            print(f"Nenhum dado de espectro de envelope válido coletado para {bearing_name}. Não é possível calcular FDT.")
            return None

        # Converte a lista de amplitudes para um array NumPy 2D
        # np.vstack empilha arrays ao longo do primeiro eixo (linhas)
        full_amps_matrix = np.vstack(all_aes_amplitudes)

        # Prepara o dicionário de resultados para detect_fdt
        detection_results = {
            'aes_frequencies': aes_frequencies,
            'aes_amplitudes': full_amps_matrix,
            'fcf': config.FCFS[condition]
        }
        print(f"Calculando FDT para {bearing_name} com {full_amps_matrix.shape[0]} minutos de dados...")
        fdt, _, _ = processing.detect_fdt(detection_results, **self.fdt_params)

        print(f"FDT calculado para {bearing_name}: {fdt} minutos.")
        return fdt
