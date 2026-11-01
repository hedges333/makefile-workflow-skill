#!/usr/bin/env python3
"""PreToolUse hook script for Antigravity.

Blocks production database commands and destructive Git commands, and gates
git commit, git push, gh pr merge, git rebase, and git branch -D.
"""

import json
import os
import re
import shlex
import sys

DB_TOOLS = (
    "psql",
    "pg_dump",
    "pg_restore",
    "mysql",
    "mysqldump",
    "mariadb",
    "mongo",
    "mongosh",
    "redis-cli",
    "sqlite3",
    "sqlcmd",
    "flyway",
    "liquibase",
    "alembic",
    "prisma",
    "goose",
    "dbmate",
)

PROD_TOKEN_RE = re.compile(
    r"(?:^|[^a-zA-Z0-9])(prod|production)(?:$|[^a-zA-Z0-9])",
    re.IGNORECASE,
)

URI_USERINFO_RE = re.compile(r"(://)[^/\s'\";@]+@")

HOST_VALUE_RE = re.compile(
    r"(?:"
    r"(?:^|\s)-(?:h|S)\s*['\"]?|"
    r"--host(?:=|\s+)['\"]?|"
    r"\b(?:DB_HOST|PGHOST|MYSQL_HOST|MARIADB_HOST|REDIS_HOST|MONGO_HOST|HOST)=['\"]?|"
    r"://|"
    r"@"
    r")([a-zA-Z0-9._-]+)",
    re.IGNORECASE,
)

QUOTED_ARG_PAT = r"(?:'[^']*'|\"(?:\\.|[^\"\\])*\")"

INLINE_QUERY_RE = re.compile(
    rf"(?:(?<=^)|(?<=\s))(?:-c|-e|--command|--execute|--eval)(?:=|\s*){QUOTED_ARG_PAT}",
    re.IGNORECASE,
)

SQLITE_CMD_RE = re.compile(
    rf"(\bsqlite3\b[^\n]*?\s){QUOTED_ARG_PAT}\s*$",
    re.IGNORECASE,
)


def _normalize_str_list(items):
  if not isinstance(items, list):
    return []
  return [x.strip() for x in items if isinstance(x, str) and x.strip()]


def _parse_csv_env(env_name):
  raw = os.getenv(env_name, "")
  if not raw:
    return []
  return [item.strip() for item in raw.split(",") if item.strip()]


def load_database_config(payload):
  """Loads database isolation rules from workspace config, global config, and env."""
  db_cfg = {
      "prodDatabases": [],
      "testDatabases": [],
      "prodHosts": [],
  }

  candidates = []
  for ws in payload.get("workspacePaths") or []:
    candidates.append(os.path.join(ws, ".workflow", "config.json"))
  candidates.append(os.path.join(os.getcwd(), ".workflow", "config.json"))
  candidates.append(os.path.expanduser("~/.gemini/config/makefile-workflow.json"))

  for cfg_path in candidates:
    if os.path.isfile(cfg_path):
      try:
        with open(cfg_path, "r", encoding="utf-8") as f:
          loaded = json.load(f)
        if isinstance(loaded, dict):
          if isinstance(loaded.get("database"), dict):
            raw_db = loaded["database"]
            for key in ("prodDatabases", "testDatabases", "prodHosts"):
              if key in raw_db:
                db_cfg[key] = _normalize_str_list(raw_db[key])
          break
      except Exception:
        pass

  env_mappings = {
      "MAKEFILE_WORKFLOW_PROD_DBS": "prodDatabases",
      "MAKEFILE_WORKFLOW_TEST_DBS": "testDatabases",
      "MAKEFILE_WORKFLOW_PROD_HOSTS": "prodHosts",
  }
  for env_var, key in env_mappings.items():
    vals = _parse_csv_env(env_var)
    if vals:
      merged = list(db_cfg[key])
      for v in vals:
        if v not in merged:
          merged.append(v)
      db_cfg[key] = merged

  return db_cfg


