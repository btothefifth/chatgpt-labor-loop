# Provider capability seed and evidence

Research checked 2026-09-21 against public official pages. No authenticated
account was inspected. This is a documentation seed, not an operational
capability snapshot. Never treat it as live quota or permission to automate.

| Service | Documented seed | Runtime facts still required |
|---|---|---|
| ChatGPT | File upload availability varies by plan/model/workspace; generated files can be downloaded. Seed Free and paid profiles as potential capabilities, not paid-only flags | Current account/workspace, model/mode, upload/analysis controls, actual output format, download and limit state |
| Gemini | Common file/code inputs and downloadable document formats are documented; consumer profiles include no AI plan, AI Plus, AI Pro, AI Ultra | Actual account/region/rollout, model/thinking, input restrictions and output format; document export does not prove arbitrary ZIP creation |
| Claude | Uploads and generated downloadable files are documented; file creation covers Free, Pro, Max, Team and Enterprise | Enabled code/file-creation feature, workspace settings, model/effort, input/output types, download and remaining allowance |

Sources supporting capability claims:

* ChatGPT [uploads](https://help.openai.com/en/articles/8555545-file-uploads-faq),
  [analysis](https://help.openai.com/en/articles/8437071-data-analysis-with-chatgpt),
  [Library](https://help.openai.com/en/articles/20001052).
* Gemini [uploads](https://support.google.com/gemini/answer/14903178?hl=en),
  [file generation](https://blog.google/innovation-and-ai/products/gemini-app/generate-files-in-gemini/),
  [plans and limits](https://support.google.com/gemini/answer/16275805?hl=en).
* Claude [uploads](https://support.claude.com/en/articles/8241126-upload-files-to-claude),
  [file creation](https://support.claude.com/en/articles/12111783-create-and-edit-files-with-claude),
  [usage versus context](https://support.claude.com/en/articles/11647753-how-do-usage-and-length-limits-work).

Exact quotas are intentionally not seeded: they vary with plan, model, mode,
account policy and service changes. Failed upload attempts may consume capacity;
repeated probing is not free. Claude's file-creation documentation describes
network defaults inconsistently across sections, so network is settings-dependent
and unknown until inspected. Never require worker network access for the packet.

## Authorized transport is a separate capability

The public [OpenAI terms](https://openai.com/policies/row-terms-of-use/) restrict
automatic/programmatic output extraction. The [Anthropic consumer terms](https://www.anthropic.com/legal/consumer-terms)
restrict nonhuman access except specified permission/API routes. The
[Google terms](https://policies.google.com/terms?hl=en) restrict automated access
contrary to machine-readable instructions. Applicable account agreements and
supported integrations can differ; a subscription tier alone settles none of this.

Design consequence: ship manual handoff for every service; qualify automated
transport only with a recorded applicable supported route/permission. Do not
silently substitute an API when subscription chat is unavailable. This project
does not claim that a provider's ability to create a file authorizes arbitrary
UI automation or backend retrieval. Keep a source/version/checked date on each
adapter's permission assessment and refresh when the route changes.
