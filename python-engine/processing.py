# Camada de Lógica de Domínio (Processamento)
# Contém funções puras para processamento de sinal e cálculos de prognóstico (ESI, RUL).
# Essas funções não dependem de onde os dados vêm, apenas dos dados em si.

import numpy as np
from scipy.signal import butter, filtfilt, hilbert
from scipy.signal.windows import hann
import config

# Funções de cálculo (compute_aes, compute_esi, run_ekf_and_get_rul)
# As funções compute_aes e run_ekf_and_get_rul são mantidas como no original,
# mas agora recebem todos os parâmetros de que precisam, em vez de usar globais.

def compute_aes(env, fs_signal, L, overlap, use_hanning_window=False):
    # (Mesmo código da função original, sem alterações na lógica interna)
    step = L - overlap
    if len(env) < L: env = np.pad(env, (0, L - len(env)), 'constant', constant_values=0)
    if step <= 0:
        if L > 0 : step = L
        else: return np.array([]), np.array([])

    Ns = (len(env) - L) // step + 1
    if Ns <= 0: Ns = 1

    power_spec_sum = np.zeros(L)
    window = np.ones(L)
    if use_hanning_window: window = hann(L, sym=False)

    actual_segments_processed = 0
    for s_idx in range(Ns):
        seg_start, seg_end = s_idx * step, s_idx * step + L
        current_seg = env[seg_start : seg_end]
        if len(current_seg) < L: current_seg = np.pad(current_seg, (0, L - len(current_seg)), 'constant', constant_values=0)

        windowed_seg = current_seg * window
        power_spec_segment = np.abs(np.fft.fft(windowed_seg))**2 / (L**2)
        power_spec_sum += power_spec_segment
        actual_segments_processed +=1

    if actual_segments_processed == 0: avg_power_spec_scaled = np.zeros(L // 2)
    else: avg_power_spec_scaled = (power_spec_sum / actual_segments_processed)[:L//2]

    avg_amplitude_spec_unscaled = np.sqrt(np.maximum(0, avg_power_spec_scaled))
    final_amplitude_spec = np.copy(avg_amplitude_spec_unscaled)
    if len(final_amplitude_spec) > 1: final_amplitude_spec[1:] = 2 * final_amplitude_spec[1:]

    freq_vector = np.arange(L//2) * fs_signal / L
    return final_amplitude_spec, freq_vector


def compute_esi(S_e_amplitude, f_vector, condition, N_harm=3, bw=0):
    # (Mesmo código da função original, sem alterações na lógica interna)
    esi_val = 0.0
    fcf_values = config.FCFS[condition]
    if len(S_e_amplitude) == 0 or len(f_vector) == 0: return 0.0

    for n_h in range(1, N_harm + 1):
        for fcf_type in ["FTF", "BSF", "BPFO", "BPFI"]:
            target_freq = n_h * fcf_values[fcf_type]
            if len(f_vector) == 0: continue

            idx = np.argmin(np.abs(f_vector - target_freq))
            start_idx = max(0, idx - bw)
            end_idx = min(len(S_e_amplitude) -1 , idx + bw)

            if start_idx <= end_idx:
                esi_val += np.sum(S_e_amplitude[start_idx : end_idx + 1])
            elif start_idx == end_idx + 1 and start_idx < len(S_e_amplitude):
                 esi_val += S_e_amplitude[start_idx]
    return esi_val

def run_ekf_and_get_rul(esi_series_input, t_start_ekf, t_pts_list, gamma_bar_val,
                        vt_noise_val, wt_noise_val, num_files_bearing_total_or_upto_pt, esi_type_label=""):
    # (Mesmo código da função original, sem alterações na lógica interna)
    num_comb_val = 1
    RULs_ekf = np.zeros((num_comb_val, len(t_pts_list)))
    b_k_histories_ekf = {}
    final_b_estimates_ekf = {}
    initial_b_states_used_ekf = {}

    for c_ekf_idx in range(num_comb_val):
        z_input = esi_series_input
        if np.all(np.abs(z_input) < 1e-9 ):
            RULs_ekf[c_ekf_idx, :] = np.nan
            continue
        for pt_idx_loop, t_PT_val_loop in enumerate(t_pts_list):
            current_t_PT_idx_loop = t_PT_val_loop - 1
            if t_start_ekf >= current_t_PT_idx_loop:
                RULs_ekf[c_ekf_idx, pt_idx_loop] = np.nan
                continue
            initial_esi_state_val = z_input[t_start_ekf]
            calculated_b0_raw_val = np.nan
            initial_b_state_for_ekf_val = 0.001
            if current_t_PT_idx_loop > 0 and current_t_PT_idx_loop < len(z_input) and \
               z_input[current_t_PT_idx_loop] > 1e-9 and z_input[current_t_PT_idx_loop-1] > 1e-9:
                try:
                    if current_t_PT_idx_loop-1 >= 0 :
                        calculated_b0_raw_val = np.log(z_input[current_t_PT_idx_loop] / z_input[current_t_PT_idx_loop-1])
                        temp_b_state_val = np.abs(calculated_b0_raw_val)
                        if temp_b_state_val <= 1e-9: initial_b_state_for_ekf_val = 0.001
                        else: initial_b_state_for_ekf_val = temp_b_state_val
                    else: initial_b_state_for_ekf_val = 0.001
                except FloatingPointError: initial_b_state_for_ekf_val = 0.001
            else: initial_b_state_for_ekf_val = 0.001
            x_hat_val = np.array([initial_esi_state_val, initial_b_state_for_ekf_val])
            P_hat_val = np.diag([0.1, 0.1])
            Q_matriz_ekf_val = np.diag([vt_noise_val**2, 0.0])
            R_measurement_variance_val = wt_noise_val**2
            x_hat_iter_val, P_hat_iter_val = np.copy(x_hat_val), np.copy(P_hat_val)
            for t_idx_in_ekf_loop_val in range(t_start_ekf, current_t_PT_idx_loop):
                if x_hat_iter_val[0] <= 1e-9: break
                if t_idx_in_ekf_loop_val >= len(z_input): break
                exp_b_delta_t_val = np.exp(x_hat_iter_val[1])
                F_matrix_val = np.array([[exp_b_delta_t_val, exp_b_delta_t_val * x_hat_iter_val[0]], [0, 1]])
                x_pred_val = np.array([exp_b_delta_t_val * x_hat_iter_val[0], x_hat_iter_val[1]])
                P_pred_val = F_matrix_val @ P_hat_iter_val @ F_matrix_val.T + Q_matriz_ekf_val
                measurement_z_val = z_input[t_idx_in_ekf_loop_val]
                H_matrix_val = np.array([1.0, 0.0])
                innovation_y_val = measurement_z_val - x_pred_val[0]
                innovation_cov_S_val = H_matrix_val @ P_pred_val @ H_matrix_val.T + R_measurement_variance_val
                K_gain_val = np.zeros_like(x_hat_iter_val)
                if np.abs(innovation_cov_S_val) >= 1e-12: K_gain_val = (P_pred_val @ H_matrix_val.T) / innovation_cov_S_val
                x_hat_iter_val = x_pred_val + K_gain_val * innovation_y_val
                P_hat_iter_val = (np.eye(2) - np.outer(K_gain_val, H_matrix_val)) @ P_pred_val
            final_estimated_esi_val, final_estimated_b_val = x_hat_iter_val[0], x_hat_iter_val[1]
            if final_estimated_esi_val > 1e-9 and gamma_bar_val > 1e-9:
                if final_estimated_b_val > 1e-9:
                    if gamma_bar_val > final_estimated_esi_val:
                        RULs_ekf[c_ekf_idx, pt_idx_loop] = np.log(gamma_bar_val / final_estimated_esi_val) / final_estimated_b_val
                    else: RULs_ekf[c_ekf_idx, pt_idx_loop] = 0
                else: RULs_ekf[c_ekf_idx, pt_idx_loop] = np.inf
            else: RULs_ekf[c_ekf_idx, pt_idx_loop] = np.nan
    return RULs_ekf, b_k_histories_ekf, final_b_estimates_ekf, initial_b_states_used_ekf


def get_envelope_from_signal(signal: np.ndarray) -> np.ndarray:
    """Aplica filtro passa-alta e calcula o envelope de um sinal."""
    b_filt, a_filt = butter(4, 1000 / (config.FS / 2), btype='highpass')
    filtered_sig = filtfilt(b_filt, a_filt, signal)
    return np.abs(hilbert(filtered_sig))

def detect_fdt(results, warmup=3, persistence_len=3, amp_offset=0.02):
    """
    Detecta o Failure Detection Time (FDT) com base nas amplitudes do espectro de envelope.
    Adaptado da Seção 4.2 do artigo.

    Args:
        results (dict): Dicionário contendo 'aes_frequencies', 'aes_amplitudes' e 'fcf'.
            - 'aes_frequencies' (np.ndarray): Vetor de frequências do espectro de envelope.
            - 'aes_amplitudes' (np.ndarray): Matriz de amplitudes do espectro de envelope ao longo do tempo (minutos x frequências).
            - 'fcf' (dict): Dicionário de Frequências Características de Falha para a condição do rolamento.
        warmup (int): Número de pontos iniciais a serem ignorados para estabelecer a linha de base.
        persistence_len (int): Número de pontos consecutivos que devem exceder o limiar para acionar o FDT.
        amp_offset (float): Offset adicionado ao valor máximo da linha de base para definir o limiar de detecção.

    Returns:
        tuple: (fdt, (lo, hi), trigger)
            - fdt (int | None): O minuto de detecção de falha (índice baseado em 0), ou None se não for detectado.
            - (lo, hi) (tuple | None): Uma tupla de índices (low, high) representando a janela de tempo ao redor do FDT.
            - trigger (tuple | None): Uma tupla (componente, harmônica) que disparou o FDT, ou (None, None).
    """
    freqs = results['aes_frequencies']
    amps = results['aes_amplitudes'] # amps.shape: (N_minutos, N_frequencias)
    n_pts = amps.shape[0] # Número de minutos

    # Garante que haja dados suficientes para o warmup e persistence_len
    if n_pts < warmup + persistence_len:
        return None, (None, None), (None, None)

    fcf = results['fcf']

    series_meta = []
    # Coleta as amplitudes para as harmônicas das FCFs
    for comp, f0 in fcf.items():
        for h in (1, 2, 3): # Considera as primeiras 3 harmônicas
            target_freq = h * f0
            # Encontra o índice da frequência mais próxima
            idx = np.argmin(np.abs(freqs - target_freq))
            # Armazena a componente, harmônica e a série temporal das amplitudes para essa frequência
            series_meta.append((comp, h, amps[:, idx])) # amps[:, idx] é a série temporal para uma frequência

    # Calcula a linha de base máxima usando os primeiros 'warmup' pontos para todas as séries
    # Considera o valor máximo em todas as séries dentro do período de warmup
    base_max = max(s[:warmup].max() for _, _, s in series_meta) if series_meta else 0.0
    threshold = base_max + amp_offset

    # Cria flags booleanas onde a amplitude excede o limiar para cada série
    flags = [(s > threshold) for _, _, s in series_meta]

    fdt = None
    trigger = None
    # Itera a partir do final do período de warmup para detectar o FDT
    for start in range(warmup, n_pts - persistence_len + 1):
        # Verifica cada série para encontrar 'persistence_len' pontos consecutivos acima do limiar
        for (comp, h, _), flag in zip(series_meta, flags):
            if flag[start : start + persistence_len].all():
                fdt = start # FDT é o índice inicial da sequência que excede o limiar
                trigger = (comp, h)
                break
        if fdt is not None:
            break

    # Se FDT não foi detectado, retorna None
    if fdt is None:
        return None, (None, None), (None, None)

    # Define a janela de tempo ao redor do FDT
    lo = max(warmup, fdt - 3) # Limite inferior, garantindo que não seja antes do warmup
    hi = min(n_pts - 1, fdt + 3) # Limite superior, garantindo que não exceda o número de pontos

    return fdt, (lo, hi), trigger
