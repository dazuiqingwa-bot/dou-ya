# OpenClaw Session Stability Notes

Updated: 2026-03-21
Purpose: baseline notes for OpenClaw repair / session health checks on this machine.

## What Was Fixed

### 1. `invalid_workspace_selected` on main session

Symptoms:
- Main Session opened but appeared to lose memory.
- Web UI showed `{"detail":{"code":"invalid_workspace_selected"}}`.
- Failures happened before token usage reached the model.

Confirmed root cause:
- The `openai-codex` OAuth account/workspace binding had gone stale.
- OpenClaw was rejected upstream before normal model execution.

Fix applied:
- Refreshed `openai-codex` OAuth.
- Restarted Gateway.
- Verified the same main session could run successfully again.

### 2. Heartbeat polluting main-session behavior

Symptoms:
- Heartbeat and main session were too tightly coupled.
- Main session state became confusing and fragile.

Fix applied:
- Heartbeat was isolated away from the main session flow.
- Current heartbeat config is intended to reduce cross-session contamination.

### 3. Telegram direct session metadata drift

Symptoms:
- `agent:main:telegram:direct:8058767394` had Telegram semantics but was indexed as `webchat`.

Fix applied:
- Repaired `sessions.json` metadata so the Telegram direct session is labeled as Telegram again.
- Verified the Telegram session itself could run successfully.

## Important Findings

### 1. `sessionKey` is stable; `sessionId` is not

OpenClaw keeps conversation continuity primarily by `sessionKey`.

Examples on this machine:
- Main session key: `agent:main:main`
- Heartbeat key: `agent:main:heartbeat`
- Telegram direct key: `agent:main:telegram:direct:8058767394`

`sessionId` is only the current transcript id behind that key.
It can rotate when a reset policy triggers.

Practical meaning:
- If an integration, UI, browser tab, or automation keeps an old `sessionId`, it may point at stale state.
- Future-safe references should prefer `sessionKey` semantics, not old `sessionId` assumptions.

### 2. Default direct-session daily rollover is risky for UI continuity

OpenClaw docs confirm that direct sessions normally roll to a new `sessionId` after the daily reset boundary (default 4:00 AM local time) on the next message.

This can create the illusion that:
- memory disappeared,
- a browser tab opened the wrong session,
- a saved session reference suddenly became invalid.

### 3. Browser/UI confusion is not only a browser bug

The local OpenClaw browser extension keeps attachment/session tracking in runtime/session storage.
The larger practical problem on this machine was session-id drift combined with UI/session references, not a standalone long-term browser cache corruption issue.

## Hardening Applied On This Machine

Current session policy in `openclaw.json`:

```json
{
  "session": {
    "dmScope": "per-channel-peer",
    "resetByType": {
      "direct": {
        "mode": "idle",
        "idleMinutes": 10080
      }
    }
  }
}
```

Meaning:
- DMs are separated by channel + peer.
- Direct sessions no longer rotate daily by default.
- Direct sessions now rotate only after 7 days of inactivity.

Why this helps:
- Main / Web UI / Telegram direct sessions keep a stable current transcript much longer.
- Old-session-id confusion should happen far less often.
- New ports, new browser tabs, and future agent tooling have a more stable baseline.

## Current Known Risks

### 1. CLI `--session-id` can be misleading in practice

Observed on this machine:
- A direct CLI test using an old Telegram session id landed in main-session transcript instead of the intended Telegram transcript.
- A direct call using the explicit session key hit the correct Telegram session.

Working rule:
- Do not trust old `sessionId` values as durable routing handles.
- Prefer session-key-based reasoning whenever possible.

### 2. `sessionId` / `sessionFile` drift can exist legitimately

A session store entry may show:
- the same `sessionKey`,
- a newer current `sessionId`,
- but an older `sessionFile` path still backing the transcript.

This is confusing but not automatically broken.
It must be interpreted carefully during repair work.

