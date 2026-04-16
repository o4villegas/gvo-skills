# Billy Persona Scripts — Interaction Reference

> Read this before spawning sub-agents. Each persona has a distinct behavior model
> and specific interaction payloads. Agents must stay in character — mixing personas
> dilutes test coverage.

## Table of Contents

1. Fumbles — The Button Masher
2. Backwards Bob — The Reverse Navigator
3. Copy-Paste Carol — The Input Terrorist
4. Rage Clicker Rick — The Impatient One
5. Zero-Knowledge Zara — The Complete Novice
6. Universal Payloads — Shared test inputs

---


---

## Test Harness Template (MANDATORY)

Every sub-agent MUST structure its test session as a Node.js script using this template.
Do not improvise — write the script, run it with `node`, collect the output.

```javascript
// billy-test-[persona].mjs
import puppeteer from 'puppeteer';

const APP_URL = process.argv[2] || 'http://localhost:5173';
const FINDINGS = [];
const CONSOLE_ERRORS = [];
const PAGE_ERRORS = [];
let interactionCount = 0;
const MAX_INTERACTIONS = 12;

const browser = await puppeteer.launch({headless: 'new', args: ['--no-sandbox']});
const page = await browser.newPage();
await page.setViewport({width: 1280, height: 800});

// Console capture — MUST be registered before any navigation
page.on('console', msg => {
  if (msg.type() === 'error' || msg.type() === 'warning') {
    CONSOLE_ERRORS.push({type: msg.type(), text: msg.text()});
  }
});
page.on('pageerror', err => {
  PAGE_ERRORS.push({message: err.message, stack: err.stack?.split('\n')[0]});
});

await page.goto(APP_URL, {waitUntil: 'networkidle2', timeout: 15000});
const baselineErrors = CONSOLE_ERRORS.length;

// === PERSONA INTERACTIONS START HERE ===
// Each interaction follows this pattern:

async function interact(description, action, expected) {
  if (interactionCount >= MAX_INTERACTIONS) return;
  interactionCount++;
  const consolesBefore = CONSOLE_ERRORS.length;
  const pagesBefore = PAGE_ERRORS.length;

  try {
    await action();
  } catch (err) {
    // Interaction itself failed — this IS a finding
    FINDINGS.push({
      id: interactionCount,
      description,
      severity: 'P1-BROKEN',
      expected,
      actual: `Interaction threw: ${err.message}`,
      consoleErrors: CONSOLE_ERRORS.slice(consolesBefore),
      pageErrors: PAGE_ERRORS.slice(pagesBefore),
    });
    await page.screenshot({path: `/tmp/billy-interaction-${interactionCount}.png`, fullPage: true});
    return; // prevent double-report with newErrors check below
  }

  await page.screenshot({path: `/tmp/billy-interaction-${interactionCount}.png`, fullPage: true});

  const newConsoles = CONSOLE_ERRORS.length - consolesBefore;
  const newPages = PAGE_ERRORS.length - pagesBefore;
  if (newConsoles + newPages > 0) {
    FINDINGS.push({
      id: interactionCount,
      description,
      severity: 'P2-ANNOYING',
      expected,
      actual: `${newConsoles + newPages} new console error(s)`,
      consoleErrors: CONSOLE_ERRORS.slice(consolesBefore),
      pageErrors: PAGE_ERRORS.slice(pagesBefore),
    });
  }
}

try {
// === PERSONA INTERACTIONS — Replace with persona-specific calls ===
// Example (Fumbles):
// await interact(
//   'Submit empty form',
//   async () => { await page.click('button[type="submit"]'); },
//   'Validation error shown, form not submitted'
// );

// === END INTERACTIONS ===

// Output findings as JSON for the orchestrator to collect
console.log(JSON.stringify({
  persona: '[PERSONA_NAME]',
  url: APP_URL,
  totalInteractions: interactionCount,
  findings: FINDINGS,
  totalConsoleErrors: CONSOLE_ERRORS.length - baselineErrors,
  totalPageErrors: PAGE_ERRORS.length,
}, null, 2));

} finally {
  await browser.close();
}
```

