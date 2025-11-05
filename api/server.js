import express from "express";
import cors from "cors";

const app = express();
app.use(cors());
app.use(express.json()); // parse JSON bodies

// Example endpoint to receive answers
app.post("/api/estimate", async (req, res) => {
  const answers = req.body;

  console.log("Received answers from frontend:", answers);

  try {
    // If your Python API is running locally:
    const response = await fetch("http://127.0.0.1:5000/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(answers),
    });

    const data = await response.json();
    res.json(data); // forward Python API response to frontend
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Failed to connect to Python API" });
  }
});

app.listen(4000, () => console.log("✅ Express server running on port 4000"));
