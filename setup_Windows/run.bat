start cmd.exe @cmd /k "conda activate NLP && cd %~dp0/src"
conda activate NLP && cd %~dp0 && python3 src/NLP_welcome_main.py && git pull origin