def _preprocess_shell(cmd):
  """Strips unquoted # comments and normalizes ANSI-C $'...' literals."""
  out = []
  quote = None
  escaped = False
  i = 0
  n = len(cmd)
  while i < n:
    ch = cmd[i]
    if quote is None:
      if escaped:
        out.append("\\")
        out.append(ch)
        escaped = False
        i += 1
        continue
      if ch == "\\":
        escaped = True
        i += 1
        continue
      if ch == "#" and (i == 0 or cmd[i - 1] in " \t\r\n;|&()"):
        while i < n and cmd[i] != "\n":
          i += 1
        continue
      if cmd[i : i + 2] == "$'":
        j = i + 2
        body = []
        closed = False
        while j < n:
          c2 = cmd[j]
          if c2 == "\\" and j + 1 < n:
            nxt = cmd[j + 1]
            if nxt in ("'", "\\"):
              body.append(nxt)
            else:
              body.append(nxt)
            j += 2
            continue
          if c2 == "'":
            closed = True
            j += 1
            break
          body.append(c2)
          j += 1
        if closed:
          safe_single = "'" + "".join(body).replace("'", "'\\''") + "'"
          out.append(safe_single)
          i = j
          continue
        out.append("'")
        i += 2
        continue
      if ch in ("'", '"'):
        quote = ch
        out.append(ch)
        i += 1
        continue
      out.append(ch)
      i += 1
      continue

    if quote == "'":
      out.append(ch)
      if ch == "'":
        quote = None
      i += 1
      continue

    if escaped:
      out.append("\\")
      out.append(ch)
      escaped = False
      i += 1
      continue
    if ch == "\\":
      escaped = True
      i += 1
      continue
    out.append(ch)
    if ch == '"':
      quote = None
    i += 1

  if escaped:
    out.append("\\")
  return "".join(out)


def _strip_shell_redirections(seg):
  """Strips unquoted shell redirections (such as 2>&1, 2>/dev/null, > out)."""
  out = []
  quote = None
  escaped = False
  i = 0
  n = len(seg)
  while i < n:
    ch = seg[i]
    if escaped:
      out.append("\\")
      out.append(ch)
      escaped = False
      i += 1
      continue
    if ch == "\\" and quote != "'":
      escaped = True
      i += 1
      continue
    if quote:
      out.append(ch)
      if ch == quote:
        quote = None
      i += 1
      continue
    if ch in ("'", '"'):
      quote = ch
      out.append(ch)
      i += 1
      continue

    op_idx = -1
    if ch.isdigit() and (i == 0 or seg[i - 1] in " \t\r\n;|&()"):
      k = i
      while k < n and seg[k].isdigit():
        k += 1
      if k < n and seg[k] in ("<", ">"):
        op_idx = k
    elif ch in ("<", ">") or seg[i : i + 2] == "&>":
      op_idx = i

    if op_idx != -1:
      if seg[op_idx : op_idx + 3] in ("&>>", "<<<", "<<-"):
        j = op_idx + 3
      elif seg[op_idx : op_idx + 2] in ("&>", ">>", "<<", "<&", ">&", "<>", ">|"):
        j = op_idx + 2
      else:
        j = op_idx + 1
      while j < n and seg[j] in (" ", "\t"):
        j += 1
      w_quote = None
      w_esc = False
      w_paren = 0
      while j < n:
        wc = seg[j]
        if w_esc:
          w_esc = False
          j += 1
          continue
        if wc == "\\" and w_quote != "'":
          w_esc = True
          j += 1
          continue
        if w_quote:
          if wc == w_quote:
            w_quote = None
          j += 1
          continue
        if wc in ("'", '"'):
          w_quote = wc
          j += 1
          continue
        if wc == "(":
          w_paren += 1
          j += 1
          continue
        if wc == ")":
          if w_paren > 0:
            w_paren -= 1
            j += 1
            continue
          break
        if w_paren == 0 and wc in (" ", "\t", "\r", "\n", ";", "|", "&", "<", ">"):
          break
        j += 1
      out.append(" ")
      i = j
      continue

    out.append(ch)
    i += 1

  if escaped:
    out.append("\\")
  return "".join(out)


def _split_shell_subcommands(cmd):
  """Splits a shell command string on unquoted |, ||, &&, ;, and newline."""
  parts = []
  buf = []
  quote = None
  escaped = False
  i = 0
  n = len(cmd)
  while i < n:
    ch = cmd[i]
    if escaped:
      buf.append(ch)
      escaped = False
      i += 1
      continue
    if ch == "\\" and quote != "'":
      buf.append(ch)
      escaped = True
      i += 1
      continue
    if quote:
      buf.append(ch)
      if ch == quote:
        quote = None
      i += 1
      continue
    if ch in ("'", '"'):
      quote = ch
      buf.append(ch)
      i += 1
      continue
    if ch in (";", "\n"):
      seg = "".join(buf).strip()
      if seg:
        parts.append(seg)
      buf = []
      i += 1
      continue
    if ch == "|":
      seg = "".join(buf).strip()
      if seg:
        parts.append(seg)
      buf = []
      if i + 1 < n and cmd[i + 1] == "|":
        i += 2
      else:
        i += 1
      continue
    if ch == "&":
      if i + 1 < n and cmd[i + 1] == "&":
        seg = "".join(buf).strip()
        if seg:
          parts.append(seg)
        buf = []
        i += 2
        continue
      if (i > 0 and cmd[i - 1] in ("<", ">")) or (i + 1 < n and cmd[i + 1] == ">"):
        buf.append(ch)
        i += 1
        continue
      seg = "".join(buf).strip()
      if seg:
        parts.append(seg)
      buf = []
      i += 1
      continue
    buf.append(ch)
    i += 1
  tail = "".join(buf).strip()
  if tail:
    parts.append(tail)
  return parts or [cmd]


