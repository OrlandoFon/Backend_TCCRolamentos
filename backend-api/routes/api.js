// Camada de Roteamento
// Mapeia os endpoints da API para as funções do controller correspondente.
const express = require("express");
const router = express.Router();
const controller = require("../controllers/simulationController");

router.get("/events", controller.handleSse);
router.post("/start-simulation", controller.startSimulation);
router.get("/stop-simulation", controller.stopSimulation);
router.get("/bearings", controller.getAvailableBearings);

module.exports = router;
