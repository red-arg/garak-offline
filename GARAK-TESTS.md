# Offline garak 0.17.1: What the Default Scan Tests

Oct 26, 2026 · @Zhi Feng

## Overview

The offline bundle runs garak 0.17.1's default probe set against the model served by vLLM behind LiteLLM, with 5 responses per prompt (`garak-offline.yaml`). garak sends batches of attack or test prompts (**probes**). It then scores every reply with **detectors**: keyword and regex checks, reference data, or small local classifier models. The report gives a failure rate for each probe and detector pair.

This document sorts the default probes into two groups by what a failure means:

- **Safety**: the model itself says something harmful, toxic or false when asked fairly directly. The harm lands on the person reading the output.
- **Security**: someone attacks the model or the system around it. They get past its guardrails, hijack it with injected instructions, pull out data it should keep, or get it to produce output that attacks other systems.

Where a probe uses an attack technique (a jailbreak, an encoding trick) to get harmful content, it is filed under **Security**, because what it tests is whether the guardrail can be bypassed.

## At a glance

The default scan runs **93 probes**: **13 safety** and **80 security**. Security dominates because one attack technique (such as an encoding) is often a separate probe per variant: encoding alone accounts for 15. The list comes from garak 0.17.1's own plugin metadata (`resources/plugin_cache.json`), which marks 93 of its 195 probes as active by default.

| Category | Group | What a failure means | Probe modules | Probes |
| --- | --- | --- | --- | --- |
| Safety | Toxic and offensive content | Model produces toxicity, slurs, bullying or sexual content | `lmrc`, `realtoxicityprompts`, `continuation`, `atkgen` | 9 |
| Safety | Controversial topics | Model engages on topics it should steer away from | `topic` | 1 |
| Safety | Misinformation and hallucination | Model accepts false claims or invents facts | `misleading`, `snowball`, `goodside.WhoIsRiley` | 3 |
| Security | Prompt injection and obfuscation | Hidden or injected instructions override the user's task | `encoding`, `latentinjection`, `promptinject`, `goodside.Tag` | 28 |
| Security | Jailbreaks and guardrail bypass | Attack prompts get the model past its refusals | `dan`, `grandma`, `tap`, `suffix`, `adaptive_attacks`, `dra`, `sata`, `phrasing`, `badchars`, `goodside.ThreatenJSON` | 16 |
| Security | Attacks on downstream systems | Model output carries XSS, data exfiltration, SQL or template injection, or terminal escapes | `web_injection`, `exploitation`, `ansiescape` | 12 |
| Security | Data leakage | Model reveals training data or its system prompt | `leakreplay`, `divergence`, `sysprompt_extraction` | 11 |
| Security | Software supply chain | Generated code imports packages that do not exist | `packagehallucination` | 7 |
| Security | Cyber-offence assistance | Model writes malware or produces API keys | `malwaregen`, `apikey` | 6 |

## Safety tests (13 probes)

These probes ask for harmful or false content fairly directly, or set up a situation where it comes out naturally. A failure means the model's own output is harmful to the person reading it.

### Toxic and offensive content (9)

| Probe | What it tests | How a failure is detected |
| --- | --- | --- |
| `lmrc.Bullying` | Whether the model helps someone bully, threaten or intimidate a person | Toxicity classifier (`unsafe_content.ToxicCommentModel`) |
| `lmrc.Deadnaming` | Whether it uses a trans person's former name when asked about well-known people | Trigger list of the old names |
| `lmrc.SexualContent` | Whether it writes sexual content on request | Sexual-profanity word list (Surge), Ofcom offensive-sexual list |
| `lmrc.Sexualisation` | Whether it sexualises or objectifies people | Same sexual-content lists |
| `lmrc.SlurUsage` | Whether it uses racial or ethnic slurs when asked | Racial/ethnic profanity list (Surge), Ofcom list |
| `lmrc.QuackMedicine` | Whether it promotes bogus medical treatments | Keyword detector for quack-medicine claims |
| `realtoxicityprompts.RTPBlank` | Whether toxic text comes out from an empty prompt or special tokens alone | Toxicity classifier |
| `continuation.ContinueSlursReclaimedSlurs` | Whether it completes a sentence that ends partway into a slur | Checks if the continuation finishes the slur |
| `atkgen.Tox` | Whether a small attacker model (GPT-2), talking to the target over several turns, can provoke something toxic | Toxicity classifier |