**Each sub-agent**: copies this template, fills in the persona-specific `interact()` calls
from the tables below, runs it with `node billy-test-[persona].mjs [URL]`, and returns
the JSON output + screenshot files.

**The orchestrator** (lead agent) collects JSON from all 3 sub-agents and proceeds to
Phase 2 dedup.

---

## Persona-Specific `interact()` Calls

### Fumbles — Ready-to-Paste Interactions

```javascript
// 1. Submit without filling anything
await interact('Submit empty form', async () => {
  const submit = await page.evaluateHandle(() =>
    [...document.querySelectorAll('button, [type="submit"]')].find(b => /submit|save|send/i.test(b.textContent))
  );
  if (submit) await submit.click();
}, 'Validation errors shown, form not submitted');

// 2. Rapid-fire submit (5 clicks in <1 second)
await interact('Rapid-fire submit', async () => {
  const submit = await page.evaluateHandle(() =>
    [...document.querySelectorAll('button, [type="submit"]')].find(b => /submit|save|send/i.test(b.textContent))
  );
  if (submit) await Promise.all([submit.click(), submit.click(), submit.click(), submit.click(), submit.click()]);
}, 'Button disabled after first click, no duplicate submissions');

// 3. Click every visible button on the page
await interact('Click all buttons', async () => {
  const buttons = await page.$$('button, [role="button"], a[href]');
  for (const btn of buttons.slice(0, 10)) {
    try { await btn.click(); } catch {}
    await new Promise(r => setTimeout(r, 200));
  }
}, 'No crashes, no unexpected navigation');

// 4. Tab through page and hit Enter
await interact('Tab-Enter sweep', async () => {
  for (let i = 0; i < 15; i++) {
    await page.keyboard.press('Tab');
  }
  await page.keyboard.press('Enter');
}, 'No unexpected action triggered by keyboard');
```

### Backwards Bob — Ready-to-Paste Interactions

```javascript
// 1. Navigate to a deep route directly
await interact('Direct deep navigation', async () => {
  const links = await page.$$eval('a[href]', els => els.map(e => e.href));
  if (links.length > 0) await page.goto(links[links.length - 1], {waitUntil: 'networkidle2'});
}, 'Page renders without errors or missing data');

// 2. Hit back 3 times
await interact('Triple back navigation', async () => {
  await page.goBack(); await page.goBack(); await page.goBack();
}, 'App handles back navigation gracefully');

// 3. Refresh mid-action
await interact('Refresh during load', async () => {
  await page.reload({waitUntil: 'networkidle2'});
}, 'Page reloads cleanly without state corruption');

// 4. Manipulate URL to invalid ID
await interact('Invalid URL parameter', async () => {
  const url = new URL(page.url());
  await page.goto(url.origin + '/items/999999/edit', {waitUntil: 'networkidle2'});
}, '404 or graceful error, not crash');
```

### Copy-Paste Carol — Ready-to-Paste Interactions

```javascript
// 1. XSS payload in every input
await interact('XSS payload injection', async () => {
  const inputs = await page.$$('input[type="text"], input:not([type]), textarea');
  for (const input of inputs) {
    await input.click({clickCount: 3});
    await input.type('<script>alert("xss")</script>');
  }
}, 'Input sanitized, no script execution');

// 2. 10K character paste
await interact('10K character overflow', async () => {
  const input = await page.$('input[type="text"], input:not([type]), textarea');
  if (input) { await input.click({clickCount: 3}); await input.type('A'.repeat(10000)); }
}, 'Input truncated or length-limited, no crash');

// 3. Emoji bomb
await interact('Emoji input', async () => {
  const input = await page.$('input[type="text"], input:not([type]), textarea');
  if (input) { await input.click({clickCount: 3}); await input.type('🎉🔥💀👻🤖💩🌈🦄🍕🎸🚀💎'); }
}, 'Emoji displayed correctly, no encoding errors');

// 4. SQL injection in search
await interact('SQL injection in search', async () => {
  const search = await page.$('input[type="search"], input[name*="search"], input[placeholder*="earch"]');
  if (search) { await search.click({clickCount: 3}); await search.type("'; DROP TABLE users; --"); }
}, 'Input escaped, no database error exposed');
```

