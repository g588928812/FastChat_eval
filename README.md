# Turning FastChat upside down to benchmark open-source LLMs

![ab](https://miro.medium.com/v2/resize:fit:2000/format:webp/1*rSGco9WTvKng04n8suN0fw.png)
**Winning percentage of an all-against-all competition of Open Assistant, Vicuna, ChatGPT, Alpaca and the LLaMA base model.** 70 questions asked to each model. Answers evaluated by GPT-3.5 (API). Shown are averages and std. dev. of 3 replicates per model. Control: GPT-3.5 answers “shifted” = answers not related to question asked. Bottom: Human preference as Elo ratings, assessed in the LMSYS chatbot arena.

https://medium.com/@geronimo7/open-source-chatbots-in-the-wild-9a44d7a41a48

```# get reviews from OpenAI API for Vicuna vs OA Pythia-12B, 3 replicates
export APIKEY="YOURKEY"
python3 get_review.py -r "gpt-3.5-pairwise" -a table/answer/answer_vicuna-13b.jsonl table/answer/answer_pythia-12b-sft-v8-7k-steps.jsonl -o table/review_pairwise/review_vicuna-13b_pythia-12b-sft-v8-7k-steps -dr 3 -k "$APIKEY"

# calc winning percentage
python3 reviews_winrate_pairwise.py -r table/reviews_pairwise

# generate html
python3 generate_webpage_data_from_table.py -r table/reviews_pairwise
```
