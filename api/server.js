import express from "express";
import cors from "cors";
import fetch from "node-fetch";

const app = express();
app.use(cors());
app.use(express.json());

// Ensure PORT exists (required for Docker & ECS)
const PORT = process.env.PORT || 4000;

// 👇 Forward frontend data to Flask
app.post("/api/estimate", async (req, res) => {
  try {
    const flaskResponse = await fetch("http://flask-api.backend.local:5001/predict", {
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

// Start server

app.get("/health", (req, res) => {
  res.status(200).json({ status: "ok" });
});


app.listen(PORT, "0.0.0.0", () => {
  console.log(`🚀 Express server running on port ${PORT}`);
});