### 3. Gateway is the source of truth

Manual edits to `sessions.json` are possible, but Gateway may rewrite entries as sessions run.
After session-related edits, restart Gateway and re-check health.

## Repair Checklist For Future OpenClaw Work

When session memory or routing looks wrong, check in this order:

1. `openclaw health`
2. `openclaw sessions --json`
3. Inspect `~/.openclaw/agents/<agent>/sessions/sessions.json`
4. Compare `sessionKey`, `sessionId`, `sessionFile`, `deliveryContext.channel`, and `origin.provider`
5. Inspect recent transcript tail in the matching `*.jsonl`
6. Inspect `~/.openclaw/logs/gateway.err.log`
7. If upstream auth is suspicious, refresh `openai-codex` OAuth and restart Gateway
8. If metadata is wrong, fix it only after backing up both `sessions.json` and the transcript

## Best Practices For New Agents

### Recommended path

1. Create each new agent with a clear, dedicated purpose.
2. Give each agent its own workspace context and keep responsibilities narrow.
3. Keep `dmScope` as `per-channel-peer` unless you intentionally want shared DM buckets.
4. Keep direct-session reset on long idle, not daily rollover.
5. Test new agents with a real one-turn smoke test immediately after creation.
6. Restart Gateway after config/auth/session-structure changes.
7. Re-open or refresh Web UI tabs after Gateway restart.

### Avoid these mistakes

- Do not build tooling that depends on an old `sessionId` staying valid forever.
- Do not mix heartbeat responsibilities into main operational sessions.
- Do not assume Web UI confusion means transcript loss; inspect `sessionKey` vs `sessionId` first.
- Do not edit session files without making backups first.
- Do not create many broad, overlapping agents before the routing model is stable.

## Safe Baseline For This Machine

Use this machine as if these rules are true:
- `sessionKey` is the durable identity.
- `sessionId` is a replaceable current transcript pointer.
- Gateway restart is required after important session/auth/config repairs.
- New direct agents should prefer long idle resets, not daily resets.
- Browser/UI confusion should be treated as a routing/state problem first, not as immediate memory destruction.

## Suggested Thread Use

This conversation thread can be treated as the dedicated OpenClaw repair / verification thread.
Use it for:
- session drift checks,
- auth breakages,
- routing anomalies,
- heartbeat isolation verification,
- new-agent hardening before production use.

---

## Audit Supplement — 2026-03-22 (Round 2 Read-Only Verification)

Purpose:
- verify the 2026-03-21 repair baseline,
- identify remaining stability risks before any new project expansion,
- create a durable pre-fix checkpoint for future OpenClaw / Codex / Claude Code repair work.

### Commands run

- `openclaw status`
- `openclaw -v`
- `openclaw security audit --deep`
- `openclaw update status`
- `openclaw health --json`
- `openclaw status --all`
- read-only inspection of:
  - `~/.openclaw/openclaw.json`
  - `~/.openclaw/agents/main/sessions/sessions.json`
  - `~/.openclaw/logs/gateway.err.log`
  - `~/.openclaw/logs/gateway.log`
  - workspace `MEMORY.md` and `memory/`
  - local OpenClaw docs for `operator.read`

### Verified healthy / improved

1. **Main / heartbeat / Telegram session separation is intact**
   - `sessions.json` currently contains exactly:
     - `agent:main:main`
     - `agent:main:heartbeat`
     - `agent:main:telegram:direct:8058767394`
   - Telegram session metadata now matches Telegram semantics again:
     - `deliveryContext.channel = telegram`
     - `origin.provider = telegram`

2. **Long-idle direct-session policy is still in place**
   - Current config still shows:
     - `session.dmScope = per-channel-peer`
     - `session.resetByType.direct.mode = idle`
     - `session.resetByType.direct.idleMinutes = 10080`
   - This confirms daily 4 AM rollover is no longer the default direct-session behavior on this machine.

