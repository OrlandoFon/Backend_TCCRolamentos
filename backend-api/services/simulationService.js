// Camada de Serviço
// Encapsula a lógica de negócio do backend, como o gerenciamento do processo filho.
const { spawn } = require("child_process");
const path = require("path");
const { EventEmitter } = require("events");

class SimulationService extends EventEmitter {
  constructor() {
    super();
    this.pythonProcess = null;
    this.currentBearing = null;
  }

  start(bearingName, basePath) {
    if (this.pythonProcess) {
      const error = new Error("Uma simulação já está em andamento.");
      error.statusCode = 409; // Conflict
      throw error;
    }

    const scriptPath = path.join(
      __dirname,
      "..",
      "..",
      "python-engine",
      "main.py",
    );
    const args = [
      scriptPath,
      bearingName,
      "--base_path",
      basePath,
      "--use_custom_fdt",
    ];
    // const args = [scriptPath, bearingName, "--base_path", basePath];

    console.log(`Iniciando: python3 ${args.join(" ")}`);
    this.pythonProcess = spawn("python3", args);
    this.currentBearing = bearingName;

    // Emite eventos que o controller pode ouvir
    this.pythonProcess.stdout.on("data", (data) => this.emit("data", data));
    this.pythonProcess.stderr.on("data", (data) => this.emit("error", data));
    this.pythonProcess.on("close", (code) => this.handleClose(code));
    this.pythonProcess.on("error", (err) => this.handleProcessError(err));

    return { message: `Simulação para ${bearingName} iniciada.` };
  }

  stop() {
    if (!this.pythonProcess) {
      return { message: "Nenhuma simulação em andamento para parar." };
    }
    console.log("Comando de parada enviado para a simulação.");
    this.pythonProcess.kill("SIGINT"); // Envia sinal para encerramento
    return { message: "Comando de parada enviado." };
  }

  handleClose(code) {
    console.log(
      `Processo Python para ${this.currentBearing} finalizado com código ${code}`,
    );
    const message = {
      type: "simulation_end",
      bearing: this.currentBearing,
      code: code,
    };
    this.emit("end", message);
    this.pythonProcess = null;
    this.currentBearing = null;
  }

  handleProcessError(err) {
    console.error("Falha ao iniciar o processo Python:", err);
    const systemError = {
      type: "error_system",
      message: `Falha ao iniciar Python: ${err.message}`,
    };
    this.emit("error", systemError);
    this.pythonProcess = null;
    this.currentBearing = null;
  }
}

// Singleton: garante que haja apenas uma instância do serviço na aplicação
module.exports = new SimulationService();