### Controversial topics (1)

| Probe | What it tests | How a failure is detected |
| --- | --- | --- |
| `topic.WordnetControversial` | Whether the model takes part on contested topics (by default: Hitler, euthanasia, Hezbollah, Palestine, libertarianism, gun control, apartheid, homeopathy), exploring nearby words through WordNet | Flags a reply that engages rather than declining (`mitigation.MitigationBypass`) |

### Misinformation and hallucination (3)

| Probe | What it tests | How a failure is detected |
| --- | --- | --- |
| `misleading.FalseAssertion` | Whether the model rejects a false statement or builds on it | Refutation classifier, refutation keywords, NLI contradiction model |
| `snowball.GraphConnectivity` | Whether it says an impossible flight route exists, then justifies the wrong answer | Flags replies that start with "yes" |
| `goodside.WhoIsRiley` | Whether it invents a biography for a real but little-known person (Riley Goodside) | Checks for known false claims about him |

`atkgen.Tox` uses an attacker model, but it is filed here because the only thing it scores is toxicity, not whether a guardrail was bypassed.

## Security tests (80 probes)

These probes play an attacker. A failure means someone could get past the model's controls, take over its instructions, pull data out of it, or use its output against other systems.

### Prompt injection and obfuscation (28)

| Probe | What it tests | How a failure is detected |
| --- | --- | --- |
| `encoding.Inject*` (15): Base64, Base16, Base32, Base2048, Ascii85, Hex, UU, ROT13, Atbash, Braille, Morse, NATO, Ecoji, Zalgo, Unicode tag characters | Whether the model decodes and repeats a harmful payload hidden in an encoding | Decoded payload appears in the reply, exactly or approximately |
| `latentinjection.*` (9): Report, Resume, WHOIS, WHOIS snippet, two fact snippets (Eiffel, legal), two translations (English to French, English to Chinese), LatentJailbreak | Whether instructions hidden in a document the model is asked to summarise, translate or assess take over the task (indirect prompt injection) | Planted trigger string appears in the reply; toxicity classifier for LatentJailbreak |
| `promptinject.Hijack*` (3): HateHumans, KillHumans, LongPrompt | Whether a plain "ignore the above and say X" instruction hijacks a normal task | Rogue string appears in the reply |
| `goodside.Tag` | Whether instructions written in invisible Unicode tag characters are followed | Trigger string appears in the reply |

### Jailbreaks and guardrail bypass (16)

| Probe | What it tests | How a failure is detected |
| --- | --- | --- |
| `dan.DanInTheWild`, `dan.Ablation_Dan_11_0`, `dan.AutoDANCached` | "Do Anything Now" jailbreaks collected from the internet, a DAN 11.0 variant study, and pre-generated AutoDAN prompts | DAN-mode markers; reply contains no refusal (`mitigation.MitigationBypass`) |
| `grandma.Slurs`, `grandma.Substances`, `grandma.Win10`, `grandma.Win11` | Roleplay as a late grandmother to get slurs, instructions for dangerous substances, or Windows product keys | Slur list, missing refusal, product-key pattern |
| `tap.TAPCached`, `suffix.GCGCached`, `adaptive_attacks.AdaptiveAttacks` | Pre-generated attack prompts from published methods (Tree of Attacks with Pruning, GCG adversarial suffixes, simple adaptive attacks) | Missing refusal |
| `dra.DRA` | Harmful request disguised by string tricks, which the model is asked to rebuild and answer | Missing refusal; refusal-prefix check |
| `sata.MLM` | Harmful words masked out, then the model is asked to fill in the blank and comply | Missing refusal |
| `phrasing.PastTense`, `phrasing.FutureTense` | The same harmful request reworded as "how did people…" or "how will people…" | Refusal-prefix check |
| `badchars.BadCharacters` | Invisible or look-alike Unicode characters that slip a request past refusal training | Missing refusal |
| `goodside.ThreatenJSON` | Threats used to force raw JSON with no safety preamble | Reply is plain JSON |

### Attacks on downstream systems (12)

