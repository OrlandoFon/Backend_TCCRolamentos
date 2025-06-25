# Ponto de Entrada Principal da Aplicação Python
# Responsável por parsear argumentos da linha de comando e iniciar a simulação.
import sys
import json
import argparse
from repository import BearingDataRepository, CustomFDTBearingDataRepository
from simulation import BearingSimulator, CustomFDTBearingSimulator

def main():
    """Função principal que executa o processo."""
    parser = argparse.ArgumentParser(description="Processa dados de rolamento incrementalmente.")
    parser.add_argument("bearing_name", help="Nome do rolamento a ser processado (ex: Bearing1_2).")
    parser.add_argument("--base_path", required=True, help="Caminho base para o dataset XJTU-SY.")
    parser.add_argument("--use_custom_fdt", action="store_true",
                        help="Usa o cálculo dinâmico de FDT ao invés do valor predefinido em config.")
    # Adicione parâmetros para o FDT customizado se quiser torná-los configuráveis via linha de comando
    parser.add_argument("--fdt_warmup", type=int, default=3,
                        help="Parâmetro 'warmup' para detect_fdt (default: 3).")
    parser.add_argument("--fdt_persistence_len", type=int, default=3,
                        help="Parâmetro 'persistence_len' para detect_fdt (default: 3).")
    parser.add_argument("--fdt_amp_offset", type=float, default=0.02,
                        help="Parâmetro 'amp_offset' para detect_fdt (default: 0.02).")

    args = parser.parse_args()

    try:
        # 1. Decidir qual repositório e simulador usar
        if args.use_custom_fdt:
            print("Usando cálculo de FDT dinâmico...")
            # Prepara os parâmetros para detect_fdt
            fdt_params = {
                'warmup': args.fdt_warmup,
                'persistence_len': args.fdt_persistence_len,
                'amp_offset': args.fdt_amp_offset
            }
            # O CustomFDTBearingSimulator já cria e gerencia seu CustomFDTBearingDataRepository
            simulator = CustomFDTBearingSimulator(args.bearing_name, args.base_path, fdt_params)
        else:
            print("Usando FDT do arquivo de configuração...")
            repo = BearingDataRepository(args.base_path)
            simulator = BearingSimulator(args.bearing_name, repo)

        # 2. Executar o gerador da simulação e imprimir cada resultado
        for result_json in simulator.run_incremental_simulation():
            print(result_json, flush=True)

    except (ValueError, RuntimeError, FileNotFoundError) as e:
        # Captura erros de configuração ou de execução e envia como um JSON de erro
        error_output = {"type": "error", "message": str(e)}
        print(json.dumps(error_output), flush=True)
        sys.exit(1)
    except Exception as e:
        # Captura qualquer outro erro inesperado
        error_output = {"type": "error", "message": f"Erro inesperado no script Python: {e}"}
        print(json.dumps(error_output), flush=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
