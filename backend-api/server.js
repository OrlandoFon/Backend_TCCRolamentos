// Ponto de Entrada do Servidor Node.js
// Responsável pela configuração inicial do Express, middlewares e rotas.
const express = require("express");
const cors = require("cors");
const apiRoutes = require("./routes/api");

const app = express();
const PORT = process.env.PORT || 3001;

// Middlewares
app.use(cors());
app.use(express.json());

// Monta as rotas da API sob o prefixo /api
app.use("/api", apiRoutes);

app.listen(PORT, () => {
  console.log(`Servidor Node.js (API) rodando na porta ${PORT}`);
});
