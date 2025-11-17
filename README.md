# Experiments on Nudgin the Automatic and Reflective Mind of LLMs

## Installation
### Using conda
1. Create an environment
```
conda create -n llm_experiments python=3.12
conda activate llm_experiments
```
2. Install browser_use package
```
pip install browser_use "fastapi[standard]"
```

## Running Experiments
1. Run baseline experiments
```
sh script_no_nudge.sh
```
If you are on MacOS:
```
bash script_no_nudge.sh
```
2. Run defaults experiments
```
sh script_defaults.sh
```
If you are on MacOS:
```
bash script_defaults.sh
```
3. Run social influence experiments
```
sh script_social_influence.sh
```
If you are on MacOS:
```
bash script_social_influence.sh
```