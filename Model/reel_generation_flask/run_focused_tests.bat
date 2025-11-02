@echo off
echo Running focused test suite for failed/skipped endpoints...
echo Testing Cloud Run: https://reels-editor-298842469563.asia-south1.run.app/
echo Using image: edited_diary_magical.png
echo.

python pratham_test2.py

echo.
echo Focused test suite completed!
pause