def _extract_shell_substitutions(cmd):
  """Extracts unescaped $(...), `...`, and unquoted (...) subshell bodies."""
  results = []
  in_single = False
  in_double = False
  escaped = False
  i = 0
  n = len(cmd)
  while i < n:
    ch = cmd[i]
    if escaped:
      escaped = False
      i += 1
      continue
    if ch == "\\" and not in_single:
      escaped = True
      i += 1
      continue
    if ch == "'" and not in_double:
      in_single = not in_single
      i += 1
      continue
    if ch == '"' and not in_single:
      in_double = not in_double
      i += 1
      continue
    if not in_single:
      if cmd[i : i + 2] == "$(":
        depth = 1
        j = i + 2
        sub_single = False
        sub_double = False
        sub_esc = False
        while j < n and depth > 0:
          c2 = cmd[j]
          if sub_esc:
            sub_esc = False
          elif c2 == "\\" and not sub_single:
            sub_esc = True
          elif c2 == "'" and not sub_double:
            sub_single = not sub_single
          elif c2 == '"' and not sub_single:
            sub_double = not sub_double
          elif not sub_single and not sub_double:
            if c2 == "(":
              depth += 1
            elif c2 == ")":
              depth -= 1
          j += 1
        inner = cmd[i + 2 : j - 1 if depth == 0 else j].strip()
        if inner:
          results.append(inner)
        i = j
        continue
      if ch == "`":
        j = i + 1
        sub_esc = False
        while j < n:
          c2 = cmd[j]
          if sub_esc:
            sub_esc = False
          elif c2 == "\\":
            sub_esc = True
          elif c2 == "`":
            break
          j += 1
        inner = cmd[i + 1 : j].strip()
        if inner:
          results.append(inner)
        i = j + 1
        continue
      if not in_double and ch == "(":
        depth = 1
        j = i + 1
        sub_single = False
        sub_double = False
        sub_esc = False
        while j < n and depth > 0:
          c2 = cmd[j]
          if sub_esc:
            sub_esc = False
          elif c2 == "\\" and not sub_single:
            sub_esc = True
          elif c2 == "'" and not sub_double:
            sub_single = not sub_single
          elif c2 == '"' and not sub_single:
            sub_double = not sub_double
          elif not sub_single and not sub_double:
            if c2 == "(":
              depth += 1
            elif c2 == ")":
              depth -= 1
          j += 1
        inner = cmd[i + 1 : j - 1 if depth == 0 else j].strip()
        if inner:
          results.append(inner)
        i = j
        continue
    i += 1
  return results


def _expand_shell_subcommands(cmd, max_depth=3):
  """Expands pipelines, chains, command substitutions, subshells, and sh -c."""
  expanded = []
  queue = [(cmd, 0)]
  while queue:
    raw_current, depth = queue.pop(0)
    current = _preprocess_shell(raw_current)
    if depth < max_depth:
      for inner in _extract_shell_substitutions(current):
        queue.append((inner, depth + 1))
    for raw_seg in _split_shell_subcommands(current):
      seg = _strip_shell_redirections(raw_seg).strip()
      if not seg:
        continue
      expanded.append(seg)
      if depth < max_depth:
        for tokens in _tokenize_subcommand(seg):
          exe, rem = _unwrap_command_tokens(tokens)
          if exe == "SHELL_C" and rem:
            queue.append((rem[0], depth + 1))
  return expanded or [cmd]


def _contains_identifier(cmd, name):
  sep = r"[^a-zA-Z0-9_-]"
  pattern = rf"(?:^|{sep}){re.escape(name)}(?:$|{sep})"
  return re.search(pattern, cmd, re.IGNORECASE) is not None


def _strip_identifier(cmd, name):
  pattern = rf"(?i)(?:(?<=^)|(?<=[^a-zA-Z0-9_-])){re.escape(name)}(?=$|[^a-zA-Z0-9_-])"
  return re.sub(pattern, " ", cmd)


def _has_prod_host_token(cmd):
  for match in HOST_VALUE_RE.finditer(cmd):
    if PROD_TOKEN_RE.search(match.group(1)):
      return True
  return False