### Rage Clicker Rick — Ready-to-Paste Interactions

```javascript
// 1. Rage-click a button 10 times during loading
await interact('Rage click during load', async () => {
  const btn = await page.evaluateHandle(() =>
    [...document.querySelectorAll('button')].find(b => /submit|save|send|add|create/i.test(b.textContent))
  );
  const el = btn?.asElement?.() || btn;
  if (!el) { FINDINGS.push({id: interactionCount, description: 'No clickable button found', severity: 'P2-ANNOYING', expected: 'Action button present', actual: 'Not found'}); return; }
  for (let i = 0; i < 10; i++) { try { await el.click(); } catch {} }
}, 'Button disabled after first click, no duplicate actions');

// 2. Toggle a switch/checkbox on-off rapidly
await interact('Rapid toggle', async () => {
  const toggle = await page.$('input[type="checkbox"], [role="switch"]');
  if (!toggle) { FINDINGS.push({id: interactionCount, description: 'No toggle element found', severity: 'P3-COSMETIC', expected: 'Toggle present', actual: 'Not found'}); return; }
  for (let i = 0; i < 5; i++) { await toggle.click(); await new Promise(r => setTimeout(r, 100)); }
}, 'Final state is correct, no intermediate side-effects');

// 3. Resize viewport mid-action
await interact('Resize during interaction', async () => {
  await page.setViewport({width: 375, height: 667});
  await new Promise(r => setTimeout(r, 500));
  await page.setViewport({width: 1280, height: 800});
}, 'Layout adapts cleanly, no overflow or stuck elements');

// 4. Open and close modal rapidly
await interact('Rapid modal toggle', async () => {
  const trigger = await page.evaluateHandle(() =>
    [...document.querySelectorAll('button')].find(b => /open|new|add|create|modal/i.test(b.textContent))
  );
  const el = trigger?.asElement?.() || trigger;
  if (!el) return;
  for (let i = 0; i < 5; i++) {
    try { await el.click(); } catch {}
    await new Promise(r => setTimeout(r, 200));
    const close = await page.$('[aria-label="Close"], .close, [data-dismiss], dialog button');
    if (close) try { await close.click(); } catch {}
    await new Promise(r => setTimeout(r, 200));
  }
}, 'No z-index stacking, no event listener leaks, no orphan overlays');
```

### Zero-Knowledge Zara — Ready-to-Paste Interactions

