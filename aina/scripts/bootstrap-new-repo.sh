#!/usr/bin/env bash
#
# Løfter aina/-mappen ut i sitt eget GitHub-repo, med historikken intakt.
#
# Bakgrunn: Aina ble laget som en mappe i anchor-prospekt-api fordi
# GitHub-appen i den økten ikke hadde rettighet til å opprette nye repo.
# Alt er skrevet for å stå alene — dette scriptet fullfører flyttingen.
#
#   ./scripts/bootstrap-new-repo.sh [reponavn]
#
# Krever: git, og gh (GitHub CLI) hvis repoet skal opprettes automatisk.

set -euo pipefail

REPONAVN="${1:-aina}"
KILDEMAPPE="aina"
ARBEID="$(mktemp -d)"

rot="$(git rev-parse --show-toplevel)"
cd "$rot"

if [[ ! -d "$KILDEMAPPE" ]]; then
  echo "Fant ikke $KILDEMAPPE/ i $rot" >&2
  exit 1
fi

echo "→ Splitter ut $KILDEMAPPE/ med historikk"
gren="split-$REPONAVN-$$"
git subtree split --prefix="$KILDEMAPPE" -b "$gren"

echo "→ Bygger nytt repo i $ARBEID"
git clone --quiet --branch "$gren" --single-branch "$rot" "$ARBEID/$REPONAVN"
cd "$ARBEID/$REPONAVN"
git checkout --quiet -b main
git branch --quiet -D "$gren" 2>/dev/null || true
git remote remove origin

cd "$rot"
git branch -D "$gren"

echo
echo "Ferdig. Repoet ligger klart i:"
echo "    $ARBEID/$REPONAVN"
echo
echo "Neste steg — opprett repoet på GitHub og push:"
echo
echo "    cd $ARBEID/$REPONAVN"
echo "    gh repo create $REPONAVN --private --source=. --push"
echo
echo "Uten gh: opprett et tomt privat repo på github.com/new, og deretter"
echo
echo "    git remote add origin git@github.com:<bruker>/$REPONAVN.git"
echo "    git push -u origin main"
echo
echo "Merk: .github/workflows/ci.yml kjører først når mappen er sitt eget repo."
echo "GitHub Actions leser kun workflows som ligger i repoets rot."
