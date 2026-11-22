@echo off
chcp 65001 >nul
rem Met a jour la copie locale du tableau de bord (donnees publiees par le robot GitHub).
cd /d "%~dp0"
echo Mise a jour de la copie locale...
git pull --rebase --autostash
if errorlevel 1 (
  echo.
  echo La mise a jour a echoue. Verifiez la connexion internet, puis reessayez.
) else (
  echo.
  echo Termine. Vous pouvez ouvrir index.html.
)
pause