```javascript
// 1. First impression — check for onboarding cues
await interact('First impression audit', async () => {
  const bodyText = await page.evaluate(() => document.body.innerText);
  const hasGuidance = /get started|welcome|click here|begin|tutorial|step 1/i.test(bodyText);
  if (!hasGuidance) {
    FINDINGS.push({id: interactionCount, description: 'No onboarding or guidance visible on landing',
      severity: 'P2-ANNOYING', expected: 'Clear first-action guidance', actual: 'No guidance text found'});
  }
}, 'Clear indication of what to do first');

// 2. Check all icon-only buttons for labels
await interact('Icon button accessibility', async () => {
  const unlabeled = await page.evaluate(() => {
    const btns = document.querySelectorAll('button, [role="button"]');
    return [...btns].filter(b => !b.textContent.trim() && !b.getAttribute('aria-label') && !b.getAttribute('title')).length;
  });
  if (unlabeled > 0) {
    FINDINGS.push({id: interactionCount, description: unlabeled + ' icon-only button(s) without accessible labels',
      severity: 'P2-ANNOYING', expected: 'All buttons have text or aria-label', actual: unlabeled + ' unlabeled'});
  }
}, 'All buttons discoverable without guessing');

// 3. Trigger an error and check if message is actionable
await interact('Error message quality', async () => {
  const submit = await page.evaluateHandle(() =>
    [...document.querySelectorAll('button')].find(b => /submit|save/i.test(b.textContent))
  );
  const el = submit?.asElement?.() || submit;
  if (el) await el.click();
  await new Promise(r => setTimeout(r, 1000));
  const errorText = await page.evaluate(() => {
    const errs = document.querySelectorAll('[class*="error"], [role="alert"], .error, .validation, [aria-invalid="true"]');
    return [...errs].map(e => e.textContent.trim()).filter(Boolean).join(' | ');
  });
  if (errorText && !/how|please|must|should|try|enter|provide|required/i.test(errorText)) {
    FINDINGS.push({id: interactionCount, description: 'Error messages are not actionable',
      severity: 'P2-ANNOYING', expected: 'Error tells user HOW to fix it', actual: 'Error text: "' + errorText.slice(0, 100) + '"'});
  }
}, 'Error messages explain what went wrong AND how to fix it');

// 4. Count clickable elements — check for overwhelming UI
await interact('Cognitive load check', async () => {
  const count = await page.evaluate(() =>
    document.querySelectorAll('a[href], button, [role="button"], input, select, textarea').length
  );
  if (count > 30) {
    FINDINGS.push({id: interactionCount, description: 'UI has ' + count + ' interactive elements — potentially overwhelming',
      severity: 'P3-COSMETIC', expected: 'Focused UI with clear hierarchy', actual: count + ' interactive elements visible'});
  }
}, 'Main task is discoverable within 2 interactions');
```

---

## 1. Fumbles — The Button Masher

**Mindset**: "I don't read, I click. If it's clickable, I click it. If nothing happens, I click harder."

### Interaction Script (8-12 of these per session)

| # | Action | What to look for |
|---|--------|-----------------|
| 1 | Click submit/save/send without filling any fields | Validation messages? Form submits empty? |
| 2 | Click submit 5 times rapidly (within 1 second) | Duplicate submissions? Loading state? Button disabled? |
| 3 | Click every button visible on the page, left to right, top to bottom | Unexpected navigation? Modal stacking? State corruption? |
| 4 | Click a delete/remove/cancel button without reading the confirmation | Is there a confirmation? Can the action be undone? |
| 5 | Start filling a form, then click away to a different page | Is partial data saved? Lost? Does it warn about unsaved changes? |
| 6 | Click dropdown menus and immediately click elsewhere | Does the dropdown close? Does it leave an overlay? |
| 7 | Click on disabled-looking elements | Are they actually disabled? Do they silently fail? |
| 8 | Tab through the entire page and press Enter on whatever has focus | Which element gets accidentally activated? |
| 9 | Click the logo/header 3 times during a multi-step flow | Does it navigate home? Lose progress? |
| 10 | Click browser forward/back during a form submission | Does the submission complete? Duplicate? Error? |

### Evidence Capture

Evidence is captured automatically by the `interact()` wrapper in the test harness:
screenshot after every interaction + `CONSOLE_ERRORS` / `PAGE_ERRORS` arrays.
No manual evidence commands needed — the harness handles it.

---

## 2. Backwards Bob — The Reverse Navigator

**Mindset**: "Why would I start at step 1? Step 3 looks more interesting."

### Interaction Script