def _evaluate_single_subcommand(subcmd, db_cfg):
  if not is_database_command(subcmd):
    return True, ""

  clean_cmd = URI_USERINFO_RE.sub(r"\1", subcmd)

  for host in db_cfg.get("prodHosts") or []:
    if host and _contains_identifier(clean_cmd, host):
      return (
          False,
          f"Blocked database command targeting live host '{host}'. "
          "Do not connect to live databases. "
          "Point tests to a *_test database or an in-memory mock.",
      )

  for db_name in db_cfg.get("prodDatabases") or []:
    if db_name and _contains_identifier(clean_cmd, db_name):
      return (
          False,
          f"Blocked database command with live database name '{db_name}'. "
          "Do not connect to live databases. "
          "Point tests to a *_test database or an in-memory mock.",
      )

  if _has_prod_host_token(clean_cmd):
    return (
        False,
        "Blocked database command targeting a production host. "
        "Do not connect to live databases. "
        "Point tests to a *_test database or an in-memory mock.",
    )

  matched_test_dbs = [
      test_db
      for test_db in (db_cfg.get("testDatabases") or [])
      if test_db and _contains_identifier(clean_cmd, test_db)
  ]
  if matched_test_dbs:
    scrubbed = INLINE_QUERY_RE.sub(" ", clean_cmd)
    scrubbed = SQLITE_CMD_RE.sub(r"\1", scrubbed)
    for test_db in matched_test_dbs:
      scrubbed = _strip_identifier(scrubbed, test_db)
    prod_rem = PROD_TOKEN_RE.search(scrubbed)
    if prod_rem:
      token = prod_rem.group(1)
      return (
          False,
          f"Blocked database command with production name '{token}'. "
          "Do not connect to live databases. "
          "Point tests to a *_test database or an in-memory mock.",
      )
    return True, ""

  prod_match = PROD_TOKEN_RE.search(clean_cmd)
  if prod_match:
    token = prod_match.group(1)
    return (
        False,
        f"Blocked database command with production name '{token}'. "
        "Do not connect to live databases. "
        "Point tests to a *_test database or an in-memory mock.",
    )

  return True, ""


def evaluate_database_safety(cmd, db_cfg):
  for subcmd in _expand_shell_subcommands(cmd):
    is_safe, deny_reason = _evaluate_single_subcommand(subcmd, db_cfg)
    if not is_safe:
      return False, deny_reason
  return True, ""


GIT_GLOBAL_VALUE_FLAGS = {
    "-C",
    "-c",
    "--git-dir",
    "--work-tree",
    "--namespace",
    "--super-prefix",
    "--config-env",
    "--exec-path",
    "--attr-source",
    "--list-cmds",
}

ENV_ASSIGN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
SHELL_KEYWORDS = {
    "(",
    "{",
    "}",
    ")",
    "!",
    "if",
    "then",
    "elif",
    "else",
    "do",
    "while",
    "until",
}


def _tokenize_subcommand(subcmd):
  """Splits a shell segment into token lists, failing closed on bad quotes."""
  try:
    toks = shlex.split(subcmd, posix=True)
    return [toks] if toks else []
  except ValueError:
    groups = []
    for chunk in re.split(r"(?:&&|\|\||[;|&\n])", subcmd):
      words = [t for t in re.split(r"[\s'\"]+", chunk.strip()) if t]
      if words:
        groups.append(words)
    return groups


