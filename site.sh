#!/bin/sh
# Builds the site: the page into site/public, and the rules, the commander and the server into site/server.
# Then `pnpm run dev` runs it locally, and `pnpm run deploy` builds it and puts it up.
set -e
cd "$(dirname "$0")"
# The page's scripts go in minified, all but the rules and the commander, which stay as written so the browsers
# run the same source as the server. Without a module format esbuild keeps every top-level name, which the
# page's scripts share.
MINIFY=$(jq -r '.film.scripts[] | select(. != "rules.js" and . != "ai.js")' game.json)
pnpm exec esbuild $MINIFY --minify --charset=utf8 --log-level=warning --outbase=. --outdir=.site-min
# Every sound, the score, the spoken lines, the weather and the effects, is kept out of the page, as a file of its
# own named by its contents, so the page loads quickly and a returning player's browser keeps the sounds across
# deploys. The page is built from the game's manifest without them, and with the minified scripts.
jq '.sounds = {} | .film.scripts |= map(if . == "rules.js" or . == "ai.js" then . else ".site-min/" + . end)' \
  game.json > .site-game.json
~/Source/film-studio/.venv/bin/python ~/Source/film-studio/player/build.py .site-game.json --out site/public/index.html
rm -f .site-game.json
rm -rf .site-min
mkdir -p site/public/audio
rm -f site/public/audio/*.mp3
FILES=""
for kf in $(jq -r '.sounds | to_entries[] | "\(.key)=\(.value)"' game.json); do
  k="${kf%%=*}"; f="${kf#*=}"
  n="$k-$(shasum -a 256 "$f" | cut -c1-10).mp3"
  cp "$f" "site/public/audio/$n"
  FILES="$FILES\"$k\":\"audio/$n\","
done
python3 -c "import sys; p='site/public/index.html'; s=open(p).read(); k='{/*@SOUND_FILES@*/}'; assert s.count(k) == 1; open(p, 'w').write(s.replace(k, '{' + sys.argv[1].rstrip(',') + '}'))" "$FILES"
# The settings panel names the build: the source commit, marked + when the folder holds unsaved changes, and when.
STAMP="$(git rev-parse --short HEAD)$(git diff --quiet -- . ':!site' || echo +) $(date '+%Y-%m-%d %H:%M')"
sed -i '' "s/Build __BUILD__/Build $STAMP/" site/public/index.html
# The build the site now serves, which open pages compare with their own to offer a reload.
printf '{"build":"%s"}\n' "$STAMP" > site/public/version.json
cp rules.js ai.js site/server/
cp server.js site/server/index.js