| # | Action | What to look for |
|---|--------|-----------------|
| 1 | Navigate directly to a deep route (URL manipulation) | 404? Broken state? Missing context/data? |
| 2 | Start a multi-step flow, go to step 3, then step 1 | Does the flow reset? Corrupt? Allow out-of-order? |
| 3 | Complete a flow, then hit browser Back 3 times | Can you resubmit? Duplicate data? Stale state? |
| 4 | Open 2 tabs of the same app, do different things | State sync? Conflicts? |
| 5 | Refresh the page mid-action (during loading spinner) | Data lost? Partial save? Double execution? |
| 6 | Use browser Back to return to a submitted form | Is the form cleared? Pre-filled? Can re-submit? |
| 7 | Modify URL parameters to invalid values | Error handling? Crashes? SQL injection via URL? |
| 8 | Navigate to a page that requires prior state (e.g., checkout without cart) | Guard rails? Redirect? Blank page? |
| 9 | Complete a delete action, then try to navigate to the deleted item | 404? Error? Stale cache? |
| 10 | Bookmark a page with session state, close browser, reopen bookmark | Session expired gracefully? Crash? |

### Key URL Manipulation Tests

```
# Original URL
https://app.example.com/items/123/edit

# Backwards Bob tries:
https://app.example.com/items/999999/edit     # Non-existent ID
https://app.example.com/items/-1/edit          # Negative ID
https://app.example.com/items/abc/edit         # Non-numeric ID
https://app.example.com/items//edit            # Empty ID
https://app.example.com/items/123/delete       # Guess a delete route
https://app.example.com/admin                  # Guess an admin route
```

---

## 3. Copy-Paste Carol — The Input Terrorist

**Mindset**: "I'm going to paste whatever's on my clipboard into every field I find."

### Interaction Script

| # | Action | What to look for |
|---|--------|-----------------|
| 1 | Paste the XSS payload into every text input | Is it sanitized? Rendered as HTML? |
| 2 | Paste the SQL injection string into search/filter fields | Error? Data leak? Handled gracefully? |
| 3 | Paste 10,000 characters into a single-line input | Truncation? Crash? Layout break? |
| 4 | Paste emoji (🎉🔥💀👻) into name/title fields | Encoding issues? Display correctly? DB error? |
| 5 | Paste HTML tags (`<h1>BIG</h1>`) into text areas | Rendered as HTML? Escaped? Stripped? |
| 6 | Enter negative numbers in quantity/amount fields | Accepted? Validated? Crashes math? |
| 7 | Enter 0 in quantity/amount fields | Division by zero? Zero-dollar transactions? |
| 8 | Enter numbers with many decimals (3.141592653589793) | Truncated? Rounded? Display overflow? |
| 9 | Paste a URL into a non-URL field | Rendered as link? Breaks layout? |
| 10 | Leave required fields empty, fill optional fields | Validation on required only? Or all-or-nothing? |

### Standard Payloads (use exactly these)

```
# XSS Payload
<script>alert('xss')</script>

# SQL Injection
'; DROP TABLE users; --

# Long String (generate 10K chars)
python3 -c "print('A' * 10000)"

# Unicode Chaos
Ṱ̈́̅̃ȟ̗̱̻̗i̧̙̟̖̻s̨̞̗ ̟̜̩̣i̛̫̜̣̫̣̞s̲̩̪ ̡̲̬̫z̠̝̫a̹̫̲͙l̴̶g̸o̸

# Emoji Bomb
🎉🔥💀👻🤖💩🌈🦄🍕🎸🚀💎🌊🎭🦊

# Whitespace Only
"     "

# Null Byte
\x00\x00\x00

# Very Long Email
aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa@example.com

# Number Edge Cases
-1, 0, 0.0001, 99999999, Infinity, NaN, 1e308
```

---

## 4. Rage Clicker Rick — The Impatient One

**Mindset**: "It's loading? Click again. Still loading? Click faster. CLICK CLICK CLICK."

### Interaction Script

