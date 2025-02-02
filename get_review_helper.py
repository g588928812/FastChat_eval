cmd_str="python3 get_review.py -r \"gpt-3.5-pairwise\" -a table/answer/answer_{m1}.jsonl table/answer/answer_{m2}.jsonl -o table/reviews_pairwise/review_{m1}_{m2} -dr 3 -k \"$APIKEY\""

models=[]
models.append("gpt-4:20230517")
models.append("alpaca-13b")
models.append("bard")
models.append("gpt35-shifted")
models.append("gpt35")
models.append("llama-13b")
models.append("oasst-sft-7-llama-30b-4bit-128g")
models.append("vicuna-13b")
models.append("oasst-rlhf-2-llama-30b-7k-steps-4bit-128g")
models.append("pythia-12b-sft-v8-7k-steps")
models.append("guanaco-33B-GPTQ")
models.append("Wizard-Vicuna-30B-Uncensored-GPTQ")

for i in range(len(models)):
	for f in list(range(len(models)))[i+1:]:
		model1=models[i]
		model2=models[f]
		print(cmd_str.format(
			m1=model1,
			m2=model2
			))
		# print(f"{models[i]} {models[f]}")