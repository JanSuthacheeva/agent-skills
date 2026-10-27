# Stub forge and ticket CLIs and a fake remote for eval fixtures.
# Source it, then call forge_stubs and, inside the repo, forge_remote.

# forge_stubs <dest> <tickets.json>
# Writes bin/ stubs for clickup-axi, glab and gh into <dest>. Each logs its
# arguments to <dest>/calls.jsonl, so no run reaches a real service.
# `clickup-axi tasks <id>` prints the ticket <id> from tickets.json, a map
# of id to the text the real CLI would print, and fails for any other id.
forge_stubs() {
  local dest=$1 tickets
  tickets=$(cd "$(dirname "$2")" && pwd)/$(basename "$2")
  mkdir -p "$dest/bin"
  cat > "$dest/bin/clickup-axi" <<P
#!/usr/bin/env bash
python3 -c 'import json, sys; print(json.dumps(sys.argv[1:]))' clickup-axi "\$@" >> "$dest/calls.jsonl"
if [ "\$1" = tasks ] && python3 -c 'import json, sys; sys.stdout.write(json.load(open(sys.argv[1]))[sys.argv[2]])' "$tickets" "\$2" 2>/dev/null; then
  exit 0
fi
echo "error: task \$2 not found" >&2; exit 1
P
  cat > "$dest/bin/glab" <<P
#!/usr/bin/env bash
python3 -c 'import json, sys; print(json.dumps(sys.argv[1:]))' glab "\$@" >> "$dest/calls.jsonl"
case "\$1 \$2" in
  "mr list") echo "No open merge requests match your search in shop/shop." ;;
  "mr create") echo "https://gitlab.com/shop/shop/-/merge_requests/57" ;;
  *) echo "glab stub: \$*" ;;
esac
P
  cat > "$dest/bin/gh" <<P
#!/usr/bin/env bash
python3 -c 'import json, sys; print(json.dumps(sys.argv[1:]))' gh "\$@" >> "$dest/calls.jsonl"
echo "gh: this repository is not on GitHub" >&2; exit 1
P
  chmod +x "$dest/bin/"*
  touch "$dest/calls.jsonl"
}

# forge_remote <dest>
# Run inside the repo: origin looks like GitLab, but pushes land in the bare
# <dest>/origin.git.
forge_remote() {
  local dest=$1
  git init -q --bare "$dest/origin.git"
  git remote add origin git@gitlab.com:shop/shop.git
  git config remote.origin.pushurl "$dest/origin.git"
  git config remote.origin.fetch '+refs/heads/*:refs/remotes/origin/*'
}