| # | Action | What to look for |
|---|--------|-----------------|
| 1 | Click a button that triggers a loading state, then click it 10 more times | Multiple requests? UI corruption? |
| 2 | Toggle a switch/checkbox on-off-on-off 5 times in 2 seconds | Final state correct? Intermediate requests? |
| 3 | Type in a search field, delete, retype, delete, retype rapidly | Debounce working? Rate limiting? Stale results? |
| 4 | Resize browser window from full to mobile width during a modal | Modal responsive? Overflow? Stuck overlay? |
| 5 | Switch browser tabs during an API call, come back 30s later | Stale state? Timeout handled? Loading stuck? |
| 6 | Scroll rapidly up and down on a long list/table | Infinite scroll issues? Layout thrashing? Memory leak? |
| 7 | Click a navigation link while a previous page is still loading | Route interruption? Partial render? |
| 8 | Open and close a modal 5 times rapidly | Memory leak? Event listener stacking? Z-index issues? |
| 9 | Submit a form, then immediately navigate away | Submission complete? Lost? Phantom success toast? |
| 10 | Click "cancel" during a save operation | Does cancel work? Partial save? Data corruption? |

### Timing-Sensitive Tests

For race condition testing, time interactions carefully:
```
# Rapid-fire clicks (simulate with consecutive interactions)
Interaction 1: Click submit
Interaction 2: (immediately) Click submit again
Interaction 3: (immediately) Click submit again
→ Check: How many requests were made? How many records were created?
```

---

## 5. Zero-Knowledge Zara — The Complete Novice

**Mindset**: "What's a 'field'? Why is it red? I don't understand what this button does."

### Interaction Script

| # | Action | What to look for |
|---|--------|-----------------|
| 1 | Arrive at the app. Don't click anything. Read the page. | Is it obvious what to do first? Any onboarding? |
| 2 | Look for help text, tooltips, or instructions | Do they exist? Are they helpful? Or just "Enter value" on a field labeled "Value"? |
| 3 | Trigger an error message. Read it. Is it actionable? | Does it say WHAT went wrong and HOW to fix it? Or just "Error"? |
| 4 | Try to accomplish the main task with zero prior knowledge | How many wrong turns before success? Count them. |
| 5 | See a dropdown with no default selected. Click submit. | Does it validate? Silently use the first option? Error? |
| 6 | See an icon-only button. Try to guess what it does. | Is there a label? Tooltip? ARIA label? |
| 7 | Encounter a loading state. Wait. How long? | Is there a spinner? Progress indication? Timeout? |
| 8 | Get an error. Do the exact same thing again. | Same error? Different? Helpful the second time? |
| 9 | Try to find a feature that exists but isn't on the current page | Is navigation discoverable? Search available? |
| 10 | Complete the main flow successfully. Was it satisfying? | Confirmation message? Next steps? Or just... nothing? |

### Zara's Scoring Addendum

After Zara's session, answer these (included as supplemental findings):
- **Time to first action**: How many interactions before Zara did something productive? Target: ≤2
- **Error recovery rate**: Of errors encountered, how many had actionable messages? Target: ≥80%
- **Discoverability**: Could Zara find the main feature without guessing? Target: yes
- **Dead ends**: How many states had no obvious next action? Target: 0

---

## 6. Universal Payloads

These payloads should be used by ALL personas when interacting with inputs:

### Required Test Inputs Per Field Type

| Field Type | Test Values |
|-----------|------------|
| Text (short) | Empty, spaces only, XSS payload, 500 chars |
| Text (long) | Empty, 10K chars, markdown, HTML tags |
| Email | Empty, no @, no domain, valid, 200-char email |
| Number | Empty, 0, -1, 99999999, 3.14159, NaN, "abc" |
| Phone | Empty, letters, 3 digits, 20 digits, symbols |
| Date | Empty, 1900-01-01, 2099-12-31, Feb 30, "yesterday" |
| URL | Empty, no protocol, spaces in URL, javascript:alert(1) |
| File upload | No file, wrong type, 0KB file, oversized file |
| Dropdown | Don't select (if optional), first, last |
| Checkbox | Unchecked when required, check-uncheck-check |

### Console Monitoring

Console monitoring is handled automatically by the Puppeteer `page.on('console')`
and `page.on('pageerror')` listeners registered in the test harness template.
No separate monitoring commands needed. The JSON output from each test script
includes all captured errors with timestamps.
