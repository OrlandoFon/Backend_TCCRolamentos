# Camada de Aplicação/Orquestração
# Contém a lógica de alto nível que orquestra a simulação, usando as outras camadas.
import numpy as np
import pandas as pd
import json
import time

# Importa os módulos refatorados
import config
import processing
from repository import BearingDataRepository, CustomFDTBearingDataRepository

class BearingSimulator:
    """
    Orquestra a simulação de prognóstico para um rolamento.
    Usa o Repository para buscar dados e o módulo de Processing para os cálculos.
    """
    def __init__(self, bearing_name: str, repository: BearingDataRepository):
        self.bearing_name = bearing_name
        self.repository = repository

        self.metadata = self.repository.get_bearing_metadata(bearing_name)
        if not self.metadata:
            raise ValueError(f"Metadados não encontrados para o rolamento: {bearing_name}")

        self.condition = self.metadata["condition_key"]
        self.num_files = self.repository.get_num_files_for_bearing(bearing_name)

        # Estado da simulação
        self.all_esi_raw = []
        self.all_esi_smoothed = []

    def _calculate_gamma_bar(self) -> float:
        """Calcula o valor de limiar gamma_bar, usado como critério de falha."""
        max_esis = []
        L_gamma, overlap_gamma = 8192, 2048

        for condition, bearings in config.BEARINGS_FOR_GAMMA_BAR_CALC.items():
            for bearing_name in bearings:
                num_files = self.repository.get_num_files_for_bearing(bearing_name)
                if not num_files: continue

                esi_vals = []
                for k in range(1, num_files + 1):
                    sig = self.repository.get_signal_for_minute(condition, bearing_name, k)
                    if sig is None: continue

                    env = processing.get_envelope_from_signal(sig)
                    S_e, f_aes = processing.compute_aes(env, config.FS, L_gamma, overlap_gamma)
                    esi = processing.compute_esi(S_e, f_aes, condition)
                    esi_vals.append(esi)

                if esi_vals:
                    max_esis.append(np.max(esi_vals))

        if not max_esis:
            raise RuntimeError("Falha fatal ao calcular gamma_bar. Nenhum dado de ESI foi gerado.")

        return np.mean(max_esis)

    def run_incremental_simulation(self):
        """
        Executa a simulação passo a passo (minuto a minuto) e 'yields' (gera)
        os resultados em formato JSON. Este é um gerador.
        """
        gamma_bar = self._calculate_gamma_bar()

        t_fdt = self.metadata["t_fdt"]
        t_start_ekf_idx = max(0, (t_fdt - config.N_PRIOR_FDT) - 1)

        L_rul, overlap_rul = 8192, int(8192 * 0.25)

        for minute in range(1, self.num_files + 1):
            minute_idx = minute - 1
            esi_raw_current = np.nan
            error_msg = None

            signal = self.repository.get_signal_for_minute(self.condition, self.bearing_name, minute)

            if signal is not None:
                try:
                    env = processing.get_envelope_from_signal(signal)
                    S_e_amp, f_aes = processing.compute_aes(env, config.FS, L_rul, overlap_rul)
                    esi_raw_current = processing.compute_esi(S_e_amp, f_aes, self.condition)
                except Exception as e:
                    error_msg = str(e)
            else:
                error_msg = "file_not_found"

            self.all_esi_raw.append(esi_raw_current if not np.isnan(esi_raw_current) else 0.0)

            # Suavização com média móvel
            series_to_smooth = pd.Series(self.all_esi_raw).fillna(0)
            smoothed_series = series_to_smooth.rolling(window=4, center=True, min_periods=1).mean().to_numpy()
            self.all_esi_smoothed = list(smoothed_series)
            esi_smoothed_current = self.all_esi_smoothed[minute_idx]

            # Gera o resultado do ESI para o minuto atual
            esi_output = {
                "type": "esi", "bearing": self.bearing_name, "minute": minute,
                "value_raw_ms2": float(esi_raw_current) if not np.isnan(esi_raw_current) else None,
                "value_raw_g": float(esi_raw_current / config.GRAV_ACCEL) if not np.isnan(esi_raw_current) else None,
                "value_smoothed_ms2": float(esi_smoothed_current),
                "value_smoothed_g": float(esi_smoothed_current / config.GRAV_ACCEL),
                "error": error_msg
            }
            yield json.dumps(esi_output)

            # Condição para calcular o RUL a cada 3 minutos após o início do EKF
            should_calculate_rul = (minute_idx > t_start_ekf_idx) and (minute % 3 == 0)

            if should_calculate_rul:
                current_esi_series = np.array(self.all_esi_smoothed[:minute])

                rul_results, _, _, _ = processing.run_ekf_and_get_rul(
                    current_esi_series, t_start_ekf_idx, [minute], gamma_bar,
                    self.metadata["vt"], self.metadata["wt"], len(current_esi_series)
                )
                rul_val = rul_results[0, 0]

                rul_output = {
                    "type": "rul", "bearing": self.bearing_name, "minute": minute,
                    "rul_predicted_min": float(rul_val) if not np.isnan(rul_val) and not np.isinf(rul_val) else None,
                    "is_inf": bool(np.isinf(rul_val)),
                    "is_nan": bool(np.isnan(rul_val))
                }
                yield json.dumps(rul_output)

            time.sleep(10) # Delay opcional

        yield json.dumps({"type": "status", "status": "completed", "bearing": self.bearing_name})

class CustomFDTBearingSimulator(BearingSimulator):
    """
    Um Simulador de Rolamento que utiliza um CustomFDTBearingDataRepository
    para calcular o FDT dinamicamente, em vez de usar um valor predefinido.
    """
    def __init__(self, bearing_name: str, base_path: str, fdt_params: dict = None):
        """
        Inicializa o CustomFDTBearingSimulator.
        Cria uma instância de CustomFDTBearingDataRepository e a injeta na classe base.

        Args:
            bearing_name (str): Nome do rolamento a ser processado.
            base_path (str): Caminho base para o dataset XJTU-SY.
            fdt_params (dict, optional): Parâmetros para a função detect_fdt
                                         (e.g., {'warmup': 3, 'persistence_len': 3, 'amp_offset': 0.02}).
                                         Se None, usará valores padrão.
        """
        # Cria a instância do repositório personalizado que calcula o FDT
        custom_repo = CustomFDTBearingDataRepository(base_path, fdt_params)
        super().__init__(bearing_name, custom_repo)
        self.custom_repo = custom_repo # Armazena para acesso direto se necessário

    def _get_fdt_for_simulation(self) -> int:
        """
        Sobrescreve o método da classe base para obter o FDT calculado
        pelo CustomFDTBearingDataRepository.
        """
        print(f"Obtendo FDT dinâmico para {self.bearing_name}...")
        fdt = self.custom_repo.calculate_fdt(self.bearing_name)
        if fdt is None:
            raise RuntimeError(f"Não foi possível calcular o FDT dinamicamente para {self.bearing_name}.")
        return fdt
