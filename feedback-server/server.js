const express = require("express");
const bodyParser = require("body-parser");
const cors = require("cors");

const app = express();
app.use(cors());
app.use(bodyParser.json());

let reviews = [];

// 피드백 데이터를 저장하는 엔드포인트
app.post("/feedback", (req, res) => {
  const { rating, comment, recipe } = req.body;
  reviews.push({ rating, comment, recipe });
  res.status(200).send("Feedback received");
});

// 저장된 피드백 데이터를 불러오는 엔드포인트
app.get("/reviews", (req, res) => {
  res.json(reviews);
});

const port = process.env.PORT || 3000;
app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});
