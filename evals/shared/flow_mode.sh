# Sourced by a run_trial.sh after the fixture $fx is built, to set the
# trial's flow per FLOW:
#   stub (default): a flow id; the fixture's bin/flow logs every report.
#   absent: no flow id and no flow command. A PATH entry holding a `flow`
#   is replaced by a directory linking everything else in it, so the
#   trial keeps the other tools that live next to it.
case ${FLOW:-stub} in
  stub) export FLOW_ID=eval-trial ;;
  absent)
    rm -f "$fx/bin/flow" "$fx/flow.jsonl"; unset FLOW_ID
    IFS=: read -ra entries <<< "$PATH"
    dirs=(); n=0
    for dir in "${entries[@]}"; do
      if [ -x "$dir/flow" ]; then
        n=$((n + 1)); shadow="$fx/path-$n"; mkdir -p "$shadow"
        for file in "$dir"/*; do [ "${file##*/}" = flow ] || ln -sf "$file" "$shadow/"; done
        dir=$shadow
      fi
      dirs+=("$dir")
    done
    PATH=$(IFS=:; echo "${dirs[*]}") ;;
  *) echo "FLOW must be stub or absent" >&2; exit 1 ;;
esac