def _unwrap_command_tokens(tokens):
  """Strips leading env assignments and shell wrappers, returning (exe, args)."""
  idx = 0
  n = len(tokens)
  while idx < n:
    tok = tokens[idx]
    if tok in SHELL_KEYWORDS:
      idx += 1
      continue
    if ENV_ASSIGN_RE.match(tok):
      idx += 1
      continue
    exe = os.path.basename(tok)
    if exe == "eval":
      j = idx + 1
      if j < n and tokens[j] == "--":
        j += 1
      if j < n:
        return "SHELL_C", [" ".join(tokens[j:])]
      return None, []
    if exe == "env":
      idx += 1
      while idx < n and tokens[idx].startswith("-"):
        flag = tokens[idx]
        if flag == "--":
          idx += 1
          break
        if flag in {"-S", "--split-string"}:
          if idx + 1 < n:
            return "SHELL_C", [tokens[idx + 1]]
          return None, []
        if flag.startswith("-S") and len(flag) > 2:
          return "SHELL_C", [flag[2:]]
        if flag.startswith("--split-string="):
          return "SHELL_C", [flag.split("=", 1)[1]]
        if flag in {"-u", "-C", "--unset", "--chdir"}:
          idx += 2
        else:
          idx += 1
      continue
    if exe in {"command", "builtin", "exec", "nohup", "time"}:
      idx += 1
      while idx < n and tokens[idx].startswith("-"):
        flag = tokens[idx]
        if flag == "--":
          idx += 1
          break
        idx += 1
      continue
    if exe == "sudo":
      idx += 1
      while idx < n and tokens[idx].startswith("-"):
        flag = tokens[idx]
        if flag == "--":
          idx += 1
          break
        if flag in {"-u", "-g", "-C", "-D", "-h", "-p", "-r", "-t", "-T", "-U"}:
          idx += 2
        else:
          idx += 1
      continue
    if exe == "xargs":
      idx += 1
      while idx < n and tokens[idx].startswith("-"):
        flag = tokens[idx]
        if flag == "--":
          idx += 1
          break
        if flag in {"-n", "-L", "-s", "-P", "-I", "-d", "-E", "-a"}:
          idx += 2
        else:
          idx += 1
      continue
    if exe == "timeout":
      idx += 1
      while idx < n and tokens[idx].startswith("-"):
        flag = tokens[idx]
        if flag == "--":
          idx += 1
          break
        if flag in {"-k", "-s", "--kill-after", "--signal"}:
          idx += 2
        else:
          idx += 1
      if idx < n:
        idx += 1
      continue
    if exe == "nice":
      idx += 1
      while idx < n and tokens[idx].startswith("-"):
        flag = tokens[idx]
        if flag == "--":
          idx += 1
          break
        if flag in {"-n", "--adjustment"}:
          idx += 2
        else:
          idx += 1
      continue
    if exe in {"sh", "bash", "zsh", "dash", "ksh"}:
      j = idx + 1
      has_c = False
      while j < n:
        flag = tokens[j]
        if flag in {"--", "-"}:
          j += 1
          break
        if flag in {"-o", "+o", "-O", "+O", "--rcfile", "--init-file"}:
          j += 2
          continue
        if flag.startswith("--"):
          j += 1
          continue
        if flag.startswith(("-", "+")) and len(flag) > 1:
          is_minus = flag.startswith("-")
          for k, ch in enumerate(flag[1:], start=1):
            if is_minus and ch == "c":
              has_c = True
            elif ch in {"o", "O"}:
              if k == len(flag) - 1:
                j += 1
              break
          j += 1
          continue
        break
      if has_c and j < n:
        return "SHELL_C", [tokens[j]]
      return exe, tokens[idx + 1 :]
    return exe, tokens[idx + 1 :]
  return None, []


def _parse_git_subcommand(git_args):
  """Strips global git flags and returns (subcommand, subcommand_args, configs)."""
  idx = 0
  n = len(git_args)
  configs = []
  while idx < n:
    tok = git_args[idx]
    if tok == "--":
      if idx + 1 < n:
        return git_args[idx + 1], git_args[idx + 2 :], configs
      return None, [], configs
    if tok == "-c":
      if idx + 1 < n:
        configs.append(git_args[idx + 1])
      idx += 2
      continue
    if tok.startswith("-c") and len(tok) > 2:
      configs.append(tok[2:])
      idx += 1
      continue
    if tok in GIT_GLOBAL_VALUE_FLAGS:
      idx += 2
      continue
    if tok.startswith("-C") and len(tok) > 2:
      idx += 1
      continue
    if any(tok.startswith(flag + "=") for flag in GIT_GLOBAL_VALUE_FLAGS):
      idx += 1
      continue
    if tok.startswith("-"):
      idx += 1
      continue
    return tok, git_args[idx + 1 :], configs
  return None, [], configs


def _split_git_args(args, short_value_chars="", long_value_flags=()):
  """Splits subcommand args into (long_opts, short_opts, ordered, pos, has_dd)."""
  long_opts = []
  short_opts = set()
  ordered_opts = []
  positionals = []
  has_double_dash = False
  i = 0
  n = len(args)
  while i < n:
    tok = args[i]
    if tok == "--":
      has_double_dash = True
      positionals.extend(args[i + 1 :])
      break
    if tok.startswith("--"):
      long_opts.append(tok)
      ordered_opts.append(tok)
      if tok in long_value_flags:
        i += 2
      else:
        i += 1
      continue
    if tok.startswith("-") and len(tok) > 1:
      for j in range(1, len(tok)):
        ch = tok[j]
        short_opts.add(ch)
        ordered_opts.append(f"-{ch}")
        if ch in short_value_chars:
          if j == len(tok) - 1:
            i += 1
          break
      i += 1
      continue
    positionals.append(tok)
    i += 1
  return long_opts, short_opts, ordered_opts, positionals, has_double_dash


