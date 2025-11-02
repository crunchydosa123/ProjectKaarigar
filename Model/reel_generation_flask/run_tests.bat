@echo off
echo Installing test dependencies...
pip install -r test_requirements.txt

echo.
echo Running comprehensive API tests...
echo Testing Cloud Run: https://reels-editor-298842469563.asia-south1.run.app/
echo.

python pratham_test.py

echo.
echo Test suite completed!
pause