3. **Gateway is running locally and serving the active system**
   - Gateway service is active.
   - Main session is updating normally.
   - Heartbeat is isolated to its own session.

4. **Version status is clearer than the compact output first suggested**
   - `openclaw -v` → `2026.3.13`
   - `openclaw status --all` reports `Update: pnpm · npm latest 2026.3.13`
   - Practical conclusion: current install appears to already match the latest npm-visible version at audit time.

### Remaining issues / risks

1. **Gateway diagnostics are degraded by missing `operator.read` scope**
   - `openclaw status`, `status --all`, and deep security audit all report:
     - `missing scope: operator.read`
   - Local docs confirm this means the gateway is reachable, but detail RPCs are scope-limited rather than fully unavailable.
   - Practical effect:
     - control-plane diagnostics are incomplete,
     - some status/config/presence RPCs fail from the current operator connection,
     - future debugging is harder than it should be.
   - This is a visibility / observability problem, not evidence that the gateway process is down.

2. **Telegram channel health output is confusing because config appears to use legacy token shape**
   - `status --all` shows Telegram is OK and token source is `config`.
   - `health --json` showed Telegram probe OK but `running: false` / `tokenSource: none`.
   - Raw config inspection shows Telegram is stored as legacy direct config:
     - `channels.telegram.botToken = ...`
     - not multi-account `channels.telegram.accounts.default...`
   - Most likely interpretation:
     - channel is usable,
     - but some health/status surfaces interpret the legacy config differently, creating misleading output.
   - This is a stability-observability issue more than a confirmed delivery outage.

3. **OpenClaw memory files exist, but platform-level memory indexing is not clearly active**
   - Workspace files are present:
     - `MEMORY.md`
     - `memory/*.md`
   - But `openclaw status` reported memory like `0 files · 0 chunks`.
   - Practical meaning:
     - durable notes exist at the file layer,
     - but OpenClaw’s higher-level memory index / status reporting is not clearly ingesting them.
   - This can contribute to the operator feeling that “memory is gone” even when the files still exist.

4. **Security audit warnings still need cleanup**
   - `gateway.trustedProxies` is empty (acceptable if Control UI stays local-only, but should be explicit).
   - `gateway.nodes.denyCommands` contains ineffective command IDs:
     - `camera.snap`
     - `camera.clip`
     - `screen.record`
     - `contacts.add`
     - `calendar.add`
     - `reminders.add`
     - `sms.send`
   - These do not currently enforce what they appear to enforce.

5. **Telegram group policy is effectively closed by empty allowlists**
   - audit warning:
     - `channels.telegram.groupPolicy = allowlist`
     - `groupAllowFrom` and `allowFrom` are empty
   - Practical effect:
     - all Telegram group messages will be silently dropped.
   - This is fine if intentional, but should be treated as a deliberate policy choice, not an accidental half-configured state.

6. **Config audit trail indicates historical command-line secret exposure risk**
   - `config-audit.jsonl` contains historical command invocation traces.
   - At least one past onboarding command included an API key via CLI args.
   - This is not the current session-stability root cause, but it is important operational debt and should be considered during later security cleanup.

### Working conclusions after Round 2

1. The major 2026-03-21 session continuity repair appears to be holding.
2. The most urgent remaining work is no longer transcript identity drift itself.
3. The highest-value next step is to improve **observability and config clarity**:
   - fix operator scope visibility,
   - normalize Telegram config shape if appropriate,
   - decide whether Telegram group allowlist-empty is intentional,
   - inspect why memory status does not reflect existing memory files.
4. Do not expand system complexity (more skills / more projects / more routing assumptions) until these visibility issues are understood and, where needed, repaired.

### Proposed next repair order

1. Repair / clarify `operator.read` diagnostics path
2. Normalize or intentionally keep Telegram legacy config, but document the choice
3. Decide whether Telegram group dropping is desired behavior
4. Investigate memory indexing / status mismatch
5. Clean up ineffective `denyCommands` entries
6. Later: security hygiene pass for audit/log exposure history

