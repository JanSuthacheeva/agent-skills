# Reproducing a bug end to end

Read this in step 2, for a reproduction someone else can rerun.

## By kind of surface

**Command line.** Run the real binary or entry point with the reporter's
arguments, in a fresh state you control: point it at a scratch data file
or directory through its config or environment, never at the user's real
data. Record each command and its full output, including the exit code.

**HTTP API.** Start the application the way the project runs it locally
and send the request with `curl` or the project's HTTP client, with the
reporter's payload and headers. Record the request, the status, the body
and the server log for that request.

**Browser page.** Drive the page with a browser tool if one is available,
otherwise ask the user to run the steps while you watch the server log.
Use the reporter's browser and viewport where they matter. Record each
click and input, what the page showed, and the console and network errors.

**Background job or queue.** Trigger the job the way production does -
the event, the schedule, the queued message - rather than calling its
handler directly. Run a worker locally if the project has one, and record
the job's input, its log and the state it left behind.

## Data-dependent bugs

When a bug only shows with certain data, build that data through the
application's own commands or endpoints, step by step as the reporter
did, rather than writing it into storage by hand: how the data came to be
is often the bug. If the reporter can share their data, use a copy of it.
Inspect the stored state after each step to see which step first leaves
it wrong.

## Intermittent bugs

- Run the reproduction in a loop and count: "fails 7 of 50 runs" is a
  reproduction, "sometimes fails" is not.
- Vary one thing at a time: timing, concurrency, ordering, random seeds,
  the clock, the time zone, the locale.
- Fix what can be fixed for the run - a seed, a frozen clock, a single
  worker - and see whether the failure rate changes. A change in the rate
  is evidence about the cause.

## Recording the reproduction

Write it so it can be pasted: the setup, then each step as a command or
action, then the observed output quoted exactly. The fix plan's
`## Reproduction` section takes it as it is, and the plan's last task
reruns it to show the fix works.
