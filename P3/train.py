import argparse, os, joblib, json
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import time
import wandb

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--max_steps', type=int, default=100)
    parser.add_argument('--batch_size', type=int, default=16)
    parser.add_argument('--output_dir', type=str, default='artifacts/latest')
    parser.add_argument('--wandb_project', type=str, default=None)
    parser.add_argument('--epochs', type=int, default=1)
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    # tiny synthetic dataset (fast)
    X, y = make_classification(n_samples=200, n_features=16, n_informative=8, random_state=42)
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

    model = LogisticRegression(max_iter=200)
    # simulate "steps" by training multiple times or just fit
    for epoch in range(max(1, args.epochs)):
        model.fit(X_train, y_train)
        if args.max_steps < 50:
            # small sleep to simulate short smoke run
            time.sleep(0.1)

    preds = model.predict(X_val)
    acc = float(accuracy_score(y_val, preds))
    print(f"SMOKE TRAIN finished — acc={acc:.4f}")

    # save model
    model_path = os.path.join(args.output_dir, 'model.joblib')
    joblib.dump(model, model_path)

    # minimal metadata
    meta = {'acc': acc, 'n_samples': len(X), 'model_path': model_path}
    with open(os.path.join(args.output_dir, 'meta.json'), 'w') as f:
        json.dump(meta, f)

    # optional wandb log
    if args.wandb_project and os.environ.get('WANDB_API_KEY'):
        try:
            wandb.init(project=args.wandb_project)
            wandb.log({'val_acc': acc})
            wandb.finish()
        except Exception as e:
            print('WandB logging failed:', e)

if __name__ == '__main__':
    main()
