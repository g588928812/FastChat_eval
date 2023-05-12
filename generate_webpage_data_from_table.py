"""Generate json file for webpage."""
import json
import os
import glob
import re
import argparse

def import_json(file_path, key):
    file_path = os.path.expanduser(file_path)
    f = open(file_path)
    data = json.load(f)
    f.close()
    if key is not None:
        data.sort(key=lambda x: x[key])
        data = {item[key]: item for item in data}
    return data

def get_json_list(file_path):
    file_path = os.path.expanduser(file_path)
    with open(file_path, "r") as f:
        json_list = []
        for line in f:
            json_list.append(json.loads(line, strict=False))
        return json_list

def get_json_list_dir(dir_path):
    files = glob.glob(os.path.expanduser(dir_path) + "/*.jsonl")

    jsonl=[]
    for f in files:
        jsonl.extend(get_json_list(f))

    return jsonl

def import_json_dir(dir_path, key):
    files = glob.glob(os.path.expanduser(dir_path) + "/*.jsonl")

    data=[]
    for f in files:
        data.extend(get_json_list(f))

    if key is not None:
        data.sort(key=lambda x: x[key])
        data = {item[key]: item for item in data}
    return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--review-dir", default=None)
    args = parser.parse_args()

    assert(args.review_dir != None)

    answers = import_json_dir("table/answer/", key="answer_id")
    questions = import_json("table/question.json", key="question_id")
    reviews = get_json_list_dir(args.review_dir)

    html_reviews={}

    unexpected_wins=[]
    unexpected_wincount=0
    unexpected_wins.append(["gpt-3.5-turbo:20230327-shifted", None])
    unexpected_wins.append(["llama-13b:v1", "vicuna-13b:20230322-clean-lang"])
    unexpected_wins.append(["llama-13b:v1", "oasst-rlhf-2-llama-30b-7k-steps-4bit-128g"])
    unexpected_wins.append(["llama-13b:v1", "gpt-3.5-turbo:20230327"])
    unexpected_wins.append(["vicuna-13b:20230322-clean-lang", "gpt-3.5-turbo:20230327"])
    unexpected_wins.append(["pythia-12b-sft-v8-7k-steps", "oasst-sft-7-llama-30b-4bit-128g"])

    for review in reviews:
        m1=answers[review["answer1_id"]]["model_id"]
        m2=answers[review["answer2_id"]]["model_id"]

        if not m1 in html_reviews:
            html_reviews[m1]=[]
        if not m2 in html_reviews:
            html_reviews[m2]=[]

        html_reviews[m1].append(review)
        html_reviews[m2].append(review)

    table_template = """<table class="styled-table">
        <tr>
            <td colspan=2>Question {qid}: {question}</td>
        </tr>
        <tr>
            <td>Answer <b>{model1}</td>
            <td>Answer <b>{model2}</td>
        </tr>
        <tr>
            <td>{answer1}</td>
            <td>{answer2}</td>
        </tr>
        <tr>
            <td>Winner: <b>{winner1}{tie}</td>
            <td><b>{winner2}{tie}</td>
        </tr>
        <tr>
            <td colspan=2>Review {rid}:<br>{revtext}</td>
        </tr>
        <tr>
            <td colspan=2>{unexpected_win}</td>
        </tr>
    </table>
    <br>"""
    for model in html_reviews:
        outfn=f"webpage/{model}.html"
        unexpected_wincount_model=0
        total_wincount_model=0

        with open(outfn, "w") as f:
            f.write("""<html>
                <head>
                    <link rel="stylesheet" href="style.css" media="all" />
                </head>
                <body>""")


            for review in html_reviews[model]:
                model1=answers[review["answer1_id"]]["model_id"]
                model2=answers[review["answer2_id"]]["model_id"]

                unexpected_win=""
                if review["winner"] > 0:
                    winner=model1 if review["winner"]==1 else model2
                    loser=model2 if review["winner"]==1 else model1

                    for ue in unexpected_wins:
                        if ue[0]==winner and (ue[1]==loser or ue[1] is None):
                            unexpected_win="unexpected_win"
                            unexpected_wincount+=1
                            unexpected_wincount_model+=1
                    if winner==model:
                        total_wincount_model+=1

                f.write(table_template.format(
                    qid=review["question_id"],
                    question=questions[review["question_id"]]["text"],
                    model1=answers[review["answer1_id"]]["model_id"],
                    answer1=answers[review["answer1_id"]]["text"],
                    model2=answers[review["answer2_id"]]["model_id"],
                    answer2=answers[review["answer2_id"]]["text"],
                    winner1=answers[review["answer1_id"]]["model_id"] if review["winner"] == 1 else "",
                    winner2=answers[review["answer2_id"]]["model_id"] if review["winner"] == 2 else "",
                    tie="TIE" if review["winner"] == 0 else "",
                    rid=review["review_id"],
                    revtext=review["text"],
                    unexpected_win=unexpected_win
                    ))

            f.write("</body></html>")
            f.close()
            print(f"wrote {outfn} ({unexpected_wincount_model} unexpected wins of {total_wincount_model} total wins ({round(unexpected_wincount_model/total_wincount_model*100,1)}%), total comparisons {len(html_reviews[model])})")

    print(f"{unexpected_wincount} total unexpected wins")

    # # Reorder the records, this is optional
    # for r in records:
    #     if r["id"] <= 20:
    #         r["id"] += 60
    #     else:
    #         r["id"] -= 20
    # for r in records:
    #     if r["id"] <= 50:
    #         r["id"] += 10
    #     elif 50 < r["id"] <= 60:
    #         r["id"] -= 50
    # for r in records:
    #     if r["id"] == 7:
    #         r["id"] = 1
    #     elif r["id"] < 7:
    #         r["id"] += 1

    # records.sort(key=lambda x: x["id"])

    # Write to file
    # with open("webpage/data.json", "w") as f:
    #     json.dump({"questions": records, "models": models}, f, indent=2)
