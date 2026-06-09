#!/usr/bin/env bash
# =====================================================================
#  MARS ROVER — launcher wyboru wersji projektu
#  Każda wersja to gałąź/tag git. Skrypt lokalny (nieśledzony przez git),
#  więc przetrwa przełączanie wersji.
# =====================================================================
cd "$(dirname "$0")" || exit 1

echo "================================================================"
echo "   MARS ROVER — wybór wersji projektu"
echo "================================================================"
echo "  1) PEŁNY PROJEKT (main): CNN + plecak + sklep      -> serwer"
echo "  2) ALGORYTM GENETYCZNY (plecak + sklep, bez kamery) -> serwer"
echo "  3) ALGORYTM GENETYCZNY — DEMO dla prowadzącego"
echo "  4) ALGORYTM GENETYCZNY — porównanie GA vs DP"
echo "  5) SIEĆ CNN (tylko kamera UE5, wcześniejsze zadanie) -> serwer"
echo "================================================================"
read -rp "Twój wybór [1-5]: " choice

# Odrzucenie regenerowanych artefaktów, aby przełączenie gałęzi było czyste
git checkout -- nn_model_report.txt rover_training_data.csv decision_tree.png 2>/dev/null

run_backend () {   # $1 = gałąź/tag,  $2 = komenda
    if ! git checkout "$1"; then
        echo ""
        echo "[BŁĄD] Nie można przełączyć na '$1' — masz niezapisane zmiany."
        echo "       Zatwierdź je (git commit) lub cofnij (git stash) i spróbuj ponownie."
        exit 1
    fi
    echo ""
    echo ">> Wersja '$1' aktywna. Uruchamiam: $2"
    echo "   (serwer: http://localhost:8000/docs   |   Ctrl+C aby zatrzymać)"
    echo ""
    cd backend || exit 1
    eval "$2"
}

case "$choice" in
    1) run_backend "main"                       "python3 run.py" ;;
    2) run_backend "feat/genetic-knapsack-shop" "python3 run.py" ;;
    3) run_backend "feat/genetic-knapsack-shop" "python3 demo_genetyczny.py" ;;
    4) run_backend "feat/genetic-knapsack-shop" "python3 -m app.core.knapsack" ;;
    5) run_backend "wersja-siec-cnn"            "python3 run.py" ;;
    *) echo "Nieznany wybór: '$choice'"; exit 1 ;;
esac
