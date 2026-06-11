# Article Plan: How I Predicted the World Cup Winner

## Developer Reminder
When writing the final article, replace the placeholder component's contents with plain HTML/React elements (like `<p>`, `<h3>`, `<ul>`) to display readable, editorial prose on the dedicated article page.

## Suggested Article Structure

1. **Introduction** — Why I built this model, what question it answers, and general context.
2. **The Data** — Training on 32,000+ international matches dating back to 1872, sourced from Kaggle.
3. **Feature Engineering** — Dynamically updating team Elo ratings, rolling form windows, and symmetric differences between opponent strengths.
4. **The XGBoost Model** — Training an XGBoost classifier to predict each match as a 3-class probability distribution (Win A, Draw, Win B).
5. **Probability Calibration** — Applying Platt scaling/calibration to correct raw model outputs so they act as reliable probabilities.
6. **The Monte Carlo Simulation** — Simulating the full 48-team 104-match tournament 1,000,000 times to calculate champion progression probabilities.
7. **Comparing to Opta** — Explaining why both models yielded the same top 5 favorites despite differences in underlying supercomputer methodologies.
8. **Comparing to Nate Silver** — Contrasting dynamic win probabilities (%) with static Elo-based strength ratings (PELE), and what each metric measures.
9. **What makes my model dynamic** — Demonstrating how standing arrays, match outcomes, and progression trees update in real-time after actual scores are entered.
10. **Limitations** — Reflecting on team squad listings, fatigue indexes, and home-field advantages to improve future iterations.
