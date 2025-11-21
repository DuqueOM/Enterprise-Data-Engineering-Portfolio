
#!/usr/bin/env python3
import argparse
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, Seq2SeqTrainingArguments, Seq2SeqTrainer
from peft import LoraConfig, get_peft_model, TaskType

def main(args):
    model_name = args.model_name
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name, device_map="auto")

    lora_config = LoraConfig(
        r=args.lora_r,  # [P4]
        lora_alpha=args.lora_alpha,  # [P4]
        target_modules=["q","v","k","o"],
        lora_dropout=args.lora_dropout,  # [P4]
        bias="none",
        task_type=TaskType.SEQ_2_SEQ_LM
    )
    model = get_peft_model(model, lora_config)

    ds = load_dataset("json", data_files={"train": args.train} if not args.validation else {"train": args.train, "validation": args.validation})
    def preprocess(ex):
        inp = ex["input_text"]
        tgt = ex["target_text"]
        tokenized_in = tokenizer(inp, truncation=True, padding="max_length", max_length=512)
        tokenized_out = tokenizer(tgt, truncation=True, padding="max_length", max_length=256)
        tokenized_in["labels"] = tokenized_out["input_ids"]
        return tokenized_in
    tokenized = ds.map(preprocess, batched=False)
    training_args = Seq2SeqTrainingArguments(
        output_dir=args.output_dir,
        per_device_train_batch_size=4,
        per_device_eval_batch_size=4,
        predict_with_generate=True,
        logging_steps=10,
        save_total_limit=3,
        num_train_epochs=args.epochs,
        max_steps=args.max_steps,  # [P4]
        fp16=True if args.fp16 else False
    )
    trainer = Seq2SeqTrainer(model=model, args=training_args, train_dataset=tokenized["train"], eval_dataset=tokenized.get("validation", None), tokenizer=tokenizer)
    trainer.train()
    model.save_pretrained(args.output_dir)
    print("LoRA model saved to", args.output_dir)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--model_name", default="google/flan-t5-base")
    p.add_argument("--train", required=True)
    p.add_argument("--validation", required=False)
    p.add_argument("--output_dir", default="out/lora")
    p.add_argument("--epochs", type=int, default=3)
    p.add_argument("--fp16", action="store_true")
    p.add_argument("--max_steps", type=int, default=0)  # [P4]
    p.add_argument("--lora_r", type=int, default=8)  # [P4]
    p.add_argument("--lora_alpha", type=int, default=32)  # [P4]
    p.add_argument("--lora_dropout", type=float, default=0.05)  # [P4]
    args = p.parse_args()
    main(args)
