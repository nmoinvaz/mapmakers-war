#!/bin/sh
# Builds the site: the page into site/public, and the rules, the commander and the server into site/server.
# Then `npx wrangler dev` in site/ runs it locally, and `npx wrangler deploy` puts it up.
set -e
cd "$(dirname "$0")"
# Every sound, the score, the spoken lines, the weather and the effects, is kept out of the page, as a file of its
# own named by its contents, so the page loads quickly and a returning player's browser keeps the sounds across
# deploys. The page is built from the game's manifest without them.
jq '.sounds = {}' game.json > .site-game.json
~/Source/film-studio/.venv/bin/python ~/Source/film-studio/player/build.py .site-game.json --out site/public/index.html
rm -f .site-game.json
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
