@echo off
echo ===================================================
echo   Launching Government Exam Assistant (ExamPrep AI)
echo ===================================================
cd /d "%~dp0"
python -m streamlit run app.py
pause