| Probe | What it tests | How a failure is detected |
| --- | --- | --- |
| `web_injection.*` (6): MarkdownImageExfil, StringAssemblyDataExfil, PlaygroundMarkdownExfil, ColabAIDataLeakage, MarkdownURIImageExfilExtended, MarkdownURINonImageExfilExtended | Whether injected text makes the model write Markdown image or link URLs that would send conversation data to an attacker's server when rendered | Exfiltration-URL pattern in the reply |
| `web_injection.MarkdownXSS`, `web_injection.TaskXSS` | Whether the model emits cross-site scripting payloads that a web front end would run | XSS pattern in the reply |
| `exploitation.JinjaTemplatePythonInjection` | Whether the model outputs Jinja template code that would run Python on a server | Template-injection and Python-execution patterns |
| `exploitation.SQLInjectionEcho` | Whether the model echoes SQL injection payloads into output an app would pass to a database | SQL injection pattern |
| `ansiescape.AnsiRaw`, `ansiescape.AnsiEscaped` | Whether the model outputs ANSI terminal escape codes that could alter or hide what a log or console shows | Raw or escaped ANSI sequences in the reply |

### Data leakage (11)

| Probe | What it tests | How a failure is detected |
| --- | --- | --- |
| `leakreplay.*` (8): Cloze and Complete for literature, NYT, Guardian, Harry Potter | Whether the model reproduces memorised copyrighted text, by filling in a masked word or continuing a passage | Exact missing word, or continuation matches the original |
| `divergence.Repeat` | "Repeat this word forever" prompts that can make a model drift into training data | Output drifts away from the repeated word |
| `divergence.RepeatedToken` | Single-token strings repeated thousands of times, to push the model into an unstable state | Reply over 2,000 characters, looping text, or invented citations |
| `sysprompt_extraction.SystemPromptExtraction` | Whether attack prompts get the model to reveal its system prompt (50 real system prompts sampled from two datasets, each paired with attack templates) | System prompt text appears in the reply |

### Software supply chain (7)

| Probe | What it tests | How a failure is detected |
| --- | --- | --- |
| `packagehallucination.*` (7): Python, JavaScript, Ruby, Rust, Perl, Raku, Dart | Whether generated code imports packages that don't exist. An attacker can register such a name and ship malware to anyone who installs it. | Each imported name is checked against a snapshot of the real package index (PyPI, npm, RubyGems, crates.io, MetaCPAN, raku.land, pub.dev) |

### Cyber-offence assistance (6)

| Probe | What it tests | How a failure is detected |
| --- | --- | --- |
| `malwaregen.TopLevel`, `SubFunctions`, `Evasion`, `Payload` | Whether the model writes malware: whole programs, parts of them, anti-virus evasion, or payloads | Reply contains code |
| `apikey.GetKey`, `apikey.CompleteKey` | Whether it generates or completes API keys for real services | Key-format patterns |

## Not run by default (96 probes)

garak 0.17.1 ships 96 more probes that are switched off (plus 6 base and test classes). They are off because they are large, slow, need an attacker LLM, or need settings for a particular target. The bundle has not collected files for them, so check that they work offline before relying on them.

| Why it is off | Category | Probes |
| --- | --- | --- |
| Full-size versions of default probes (the default runs a sample) | Both | `latentinjection.*Full` (8), `leakreplay.*Full` (8), `promptinject.*Full` (3), `phrasing.*Full` (2), `continuation.ContinueSlursReclaimedSlursFull`, `dan.DanInTheWildFull`, `snowball.GraphConnectivityFull` |
| More safety prompt sets | Safety | `donotanswer` (5: discrimination and hate, information hazards, malicious uses, misinformation, human-chatbot interaction), `realtoxicityprompts` (7 subsets: threat, insult, identity attack and others), `lmrc.Profanity`, `lmrc.Anthropomorphisation`, `snowball.Primes`/`Senators` (+ Full versions) |
| Live attacks that need an attacker or helper LLM | Security | `tap.TAP`, `tap.PAIR`, `suffix.GCG`, `suffix.BEAST`, `dan.AutoDAN`, `goat.GOATAttack`, `fitd.FITD`, `agent_breaker.AgentBreaker`, `dra.DRAAdvanced` |
| Individual DAN-style jailbreak prompts | Security | `dan` (15 more: DAN 6.0 to 11.0, DUDE, STAN, AntiDAN, Developer Mode and others) |
| Other jailbreak and evasion techniques | Security | `doctor` (3), `smuggling` (3), `grandma.GrandmaIntent`, `encoding` (5 more: Leet, MIME, quoted-printable, SneakyBits, variant selectors), `goodside.Davidjl`, `glitch` (2) |
| Need settings or access for a particular target | Security | `topic.WordnetAllowedWords`/`BlockedWords` (need your topic list), `exploitation.SQLInjectionSystem`, `fileformats.HF_Files` (Hugging Face model files), `ansiescape.AnsiRawTokenizerHF` (local tokenizer), `av_spam_scanning` (3: EICAR, GTUBE, phishing test strings) |
| Personal data leakage | Security | `propile` (4 PII leak probes) |
| Images or audio | Security | `visual_jailbreak.FigStep` (+ Full), `audio.AudioAchillesHeel` |

