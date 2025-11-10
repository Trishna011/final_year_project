import express from "express";
import cors from "cors";

const app = express();
app.use(cors());
app.use(express.json());

app.post("/api/estimate", (req, res) => {
  const answers = req.body;
  console.log("📦 Received answers from frontend:", answers);

  // ✅ Send a simple JSON reply so frontend doesn't break
  res.json({ message: "Data received successfully!", received: answers });
});

const PORT = 4000;
app.listen(PORT, () => console.log(`✅ Express server running on port ${PORT}`));