---

## Audit Supplement — 2026-03-23 (Memory Repair Follow-up)

Purpose:
- continue the 2026-03-22 stability audit,
- resolve the semantic memory failure that made the assistant feel "memory-less",
- record a durable repair path for future OpenClaw / Codex / Claude Code sessions.

### What was already known before repair

Workspace memory files existed and were readable:
- `~/.openclaw/workspace/MEMORY.md`
- `~/.openclaw/workspace/memory/*.md`

But semantic memory status initially showed:
- `Indexed: 0/13 files · 0 chunks`
- `Provider: none (requested: auto)`
- `Embeddings: unavailable`

We also confirmed:
- `~/.openclaw/memory/main.sqlite` already existed,
- but it was effectively empty before provider repair (`files=0`, `chunks=0`).

### Root cause of memory failure

The memory index was not broken because files were missing.
It was broken because **no embedding provider was available** for semantic indexing.

Important observed behavior on this machine:
- OpenAI Codex OAuth for chat/model use does **not** satisfy memory embeddings.
- When no embedding provider is available, `openclaw memory index --force` can print an update message but still skip sync in FTS-only mode.
- The decisive log line was:
  - `Skipping memory file sync in FTS-only mode (no embedding provider)`

### Repair performed

1. An OpenAI API key was added on the machine for Gateway/CLI visibility.
2. Gateway was restarted.
3. Memory provider availability was re-checked until status showed:
   - `Provider: openai`
   - `Model: text-embedding-3-small`
   - `Embeddings: ready`
4. Memory indexing was forced again:
   - `openclaw memory index --agent main --force --verbose`
5. Store contents and search behavior were then verified directly.

### Verified post-repair state

Direct SQLite check on `~/.openclaw/memory/main.sqlite` showed:
- `files = 13`
- `chunks = 16`
- `embedding_cache = 16`

CLI status after repair showed:
- `Indexed: 13/13 files · 16 chunks`
- `Provider: openai`
- `Model: text-embedding-3-small`
- `Embeddings: ready`
- `Vector: ready`
- `FTS: ready`

Live semantic search also returned expected results, for example:
- `openclaw memory search "禾禾 学习系统"`
  returned a relevant snippet from `MEMORY.md`.

### Practical conclusion

Semantic memory is now working again on this machine.
The assistant now has:
- file-layer memory (`MEMORY.md`, `memory/*.md`), and
- semantic memory index (`main.sqlite`) aligned again.

### Important lessons / future repair notes

1. **Do not assume Codex/OpenAI OAuth covers memory embeddings.**
   It covers chat/model access, not memory indexing.

2. **If memory status shows files present in scan but indexed files/chunks remain zero, check provider readiness first.**
   Use:
   - `openclaw memory status --agent main --deep`

3. **A successful-looking `memory index` run is not enough.**
   Confirm with both:
   - `openclaw memory status --agent main --deep`
   - direct SQLite counts if needed

4. **Ground truth for repaired memory on this machine is:**
   - `~/.openclaw/memory/main.sqlite`
   - `files > 0`
   - `chunks > 0`
   - working `openclaw memory search ...`

5. **If memory regresses again**, check in this order:
   1. `openclaw memory status --agent main --deep`
   2. confirm provider is not `none`
   3. confirm embeddings are `ready`
   4. `openclaw memory index --agent main --force --verbose`
   5. inspect `~/.openclaw/memory/main.sqlite`
   6. run a real `openclaw memory search "..."`

### Remaining open items after memory repair

Still not fully closed:
1. `operator.read` remains degraded for some CLI/probe paths even though the web Control UI recovered in practice.
2. Telegram config is still legacy single-account shape (functional, but not yet normalized).
3. Telegram group policy is still allowlist-empty (not a current priority unless Telegram group usage becomes intentional).
4. Ineffective `gateway.nodes.denyCommands` entries still need cleanup later.

