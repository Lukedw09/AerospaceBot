Tool calls can do arithmetic and unit conversion, and the daily cap fails closed when usage tracking is missing or DynamoDB errors. No new formulas or skills.

## Calculate

- `calculate` is on `/mcp` and `/api/chat`.
- Expressions use a restricted AST walker, not `eval` or `exec`: `+ - * / ** %`, parentheses, `sqrt`, trig and inverse trig, `atan2`, `log`, `log10`, `exp`, `radians`, `degrees`, `pi`, and `e`.
- Unit conversion covers length, time, speed, acceleration, mass, force, pressure, angle, angular speed, temperature, energy, and power.
- Symbols and SI prefixes are case-sensitive (`m` milli, `M` mega). Ambiguous spellings such as `MM` and `mpa` error instead of guessing. Temperature readings below absolute zero error.
- Exponents above 1000, results over 10,000 digits, and evaluations past about one second are rejected. `9**9**9` returns immediately.
- The tool prints `input`, `result`, and `units` for Show details.
- The chat prompt requires `calculate` for any arithmetic or unit conversion, including seconds to minutes, km/s to ft/s, and degrees to radians.

## Usage cap

- An unconfigured usage store, or a DynamoDB error while checking or recording a call, refuses the tool call. The previous behavior allowed the call when `USAGE_TABLE` was empty, and a mid-request DynamoDB error escaped as `ClientError` (the chat loop then showed "that tool failed").
- `USAGE_CAP_DEV_BYPASS=1` is the local bypass. The process refuses to start when that variable is set and `AWS_LAMBDA_FUNCTION_NAME` is set.
- `AUTH_DISABLED` still skips sign-in. It does not skip the cap.
- `OWNER_UNLIMITED_EMAILS` is set in `template.yaml`. If it is empty at runtime, `lukedw09@gmail.com` stays on the unlimited plan.

## Checks

- Calculate, usage-cap, chat, set-plan, plugin, and program tests passed.

**Full Changelog**: https://github.com/Lukedw09/AerospaceBot/compare/v11.3.0...v11.4.0