def _has_clean_force_config(configs):
  for item in configs:
    if "=" in item:
      key, val = item.split("=", 1)
      if key.strip().lower() == "clean.requireforce" and val.strip().lower() in {
          "false",
          "0",
          "no",
          "off",
      }:
        return True
  return False


def _has_push_force_config(configs):
  for item in configs:
    if "=" in item:
      key, val = item.split("=", 1)
      k_low = key.strip().lower()
      v_str = val.strip()
      if re.match(r"^remote\..+\.push$", k_low) and v_str.startswith("+"):
        return True
  return False


def _detect_target_90(cmd, state_dir=None):
  """Detects whether command is a Target 90 history ledger operation."""
  is_history_msg = (
      "docs(history):" in cmd
      or ".workflow/history" in cmd
      or "history.json" in cmd
      or "history.md" in cmd
  )
  is_t90_state = False
  if state_dir is None:
    cwd_state = os.path.join(os.getcwd(), ".workflow", "state")
    if os.path.isdir(cwd_state):
      state_dir = cwd_state

  if state_dir and os.path.isdir(state_dir):
    next_action_card = os.path.join(state_dir, "99_next_action.md")
    if os.path.isfile(next_action_card):
      try:
        with open(next_action_card, "r", encoding="utf-8") as f:
          txt = f.read()
        if (
            re.search(r"(?im)^-\s*Active Target:\s*(?:Target\s*90|T90)\b", txt)
            or re.search(r"^\s*-\s*\[>\]\s*(?:Target\s*90|T90)\b", txt, re.M)
            or re.search(
                r"(?im)^#\s*Next Action:.*(?:COMPLETE|make finish satisfied)",
                txt,
            )
        ):
          is_t90_state = True
      except Exception:
        pass
  return is_history_msg, is_t90_state