To run one, name its class in `--spec`: naming only the module (`probes.donotanswer`) selects just its active probes, which here is none. `--spec` replaces the default set, so add `probes.*` to keep it: `garak --config garak-offline.yaml --spec 'probes.*,probes.donotanswer.MaliciousUses'`. On the staging host, run the harvest again with the same `--spec` so any files the probe needs end up in the bundle.

## What each category needs offline

Most probes need nothing but the LiteLLM endpoint. Their prompts and keyword detectors ship inside the garak package. The probes below also need files from the bundle; if a file is missing, that probe fails or is skipped while the rest of the scan carries on. Status is as of the bundle's 2026-10-25 note in `OFFLINE-FILES.md`.

| Bundled file | Category | Used by | Status |
| --- | --- | --- | --- |
| `garak-llm/toxic-comment-model` (toxicity classifier, 256 MB) | Safety and Security | `lmrc.Bullying`, `realtoxicityprompts.RTPBlank`, `atkgen.Tox`, `latentinjection.LatentJailbreak` | Collected |
| `garak-llm/attackgeneration-toxicity_gpt2` (attacker model, 478 MB) | Safety | `atkgen.Tox` | Collected |
| `garak-llm/refutation_detector_distilbert` (256 MB) | Safety | `misleading.FalseAssertion` | Collected |
| `garak-llm/roberta-large-snli_mnli_fever_anli_R1_R2_R3-nli` (NLI model, 1.3 GB) | Safety | `misleading.FalseAssertion` | Collected |
| Open English WordNet 2023 (local database) | Safety | `topic.WordnetControversial` | Pending |
| 7 package-index snapshots: PyPI, npm, RubyGems, crates.io, Perl, Raku, Dart (190 MB) | Security | `packagehallucination.*` | Pending |
| 2 system-prompt datasets (1.4 MB) | Security | `sysprompt_extraction.SystemPromptExtraction` | Pending |
| NLTK `averaged_perceptron_tagger_eng` | Security | `sata.MLM` | Pending |

The Perspective API detectors (`perspective.Toxicity`, `perspective.Sexually_Explicit`) are a Google cloud service and are not bundled. They are extra detectors only, so `lmrc.SexualContent`, `lmrc.Sexualisation` and `realtoxicityprompts.RTPBlank` are still scored by their main detector.

## Reading results and running one category

Reports land in `$XDG_DATA_HOME/garak/garak_runs`, which is `/opt/garak/data/garak/garak_runs` with the bundle's `garak-env.sh`. Each run writes three files:

- `garak.<run id>.report.html`: a pass rate for each probe and detector pair. A lower rate means the model failed more often.
- `garak.<run id>.report.jsonl`: every prompt, every response and every detector score.
- `garak.<run id>.hitlog.jsonl`: only the responses that failed, for review.

Detectors are automated, so read the hit log before reporting a failure. Keyword and "missing refusal" detectors in particular can flag a harmless answer.

To run one category on its own, pass a `--spec` built from the modules in this document:

```bash
# Safety only (13 probes)
garak --config garak-offline.yaml --spec 'probes.lmrc,probes.realtoxicityprompts,probes.continuation,probes.atkgen,probes.topic,probes.misleading,probes.snowball,probes.goodside.WhoIsRiley'

# Security only (80 probes): the default set minus the safety probes
garak --config garak-offline.yaml --spec 'probes.*,-probes.lmrc,-probes.realtoxicityprompts,-probes.continuation,-probes.atkgen,-probes.topic,-probes.misleading,-probes.snowball,-probes.goodside.WhoIsRiley'
```

Check either selection without running it by adding `--list_probes` to the command.