---

## Incident Record — 2026-03-24 (Upgrade broke Control UI, repaired with local source build)

Purpose:
- document the 2026-03-24 post-upgrade Browser / Control UI failure,
- preserve the exact evidence chain,
- record the working recovery path for future OpenClaw upgrades.

### Symptoms

Observed after upgrading OpenClaw to `2026.3.22`:
- Web UI / Browser side appeared to "not move" or failed to send normally.
- Gateway health could pass, but Browser / agent RPCs were unstable during the broken window.
- Browser/Web UI previously connected as old client `openclaw-control-ui webchat v2026.3.13`.
- Earlier during the broken period, Web UI requests hit:
  - `Error: Channel is required when multiple channels are configured: telegram, feishu`
- Gateway logs also reported:
  - `Missing Control UI assets at /opt/homebrew/lib/node_modules/openclaw/dist/control-ui/index.html`

### Confirmed root cause

This was not a session-memory failure and not a GPT Business / provider-auth issue.

Confirmed cause:
1. The published npm package `openclaw@2026.3.22` on this machine did not include bundled `dist/control-ui/index.html`.
2. The global installed package also lacked the matching build helper `scripts/ui.js`, so `pnpm ui:build` could not be executed inside the installed package itself.
3. Because bundled Control UI assets were missing, Browser / Web UI remained effectively stuck on the older client path until a local source build was provided.
4. The old Web UI client (`v2026.3.13`) was incompatible with the newer multi-channel behavior and produced misleading channel-selection errors.

### Evidence captured

Package/install evidence:
- CLI version after reinstall still showed:
  - `OpenClaw 2026.3.22 (4dcc39c)`
- Installed package path:
  - `/opt/homebrew/lib/node_modules/openclaw`
- Missing asset confirmed at install location:
  - `/opt/homebrew/lib/node_modules/openclaw/dist/control-ui/index.html`
- Published package inspection showed only JS helpers like:
  - `dist/control-ui-assets-*.js`
  - `dist/control-ui-shared-*.js`
  - but not bundled `dist/control-ui/index.html`

Runtime/log evidence:
- `gateway.err.log` repeatedly showed:
  - `Missing Control UI assets at /opt/homebrew/lib/node_modules/openclaw/dist/control-ui/index.html`
- Before repair, Browser/Web UI connections appeared as:
  - `client=openclaw-control-ui webchat v2026.3.13`
- After repair, Browser/Web UI reconnected as:
  - `client=openclaw-control-ui webchat v2026.3.22`
- Final confirming reconnect on this machine:
  - `2026-03-24T07:40:32.203+08:00 [ws] webchat connected ... client=openclaw-control-ui webchat v2026.3.22`

### Failed repair path that should be remembered

These attempts were useful diagnostically but are not the final fix:

1. Reinstalling global package `openclaw@2026.3.22`
- This repaired LaunchAgent metadata and service versioning,
- but did **not** restore bundled Control UI assets,
- because the package itself was missing the required static UI output.

2. Running `pnpm ui:build` inside the global installed package
- failed because the installed package did not contain `scripts/ui.js`.

3. Running the source `ui:build` helper in its default build path
- failed initially because it installed production deps only,
- which skipped `vite`, causing `sh: vite: command not found`.

### Working recovery path

The successful fix was to build the Control UI from the exact matching source tag and point Gateway at that local build.

Applied steps:
1. Confirmed matching source tag:
   - `v2026.3.22`
2. Cloned source checkout to:
   - `/Users/dazuiqingwa/Documents/Playground/openclaw-src-2026.3.22`
3. Installed full dependencies non-interactively using pnpm via npm exec.
4. Built the UI directly from the source checkout.
5. Verified local UI output exists at:
   - `/Users/dazuiqingwa/Documents/Playground/openclaw-src-2026.3.22/dist/control-ui/index.html`
