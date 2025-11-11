// server.js
import express from "express";
import cors from "cors";
import fetch from "node-fetch"; // or global fetch in Node 18+

const app = express();
app.use(cors());
app.use(express.json());

// 👇 Forward frontend data to Flask
app.post("/api/estimate", async (req, res) => {
  try {
    const flaskResponse = await fetch("http://localhost:5001/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req.body),
    });

    const cost = await flaskResponse.json();
    res.json(cost);
  } catch (err) {
    console.error("Error contacting Flask API:", err);
    res.status(500).json({ error: "Failed to contact prediction service" });
  }
});

const PORT = 4000;
app.listen(PORT, () => console.log(`🚀 Express server running on port ${PORT}`));