def _evaluate_git_tokens(
    tokens, has_review, is_history_msg=False, is_t90_state=False
):
  """Returns ('deny'|'force_ask'|'allow', reason) for a single command's tokens."""
  exe, rem = _unwrap_command_tokens(tokens)
  if not exe or exe == "SHELL_C":
    return "allow", ""

  if exe == "gh":
    _, _, _, gh_pos, _ = _split_git_args(
        rem,
        short_value_chars="R",
        long_value_flags=("--repo", "--hostname"),
    )
    if len(gh_pos) >= 2 and gh_pos[0] == "pr" and gh_pos[1] == "merge":
      return (
          "force_ask",
          "Target 75 Landing Gate: gh pr merge requires operator approval. "
          "Make sure that CI is green and the 180-second quiet period passed.",
      )
    return "allow", ""

  if exe != "git":
    return "allow", ""

  subcmd, sub_args, git_configs = _parse_git_subcommand(rem)
  if not subcmd:
    return "allow", ""

  if subcmd == "reset":
    long_opts, _, _, _, _ = _split_git_args(sub_args)
    for bad_flag in ("--hard", "--merge", "--keep"):
      if bad_flag in long_opts:
        return (
            "deny",
            f"Blocked destructive Git command 'git reset {bad_flag}'. "
            "Do not discard uncommitted working-tree changes.",
        )
    return "allow", ""

  if subcmd == "clean":
    _, _, ordered_opts, _, _ = _split_git_args(
        sub_args,
        short_value_chars="e",
        long_value_flags=("--exclude",),
    )
    cfg_force = _has_clean_force_config(git_configs)
    dry_run = False
    force = cfg_force
    interactive = False
    for opt in ordered_opts:
      if opt in {"-n", "--dry-run"}:
        dry_run = True
      elif opt == "--no-dry-run":
        dry_run = False
      elif opt in {"-f", "--force"}:
        force = True
      elif opt == "--no-force":
        force = cfg_force
      elif opt in {"-i", "--interactive"}:
        interactive = True
      elif opt == "--no-interactive":
        interactive = False
    if (force or interactive) and not dry_run:
      return (
          "deny",
          "Blocked destructive Git command 'git clean'. "
          "Do not delete untracked working-tree files automatically.",
      )
    return "allow", ""

  if subcmd == "checkout":
    long_opts, short_opts, _, pos, has_dd = _split_git_args(
        sub_args,
        short_value_chars="bBU",
        long_value_flags=(
            "--orphan",
            "--conflict",
            "--inter-hunk-context",
            "--pathspec-from-file",
        ),
    )
    if (
        any(ch in short_opts for ch in ("f", "p", "2", "3"))
        or any(
            opt
            in {
                "--force",
                "--discard-changes",
                "--patch",
                "--ours",
                "--theirs",
                "--pathspec-from-file",
            }
            or opt.startswith("--pathspec-from-file=")
            for opt in long_opts
        )
    ):
      return (
          "deny",
          "Blocked 'git checkout' with worktree-overwriting flags. "
          "Do not overwrite uncommitted working-tree changes.",
      )
    if has_dd:
      return (
          "deny",
          "Blocked 'git checkout -- <path>'. "
          "Do not overwrite working-tree files with git checkout.",
      )
    if any(
        p in {".", ".."}
        or p.startswith(("./", "../"))
        or any(ch in p for ch in "*?[")
        for p in pos
    ):
      return (
          "deny",
          "Blocked path-based 'git checkout'. "
          "Do not overwrite working-tree files or directories.",
      )
    creating_branch = (
        "b" in short_opts or "B" in short_opts or "--orphan" in long_opts
    )
    if not creating_branch and len(pos) >= 2:
      return (
          "deny",
          "Blocked 'git checkout <tree> <path>'. "
          "Do not overwrite working-tree files with git checkout.",
      )
    return "allow", ""

  if subcmd == "switch":
    long_opts, short_opts, _, _, _ = _split_git_args(
        sub_args,
        short_value_chars="cC",
        long_value_flags=("--orphan", "--conflict"),
    )
    if (
        "f" in short_opts
        or "--force" in long_opts
        or "--discard-changes" in long_opts
    ):
      return (
          "deny",
          "Blocked 'git switch' with force or discard-changes. "
          "Do not discard uncommitted working-tree edits.",
      )
    return "allow", ""

  if subcmd == "restore":
    _, _, ordered_opts, _, _ = _split_git_args(
        sub_args,
        short_value_chars="s",
        long_value_flags=("--source", "--conflict", "--pathspec-from-file"),
    )
    staged = False
    worktree = False
    for opt in ordered_opts:
      if opt in {"-S", "--staged"}:
        staged = True
      elif opt == "--no-staged":
        staged = False
      elif opt in {"-W", "--worktree"}:
        worktree = True
      elif opt == "--no-worktree":
        worktree = False
    if not staged or worktree:
      return (
          "deny",
          "Blocked working-tree 'git restore'. "
          "Only 'git restore --staged' is allowed to unstage index entries.",
      )
    return "allow", ""

  if subcmd == "stash":
    _, _, _, pos, _ = _split_git_args(
        sub_args,
        short_value_chars="m",
        long_value_flags=("--message", "--pathspec-from-file"),
    )
    if pos and pos[0] in {"drop", "clear"}:
      return (
          "deny",
          f"Blocked 'git stash {pos[0]}'. Do not delete stashed changes.",
      )
    return "allow", ""

  if subcmd in {"filter-branch", "filter-repo"}:
    return (
        "deny",
        f"Blocked '{subcmd}'. History-rewriting repository filters are forbidden.",
    )

  if subcmd == "reflog":
    _, _, _, pos, _ = _split_git_args(sub_args)
    if pos and pos[0] in {"delete", "expire"}:
      return (
          "deny",
          f"Blocked 'git reflog {pos[0]}'. Do not erase Git recovery reflogs.",
      )
    return "allow", ""

  if subcmd == "update-ref":
    long_opts, short_opts, _, _, _ = _split_git_args(
        sub_args, short_value_chars="m"
    )
    if "d" in short_opts or "--stdin" in long_opts:
      return (
          "deny",
          "Blocked 'git update-ref'. Do not delete or batch-rewrite Git references.",
      )
    return "allow", ""

  if subcmd == "push":
    long_opts, short_opts, _, pos, _ = _split_git_args(
        sub_args,
        short_value_chars="o",
        long_value_flags=("--repo", "--receive-pack", "--exec", "--push-option"),
    )
    has_force_flag = (
        "f" in short_opts
        or any(
            opt
            in {"--force", "--force-with-lease", "--force-if-includes", "--mirror"}
            or opt.startswith("--force-with-lease=")
            for opt in long_opts
        )
    )
    has_plus_refspec = (
        any(p.startswith("+") and len(p) > 1 for p in pos)
        or _has_push_force_config(git_configs)
    )
    if has_force_flag or has_plus_refspec:
      return (
          "deny",
          "Blocked force-push command. "
          "Force-pushing is forbidden across all branches in the agent workflow.",
      )
    if is_t90_state and (
        "main" in pos
        or "master" in pos
        or any(p.endswith("/main") or p.endswith(":main") for p in pos)
    ):
      return (
          "force_ask",
          "Target 90 History Push Gate: Approve to push history ledger commit to origin/main.",
      )
    if has_review:
      reason = (
          "Target 60 Push Gate: 45_review_approved.md is present. "
          "Make sure that the branch merges cleanly before you approve."
      )
    else:
      reason = (
          "Target 60 Push Gate: 45_review_approved.md is missing in .workflow/state/. "
          "Make sure that review and commit gates passed before you approve."
      )
    return "force_ask", reason

  if subcmd == "rebase":
    return (
        "force_ask",
        "Git Rebase Gate: git rebase rewrites commit history. "
        "Make sure that upstream merge conflicts require a rebase before you approve.",
    )

  if subcmd == "branch":
    long_opts, short_opts, _, _, _ = _split_git_args(
        sub_args,
        short_value_chars="u",
        long_value_flags=("--set-upstream-to",),
    )
    has_force_short = any(ch in short_opts for ch in ("D", "M", "C", "f"))
    if has_force_short or "--force" in long_opts:
      return (
          "force_ask",
          "Git Branch Force Gate: force-deleting, force-renaming, or force-moving "
          "a branch requires operator approval.",
      )
    return "allow", ""

  if subcmd == "commit":
    if is_history_msg:
      return (
          "force_ask",
          "Target 90 History Ledger Gate: Approve to commit history ledger updates.",
      )
    if has_review:
      reason = (
          "Target 50 Commit Gate: 45_review_approved.md is present. "
          "Approve to create the commit."
      )
    else:
      reason = (
          "Target 50 Commit Gate: 45_review_approved.md is missing in .workflow/state/. "
          "Make sure that Target 45 review passed before you approve."
      )
    return "force_ask", reason

  return "allow", ""