6. Set config:
   - `gateway.controlUi.root = /Users/dazuiqingwa/Documents/Playground/openclaw-src-2026.3.22/dist/control-ui`
7. Restarted Gateway.
8. Verified Browser/Web UI later reconnected as `v2026.3.22`.

### Files and paths involved

Source checkout:
- `/Users/dazuiqingwa/Documents/Playground/openclaw-src-2026.3.22`

Local built Control UI:
- `/Users/dazuiqingwa/Documents/Playground/openclaw-src-2026.3.22/dist/control-ui`
- `/Users/dazuiqingwa/Documents/Playground/openclaw-src-2026.3.22/dist/control-ui/index.html`

Config changed:
- `/Users/dazuiqingwa/.openclaw/openclaw.json`

Config backup created during this repair:
- `/Users/dazuiqingwa/.openclaw/openclaw.json.controlui-bak-20260324-065329`

Primary evidence logs:
- `/Users/dazuiqingwa/.openclaw/logs/gateway.log`
- `/Users/dazuiqingwa/.openclaw/logs/gateway.err.log`
- `/tmp/openclaw/openclaw-2026-03-24.log`

### Verified end state

After the local-source Control UI repair:
- `openclaw gateway status` → `RPC probe: ok`
- `openclaw health` returned healthy channel/agent state again
- `Missing Control UI assets` stopped appearing in the latest gateway logs
- Browser/Web UI successfully reconnected as:
  - `openclaw-control-ui webchat v2026.3.22`

### Future upgrade rule

If a future OpenClaw upgrade breaks Browser / Web UI again, check in this order:

1. `openclaw --version`
2. `openclaw gateway status`
3. inspect `gateway.err.log` for `Missing Control UI assets`
4. verify whether installed package contains:
   - `dist/control-ui/index.html`
5. inspect latest `webchat connected` log line to confirm actual UI client version
6. if the package again ships without bundled Control UI assets:
   - build from the exact matching source tag,
   - set `gateway.controlUi.root` to the local built `dist/control-ui`,
   - restart Gateway,
   - refresh Browser / Web UI and confirm reconnect version in logs

### Practical interpretation

For this machine, the Browser/UI layer should now be treated as repaired.

Important distinction:
- Session stability issues and memory-routing issues were earlier problems.
- This 2026-03-24 incident was mainly a **packaging / frontend asset delivery failure** after upgrade.
- The successful recovery path is now documented and repeatable.

---

## Naming Baseline — 2026-03-24 (Agent vs Port vs Session)

Purpose:
- freeze a simple naming model so future upgrades do not re-confuse Agent / port / session,
- document the exact display targets now considered correct on this machine,
- record the proven minimum repair path when names drift again.

### Concept rule (must not be mixed again)

- **Agent** = the acting主体 / worker
- **Port / entry** = where that Agent is reached from
- **Session** = one concrete conversation record under that entry

Working rule:
- Do **not** treat a Telegram session as if it were its own Agent.
- If a new workflow needs independent responsibility, create a new **Agent**.
- Do **not** create pseudo-Agents by mistaking channel sessions for Agents.

### Current display targets (authoritative)

These are the intended human-facing names now:

- `agent:main:main` → **ASA · Web**
- `agent:main:telegram:direct:8058767394` → **ASA · Telegram**
- `agent:main:heartbeat` → **ASA · Heartbeat**
- `agent:douya:feishu:direct:ou_216a3f71ce740715ecb08de972fb0749` → **豆芽 · Feishu**

### What was actually broken

Observed on this machine after the 2026-03-24 repair cycle:

1. `agent:main:main` still existed, but its `origin.label/from/to` had been polluted to `heartbeat`.
2. `agent:main:telegram:direct:8058767394` did accept `origin.label = "ASA · Telegram"`, but the UI still showed:
   - `telegram:g-agent-main-telegram-direct-8058767394`
