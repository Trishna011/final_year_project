import express from "express";
import cors from "cors";
import fetch from "node-fetch";

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

app.post("/api/value", async (req, res) => {
  try {
    const flaskResponse = await fetch("http://localhost:5001/value", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req.body),
    });

    const value = await flaskResponse.json();
    res.json(value);
  } catch (err) {
    console.error("Error contacting Flask value API:", err);
    res.status(500).json({ error: "Failed to contact value service" });
  }
});


// Start server

app.get("/health", (req, res) => {
  res.status(200).json({ status: "ok" });
});


const PORT = 4000;
app.listen(PORT, () => console.log(`🚀 Express server running on port ${PORT}`));