def evaluate_git_command(cmd, has_review, state_dir=None):
  """Evaluates all subcommands with deny > force_ask > allow precedence."""
  is_history_msg, is_t90_state = _detect_target_90(cmd, state_dir)
  first_ask_reason = None
  for subcmd in _expand_shell_subcommands(cmd):
    for tokens in _tokenize_subcommand(subcmd):
      decision, reason = _evaluate_git_tokens(
          tokens,
          has_review,
          is_history_msg=is_history_msg,
          is_t90_state=is_t90_state,
      )
      if decision == "deny":
        return {"decision": "deny", "reason": reason}
      if decision == "force_ask" and first_ask_reason is None:
        first_ask_reason = reason
  if first_ask_reason is not None:
    return {"decision": "force_ask", "reason": first_ask_reason}
  return {"decision": "allow"}


def resolve_state_dir(payload):
  """Finds the active state directory from workspacePaths or artifactDirectoryPath."""
  workspace_paths = payload.get("workspacePaths") or []
  for ws in workspace_paths:
    candidate = os.path.join(ws, ".workflow", "state")
    if os.path.isdir(candidate):
      return candidate

  artifact_dir = payload.get("artifactDirectoryPath", "")
  if artifact_dir:
    brain_state = os.path.join(artifact_dir, "state")
    if os.path.isdir(brain_state):
      return brain_state

  if workspace_paths:
    return os.path.join(workspace_paths[0], ".workflow", "state")

  return os.path.join(os.getcwd(), ".workflow", "state")


def is_database_command(cmd):
  if "DATABASE_URL" in cmd or "DB_HOST" in cmd:
    return True
  for tool in DB_TOOLS:
    if re.search(rf"(?:^|[^a-zA-Z0-9_-]){re.escape(tool)}(?:$|[^a-zA-Z0-9_-])", cmd):
      return True
  return False


def evaluate_tool_call(payload):
  tool_call = payload.get("toolCall", {})
  tool_name = tool_call.get("name", "")
  args = tool_call.get("args", {})

  if tool_name != "run_command":
    return {"decision": "allow"}

  cmd = args.get("CommandLine", "").strip()
  if not cmd:
    return {"decision": "allow"}

  # 1. Production database guard
  db_cfg = load_database_config(payload)
  is_safe, deny_reason = evaluate_database_safety(cmd, db_cfg)
  if not is_safe:
    return {
        "decision": "deny",
        "reason": deny_reason,
    }

  # 2. Destructive Git guards and milestone pause gates
  state_dir = resolve_state_dir(payload)
  review_card = os.path.join(state_dir, "45_review_approved.md")
  has_review = os.path.isfile(review_card)
  return evaluate_git_command(cmd, has_review, state_dir=state_dir)


def main():
  try:
    input_text = sys.stdin.read()
    if not input_text.strip():
      print(json.dumps({"decision": "allow"}))
      return

    payload = json.loads(input_text)
    result = evaluate_tool_call(payload)
    print(json.dumps(result))
  except Exception as exc:
    print(json.dumps({"decision": "allow", "reason": f"Hook error: {exc}"}))


if __name__ == "__main__":
  main()
