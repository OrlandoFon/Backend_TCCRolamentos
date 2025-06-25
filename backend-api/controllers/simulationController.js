// Camada de Controle
// Lida com requisições HTTP (req, res), interage com a camada de serviço
// e gerencia a comunicação com os clientes (SSE).
const simulationService = require("../services/simulationService");

let clients = []; // Array de clientes SSE conectados

// Função para transmitir dados para todos os clientes conectados
function broadcast(data) {
  clients.forEach((client) =>
    client.res.write(`data: ${JSON.stringify(data)}\n\n`),
  );
}

// Listener para os eventos emitidos pelo serviço de simulação
simulationService.on("data", (dataBuffer) => {
  const lines = dataBuffer
    .toString()
    .split("\n")
    .filter((line) => line.trim() !== "");
  lines.forEach((line) => {
    try {
      const jsonData = JSON.parse(line);
      broadcast(jsonData);
    } catch (e) {
      console.warn("Saída não-JSON do Python (stdout):", line);
      broadcast({ type: "log_python", channel: "stdout", message: line });
    }
  });
});

simulationService.on("error", (errorData) => {
  const message = errorData.toString();
  console.error(`Erro do Python (stderr): ${message}`);
  broadcast({ type: "error_python", channel: "stderr", message });
});

simulationService.on("end", (endMessage) => {
  broadcast(endMessage);
});

// Funções do Controller
exports.handleSse = (req, res) => {
  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");
  res.flushHeaders();

  const clientId = Date.now();
  clients.push({ id: clientId, res });
  console.log(`Cliente ${clientId} conectado.`);

  req.on("close", () => {
    clients = clients.filter((c) => c.id !== clientId);
    console.log(`Cliente ${clientId} desconectado.`);
  });
};

exports.startSimulation = (req, res) => {
  try {
    const { bearingName } = req.body;
    const basePath =
      req.body.basePath ||
      "/media/orlandofonsecad/SSD_NOVO/TCC_Engenharia/Dataset/XJTU-SY_Bearing_Datasets/XJTU-SY_Bearing_Datasets/Data/XJTU-SY_Bearing_Datasets";
    if (!bearingName) {
      return res.status(400).json({ error: "bearingName é obrigatório." });
    }
    const result = simulationService.start(bearingName, basePath);
    res.json(result);
  } catch (error) {
    res.status(error.statusCode || 500).json({ error: error.message });
  }
};

exports.stopSimulation = (req, res) => {
  const result = simulationService.stop();
  res.json(result);
};

exports.getAvailableBearings = (req, res) => {
  // Idealmente, esta lista viria do próprio script Python ou de um arquivo de config compartilhado.
  const bearingsList = [
    { name_in_code: "Bearing1_2", article_id_display: "Artigo B1 (C1)" },
    { name_in_code: "Bearing1_3", article_id_display: "Artigo B2 (C1)" },
    { name_in_code: "Bearing2_1", article_id_display: "Artigo B3 (C2)" },
    { name_in_code: "Bearing2_2", article_id_display: "Artigo B4 (C2)" },
    { name_in_code: "Bearing3_3", article_id_display: "Artigo B5 (C3)" },
    { name_in_code: "Bearing3_4", article_id_display: "Artigo B6 (C3)" },
  ].map((b) => ({
    value: b.name_in_code,
    label: `${b.article_id_display} (${b.name_in_code})`,
  }));
  res.json(bearingsList);
};
