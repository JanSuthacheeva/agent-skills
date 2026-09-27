I committed everything that was staged as `c414449 treewide: add MIT license` on `main`. It's local only; nothing was pushed.

The commit adds a `LICENSE` file, a License section in the README, and an SPDX license header to each of the five Python files. I used the `treewide:` scope because the change touches every package, which matches earlier commits like `treewide: bump python to 3.12`.

`LICENSE` contains only the line "MIT License" and not the full MIT text with a copyright holder. You'll probably want to replace it with the complete license text.