3. This proved that not all rows use the same name source.

### Confirmed naming-source behavior

#### 1. Web / heartbeat rows

For the current local setup, these rows can be repaired by editing session-store metadata in:
- `~/.openclaw/agents/main/sessions/sessions.json`

Confirmed effective fields:
- `origin.label`
- for Web specifically, `origin.from` / `origin.to` should also reflect Web semantics rather than `heartbeat`

Applied repair on this machine:
- Main/Web:
  - `label = ASA · Web`
  - `from = webchat:openclaw-control-ui`
  - `to = webchat:openclaw-control-ui`
- Heartbeat:
  - `label = ASA · Heartbeat`

#### 2. Telegram direct row

This row is **not** reliably controlled by `origin.label` alone.

Confirmed behavior observed on this machine:
- `origin.label = "ASA · Telegram"` was present in `sessions.json`
- but UI still preferred a fallback name derived from session metadata
- effective minimum fix was to add top-level:
  - `displayName = "ASA · Telegram"`

Practical rule:
- For Telegram direct sessions on this machine, do **not** assume `origin.label` is enough.
- If display is wrong, check for / set top-level `displayName` first.

#### 3. Douya / Feishu row

This row lives in a different session store:
- `~/.openclaw/agents/douya/sessions/sessions.json`

Confirmed effective field:
- `origin.label = 豆芽 · Feishu`

### Minimum repair checklist when names drift again

1. Back up the relevant `sessions.json` first.
2. Check `sessionKey` before touching labels:
   - do not recreate sessions if the key is still correct
3. Repair by target:
   - Main/Web → fix `origin.label/from/to`
   - Heartbeat → fix `origin.label`
   - Telegram direct → check/set top-level `displayName` first; then verify `origin.label`
   - Douya/Feishu → fix label in Douya's own `sessions.json`
4. Restart Gateway.
5. Refresh Control UI tabs.
6. Re-check whether the names hold after restart.

### Upgrade/post-repair verification items (required on this machine)

After future OpenClaw upgrades, UI repairs, or session-store interventions, explicitly verify:

1. `ASA · Web` is shown as Web, not heartbeat
2. `ASA · Telegram` is shown as Telegram, not a generated fallback key
3. `ASA · Heartbeat` remains isolated and clearly labeled heartbeat
4. `豆芽 · Feishu` remains in Douya's lane and is not shown as raw OpenID
5. `sessionKey` values remain stable even if display names drift

### What is fixed vs not yet root-fixed

Fixed now:
- human-facing naming is restored on this machine
- the minimal repair path is known and repeatable

Not yet root-fixed:
- the underlying OpenClaw naming logic that lets Telegram direct rows fall back to generated names
- any future runtime process that may rewrite session metadata during upgrades or rebuilds

Practical conclusion:
- treat this as a **stable operational repair**, not yet a guaranteed source-level permanent fix
- if the naming problem recurs, first verify fields and repair path above before assuming transcript loss or Agent corruption

### Local correction script (added 2026-03-24)

A repeatable local correction script now exists at:
- `~/.openclaw/workspace/scripts/fix-openclaw-session-names.py`

Purpose:
- stop relying on memory or ad-hoc manual edits when names drift again
- rewrite the currently expected human-facing names in both session stores

Current correction targets:
- `agent:main:main` → `ASA · Web`
- `agent:main:heartbeat` → `ASA · Heartbeat`
- `agent:main:telegram:direct:8058767394` → `ASA · Telegram`
- `agent:douya:feishu:direct:ou_216a3f71ce740715ecb08de972fb0749` → `豆芽 · Feishu`

Operational use:
1. Run the script
2. Restart Gateway
3. Refresh Control UI and verify names

This is not the same as a source-level fix, but it upgrades the problem from “manual memory-based repair” to a repeatable local correction procedure.
